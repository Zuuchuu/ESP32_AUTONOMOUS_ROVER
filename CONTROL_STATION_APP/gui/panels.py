"""
Modular GUI panels for ESP32 Rover Control Station.

This module contains all the individual GUI components organized as
separate panels/widgets. Each panel is self-contained and handles
its own specific functionality.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QSlider, QFrame, QHeaderView, QMessageBox, QSizePolicy, QAbstractItemView
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QFont

from core.models import ConnectionState, NavigationState, TelemetryData, Waypoint, MissionPlan, MissionProgress
from mission.visualizer import MissionVisualizer


class ConnectionPanel(QGroupBox):
    """Panel for rover connection management."""
    
    # Signals
    connect_requested = pyqtSignal(str, int)  # ip, port
    disconnect_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__("Connection")
        self.is_connected = False
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the connection panel UI."""
        layout = QGridLayout()
        
        # IP address input
        layout.addWidget(QLabel("Rover IP:"), 0, 0)
        self.ip_input = QLineEdit("192.168.1.100")
        self.ip_input.setPlaceholderText("Enter rover IP address")
        self.ip_input.returnPressed.connect(self.toggle_connection)
        layout.addWidget(self.ip_input, 0, 1)
        
        # Port input (usually 80, but configurable)
        layout.addWidget(QLabel("Port:"), 1, 0)
        self.port_input = QLineEdit("80")
        self.port_input.setPlaceholderText("80")
        self.port_input.returnPressed.connect(self.toggle_connection)
        layout.addWidget(self.port_input, 1, 1)
        
        # Connect/Disconnect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("connectButton")
        self.connect_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_btn, 2, 0, 1, 2)
        
        # Connection status
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setObjectName("connectionStatus")
        layout.addWidget(self.status_label, 3, 0, 1, 2)
        
        self.setLayout(layout)
    
    def toggle_connection(self):
        """Toggle connection state."""
        if self.is_connected:
            self.disconnect_requested.emit()
        else:
            try:
                ip = self.ip_input.text().strip()
                port = int(self.port_input.text().strip())
                if ip:
                    self.connect_requested.emit(ip, port)
            except ValueError:
                QMessageBox.warning(self, "Invalid Port", "Please enter a valid port number.")
    
    def update_connection_state(self, state: ConnectionState, message: str = ""):
        """Update UI based on connection state."""
        if state == ConnectionState.CONNECTED:
            self.is_connected = True
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setObjectName("disconnectButton")
            self.status_label.setText("Status: Connected")
            self.ip_input.setEnabled(False)
            self.port_input.setEnabled(False)
        elif state == ConnectionState.CONNECTING:
            self.connect_btn.setText("Connecting...")
            self.connect_btn.setEnabled(False)
            self.status_label.setText("Status: Connecting...")
        else:  # DISCONNECTED or ERROR
            self.is_connected = False
            self.connect_btn.setText("Connect")
            self.connect_btn.setObjectName("connectButton")
            self.connect_btn.setEnabled(True)
            self.ip_input.setEnabled(True)
            self.port_input.setEnabled(True)
            
            if state == ConnectionState.ERROR and message:
                self.status_label.setText(f"Status: Error - {message}")
            else:
                self.status_label.setText("Status: Disconnected")
        
        # Force style update
        self.connect_btn.style().unpolish(self.connect_btn)
        self.connect_btn.style().polish(self.connect_btn)


class WaypointPanel(QGroupBox):
    """Panel for waypoint management."""
    
    # Signals
    waypoint_added_manual = pyqtSignal(float, float)  # lat, lng
    waypoints_cleared = pyqtSignal()
    remove_selected_requested = pyqtSignal(list)  # list of row indices
    
    def __init__(self):
        super().__init__("🎯 WAYPOINT MANAGEMENT")
        self.waypoints: List[Waypoint] = []
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold; 
                font-size: 11px; 
                color: #2c3e50; 
                background-color: #ecf0f1; 
                border: 2px solid #bdc3c7;
                border-radius: 6px; 
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #ecf0f1;
            }
        """)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up waypoint panel UI."""
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Waypoint table
        self.waypoint_table = QTableWidget(0, 3)
        self.waypoint_table.setHorizontalHeaderLabels(["#", "Latitude", "Longitude"])
        self.waypoint_table.setMaximumHeight(100)
        self.waypoint_table.setMinimumHeight(60)
        self.waypoint_table.setAlternatingRowColors(True)
        # Enable multi-row selection for targeted removal
        self.waypoint_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.waypoint_table.setSelectionMode(QAbstractItemView.MultiSelection)
        
        # Configure table headers
        header = self.waypoint_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        layout.addWidget(self.waypoint_table)
        
        # Manual waypoint input with inline instructions
        manual_frame = QFrame()
        manual_frame.setFrameStyle(QFrame.StyledPanel)
        manual_layout = QVBoxLayout()
        manual_layout.setSpacing(4)
        manual_layout.setContentsMargins(6, 6, 6, 6)
        
        # Inline instructions with input fields
        instructions_layout = QHBoxLayout()
        instructions_layout.setSpacing(4)
        
        instructions = QLabel("Click map or add manually:")
        instructions.setStyleSheet("color: #666; font-style: italic; font-size: 9px;")
        instructions_layout.addWidget(instructions)
        instructions_layout.addStretch()
        
        # Input row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(4)
        
        lat_label = QLabel("Lat:")
        lat_label.setStyleSheet("font-size: 10px; min-width: 25px;")
        input_layout.addWidget(lat_label)
        
        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText("37.7749")
        self.lat_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lat_input.setMinimumWidth(60)
        self.lat_input.setStyleSheet("font-size: 10px; padding: 3px;")
        self.lat_input.returnPressed.connect(self.add_manual_waypoint)
        input_layout.addWidget(self.lat_input)
        
        lng_label = QLabel("Lng:")
        lng_label.setStyleSheet("font-size: 10px; min-width: 30px;")
        input_layout.addWidget(lng_label)
        
        self.lng_input = QLineEdit()
        self.lng_input.setPlaceholderText("-122.4194")
        self.lng_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lng_input.setMinimumWidth(65)
        self.lng_input.setStyleSheet("font-size: 10px; padding: 3px;")
        self.lng_input.returnPressed.connect(self.add_manual_waypoint)
        input_layout.addWidget(self.lng_input)
        
        manual_layout.addLayout(instructions_layout)
        manual_layout.addLayout(input_layout)
        manual_frame.setLayout(manual_layout)
        layout.addWidget(manual_frame)
        
        # Control buttons - Compact with icons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        
        self.add_btn = QPushButton("➕ Add")
        self.add_btn.clicked.connect(self.add_manual_waypoint)
        self.add_btn.setMinimumHeight(22)
        self.add_btn.setMaximumHeight(28)
        btn_layout.addWidget(self.add_btn)
        
        self.clear_btn = QPushButton("🗑️ Remove Selected")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.clicked.connect(self.remove_selected_waypoints)
        self.clear_btn.setMinimumHeight(22)
        self.clear_btn.setMaximumHeight(28)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def add_manual_waypoint(self):
        """Add waypoint from manual input."""
        try:
            lat_text = self.lat_input.text().strip()
            lng_text = self.lng_input.text().strip()
            
            if not lat_text or not lng_text:
                QMessageBox.warning(self, "Input Error", 
                                  "Please enter both latitude and longitude.")
                return
            
            lat = float(lat_text)
            lng = float(lng_text)
            
            if not (-90 <= lat <= 90):
                QMessageBox.warning(self, "Invalid Latitude", 
                                  "Latitude must be between -90 and 90.")
                return
            
            if not (-180 <= lng <= 180):
                QMessageBox.warning(self, "Invalid Longitude", 
                                  "Longitude must be between -180 and 180.")
                return
            
            self.waypoint_added_manual.emit(lat, lng)
            self.lat_input.clear()
            self.lng_input.clear()
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", 
                              "Please enter valid numbers for coordinates.")
    
    def clear_waypoints(self):
        """Clear all waypoints."""
        self.waypoints_cleared.emit()

    def remove_selected_waypoints(self):
        """Emit indices of selected waypoints to remove only those."""
        selection_model = self.waypoint_table.selectionModel()
        if not selection_model:
            return
        selected_rows = sorted({idx.row() for idx in selection_model.selectedRows()})
        if not selected_rows:
            QMessageBox.information(self, "Remove Waypoints", "Please select waypoint rows to remove.")
            return
        self.remove_selected_requested.emit(selected_rows)
    

    
    def update_waypoints(self, waypoints: List[Waypoint]):
        """Update waypoint table display."""
        self.waypoints = waypoints
        # Clear selection and contents to avoid stale rows after deletions
        self.waypoint_table.clearSelection()
        self.waypoint_table.clearContents()
        self.waypoint_table.setRowCount(0)
        self.waypoint_table.setRowCount(len(waypoints))
        
        for i, waypoint in enumerate(waypoints):
            # Waypoint number (order)
            self.waypoint_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            # Latitude with 6 decimal places
            self.waypoint_table.setItem(i, 1, QTableWidgetItem(f"{waypoint.latitude:.6f}"))
            # Longitude with 6 decimal places  
            self.waypoint_table.setItem(i, 2, QTableWidgetItem(f"{waypoint.longitude:.6f}"))
        

    
    def set_connection_state(self, connected: bool):
        """Enable/disable controls based on connection state."""
        pass  # No longer needed for waypoint panel



class TelemetryPanel(QGroupBox):
    """Panel for displaying rover telemetry data."""
    
    def __init__(self):
        super().__init__("Rover Telemetry")
        self.current_telemetry: Optional[TelemetryData] = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up telemetry panel UI."""
        layout = QVBoxLayout()
        
        # Position info
        self.position_label = QLabel("Position: No data")
        self.position_label.setObjectName("statusLabel")
        layout.addWidget(self.position_label)
        
        # Heading info
        self.heading_label = QLabel("Heading: No data")
        self.heading_label.setObjectName("statusLabel")
        layout.addWidget(self.heading_label)
        
        # IMU data
        self.imu_label = QLabel("IMU: No data")
        self.imu_label.setObjectName("telemetryData")
        self.imu_label.setWordWrap(True)
        self.imu_label.setMinimumHeight(50)
        self.imu_label.setMaximumHeight(80)
        layout.addWidget(self.imu_label)
        
        # System info
        self.system_label = QLabel("System: No data")
        self.system_label.setObjectName("statusLabel")
        layout.addWidget(self.system_label)
        
        self.setLayout(layout)
    
    def update_telemetry(self, telemetry: TelemetryData):
        """Update telemetry display."""
        self.current_telemetry = telemetry
        
        if not telemetry.is_valid:
            self.position_label.setText("Position: Invalid data")
            self.heading_label.setText("Heading: Invalid data")
            self.imu_label.setText("IMU: Invalid data")
            self.system_label.setText("System: Invalid data")
            return
        
        # Position
        self.position_label.setText(f"Position: {telemetry.latitude:.6f}, {telemetry.longitude:.6f}")
        
        # Heading
        self.heading_label.setText(f"Heading: {telemetry.heading:.1f}°")
        
        # IMU data with formatted display
        imu_text = f"Accel: {telemetry.acceleration[0]:6.2f}, {telemetry.acceleration[1]:6.2f}, {telemetry.acceleration[2]:6.2f}\n"
        imu_text += f"Gyro:  {telemetry.gyroscope[0]:6.2f}, {telemetry.gyroscope[1]:6.2f}, {telemetry.gyroscope[2]:6.2f}\n"
        imu_text += f"Mag:   {telemetry.magnetometer[0]:6.2f}, {telemetry.magnetometer[1]:6.2f}, {telemetry.magnetometer[2]:6.2f}"
        self.imu_label.setText(imu_text)
        
        # System info
        self.system_label.setText(f"Temperature: {telemetry.temperature:.1f}°C | WiFi: {telemetry.wifi_strength} dBm")



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
