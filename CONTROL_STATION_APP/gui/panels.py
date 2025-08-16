"""
Modular GUI panels for ESP32 Rover Control Station.

This module contains all the individual GUI components organized as
separate panels/widgets. Each panel is self-contained and handles
its own specific functionality.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, pyqtSignal

from core.models import TelemetryData, Waypoint, MissionPlan, MissionProgress
from mission.visualizer import MissionVisualizer





class MapWidget(QFrame):
    """Widget containing the interactive map."""
    
    # Signals
    waypoint_added_from_map = pyqtSignal(dict)  # map data with lat/lng
    map_loaded = pyqtSignal(bool)  # success
    
    def __init__(self):
        super().__init__()
        self.setObjectName("mapContainer")
        self.map_ready = False
        self.mission_visualizer = MissionVisualizer()
        self.current_mission_id = "current_mission"
        # Internal waypoint monitoring state
        self._last_waypoint_count = 0
        self._suppress_waypoint_events = False
        self.setup_ui()
    
    def setup_ui(self):
        """Set up map widget UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Map view (edge-to-edge)
        self.map_view = QWebEngineView()
        map_path = os.path.join(os.path.dirname(__file__), "..", "assets", "map.html")
        map_url = QUrl.fromLocalFile(os.path.abspath(map_path))
        self.map_view.load(map_url)
        self.map_view.loadFinished.connect(self.on_map_loaded)
        self.map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.map_view)
        
        # Map controls are now handled by the HTML overlay (no duplicate buttons needed)
        
        self.setLayout(layout)
    
    def on_map_loaded(self, success: bool):
        """Handle map loading completion."""
        self.map_ready = success
        self.map_loaded.emit(success)
        if not success:
            QMessageBox.critical(self, "Map Error", 
                               "Failed to load map. Check internet connection.")
        else:
            # Set up JavaScript bridge for waypoint communication
            self._setup_map_communication()
    
    def add_waypoint(self, latitude: float, longitude: float):
        """Add waypoint to map programmatically."""
        if self.map_ready:
            self.map_view.page().runJavaScript(f"addWaypoint({latitude}, {longitude})")
    
    def clear_waypoints(self):
        """Clear all waypoints from map."""
        if self.map_ready:
            self.map_view.page().runJavaScript("clearWaypoints()")
            # Reset our waypoint counter
            self._last_waypoint_count = 0
    
    def update_rover_position(self, telemetry: TelemetryData):
        """Update rover position on map."""
        if self.map_ready and telemetry.has_valid_position():
            self.map_view.page().runJavaScript(
                f"setRoverPosition({telemetry.latitude}, {telemetry.longitude}, {telemetry.heading})"
            )
            # Rover position updated - HTML overlay buttons handle controls
    
        # Map control methods removed - controls are now handled by HTML overlay buttons
    
    def get_waypoints(self, callback):
        """Get waypoints from map (async)."""
        if self.map_ready:
            self.map_view.page().runJavaScript("getWaypoints()", callback)
    
    def set_map_view(self, latitude: float, longitude: float, zoom: int = 13):
        """Set map center and zoom."""
        if self.map_ready:
            self.map_view.page().runJavaScript(f"setMapView({latitude}, {longitude}, {zoom})")
    
    def _setup_map_communication(self):
        """Set up communication bridge between JavaScript and Python."""
        if not self.map_ready:
            return
        
        # Inject JavaScript bridge function to communicate waypoint clicks back to Python
        bridge_js = """
        // Override the addWaypointAtPosition function to notify Python
        var originalAddWaypointAtPosition = addWaypointAtPosition;
        addWaypointAtPosition = function(lat, lng) {
            var success = originalAddWaypointAtPosition(lat, lng);
            if (success) {
                // Notify Python about the new waypoint
                if (window.qt && window.qt.webChannelTransport) {
                    // Use QWebChannel if available
                    console.log('Waypoint added via QWebChannel:', lat, lng);
                } else {
                    // Fallback: use console logging that Python can monitor
                    console.log('WAYPOINT_ADDED:' + lat + ',' + lng);
                }
            }
            return success;
        };
        """
        
        self.map_view.page().runJavaScript(bridge_js)
        
        # Set up periodic monitoring of console messages for waypoint updates
        self._setup_waypoint_monitoring()
    
    def _setup_waypoint_monitoring(self):
        """Set up monitoring for waypoint changes from map."""
        # Create a timer to periodically check for waypoint updates
        from PyQt5.QtCore import QTimer
        
        self.waypoint_monitor_timer = QTimer()
        self.waypoint_monitor_timer.timeout.connect(self._check_map_waypoints)
        self.waypoint_monitor_timer.start(1000)  # Check every second
    
    def _check_map_waypoints(self):
        """Check for waypoint updates from the map."""
        if self.map_ready:
            # Get current waypoints from map and compare with last known state
            self.map_view.page().runJavaScript("getWaypoints()", self._handle_waypoint_update)
    
    def _handle_waypoint_update(self, waypoints):
        """Handle waypoint updates from JavaScript."""
        # Determine current count even if empty list
        current_count = len(waypoints) if waypoints else 0

        # During programmatic sync, just track count and do not emit add events
        if self._suppress_waypoint_events:
            self._last_waypoint_count = current_count
            return

        # Check if this is a new waypoint compared to our last known state
        if current_count > self._last_waypoint_count:
            # New waypoint added by user on the map - emit for the latest one
            if waypoints:
                latest_waypoint = waypoints[-1]
                self.waypoint_added_from_map.emit(latest_waypoint)
            self._last_waypoint_count = current_count
        elif current_count < self._last_waypoint_count:
            # Waypoints were removed/cleared on the map
            self._last_waypoint_count = current_count

    # Programmatic sync helpers
    def begin_programmatic_waypoint_update(self):
        """Suppress map waypoint monitoring events during programmatic updates."""
        self._suppress_waypoint_events = True

    def end_programmatic_waypoint_update(self):
        """Re-enable map waypoint monitoring events after programmatic updates."""
        self._suppress_waypoint_events = False

    def sync_waypoints(self, waypoints: List[Waypoint]):
        """Synchronize map markers to match given waypoints without emitting add events."""
        if not self.map_ready:
            return
        self.begin_programmatic_waypoint_update()
        try:
            self.clear_waypoints()
            for wp in waypoints:
                self.add_waypoint(wp.latitude, wp.longitude)
            # Ensure internal counter matches the state to avoid false-positive adds
            self._last_waypoint_count = len(waypoints)
        finally:
            self.end_programmatic_waypoint_update()
    
    # Mission visualization methods
    def display_mission_plan(self, mission_plan: MissionPlan):
        """Display mission plan on the map."""
        if not self.map_ready or not mission_plan.planned_path:
            return
        
        # Generate JavaScript for mission path visualization
        js_code = self.mission_visualizer.generate_planned_path_js(
            mission_plan.planned_path, 
            self.current_mission_id
        )
        
        # Execute JavaScript
        self.map_view.page().runJavaScript(js_code)
    
    def update_mission_progress(self, progress: MissionProgress, mission_plan: MissionPlan):
        """Update mission progress visualization."""
        if not self.map_ready or not mission_plan:
            return
        
        # Convert path segments to visualization format
        path_segments = [
            (segment.start_point, segment.end_point) 
            for segment in mission_plan.path_segments
        ]
        
        # Generate progress visualization JavaScript
        js_code = self.mission_visualizer.generate_mission_progress_js(
            progress.current_position,
            progress.current_waypoint_index,
            path_segments,
            self.current_mission_id
        )
        
        # Execute JavaScript
        self.map_view.page().runJavaScript(js_code)
    
    def show_cross_track_error(self, progress: MissionProgress, mission_plan: MissionPlan):
        """Display cross-track error visualization."""
        if not self.map_ready or not mission_plan.path_segments:
            return
        
        # Get current path segment
        segment_idx = min(progress.current_waypoint_index, len(mission_plan.path_segments) - 1)
        if segment_idx < 0:
            return
        
        current_segment = mission_plan.path_segments[segment_idx]
        
        # Generate cross-track error visualization
        js_code = self.mission_visualizer.generate_cross_track_error_js(
            progress.current_position,
            current_segment.start_point,
            current_segment.end_point,
            progress.cross_track_error
        )
        
        # Execute JavaScript
        self.map_view.page().runJavaScript(js_code)
    
    def show_rover_trail(self, position_history: List[Tuple[float, float]]):
        """Display rover position trail."""
        if not self.map_ready:
            return
        
        # Generate rover trail visualization
        js_code = self.mission_visualizer.generate_rover_trail_js(position_history)
        
        # Execute JavaScript
        self.map_view.page().runJavaScript(js_code)
    
    def update_mission_statistics(self, progress: MissionProgress):
        """Update mission statistics overlay."""
        if not self.map_ready:
            return
        
        # Generate statistics visualization
        stats = progress.get_progress_summary()
        js_code = self.mission_visualizer.generate_mission_statistics_js(stats)
        
        # Execute JavaScript
        self.map_view.page().runJavaScript(js_code)
    
    def clear_mission_visualization(self):
        """Clear all mission visualization elements."""
        if not self.map_ready:
            return
        
        # Generate clear visualization JavaScript
        js_code = self.mission_visualizer.clear_mission_visualization_js(self.current_mission_id)
        
        # Execute JavaScript
        self.map_view.page().runJavaScript(js_code)
    
    def center_on_mission(self, mission_plan: MissionPlan):
        """Center map to show entire mission."""
        if not self.map_ready or not mission_plan.planned_path:
            return
        
        # Calculate bounds of mission path
        lats = [point[0] for point in mission_plan.planned_path]
        lngs = [point[1] for point in mission_plan.planned_path]
        
        if lats and lngs:
            min_lat, max_lat = min(lats), max(lats)
            min_lng, max_lng = min(lngs), max(lngs)
            
            # Add padding
            lat_padding = (max_lat - min_lat) * 0.1
            lng_padding = (max_lng - min_lng) * 0.1
            
            # Fit bounds JavaScript
            js_code = f"""
            var bounds = [
                [{min_lat - lat_padding}, {min_lng - lng_padding}],
                [{max_lat + lat_padding}, {max_lng + lng_padding}]
            ];
            map.fitBounds(bounds);
            """
            
            self.map_view.page().runJavaScript(js_code)
