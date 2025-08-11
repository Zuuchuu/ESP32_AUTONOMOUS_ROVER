"""
Mission visualization utilities for map display and progress tracking.

Provides JavaScript generation for map overlays, path visualization,
and real-time mission progress indicators in the web map interface.
"""

from typing import List, Tuple, Dict, Any, Optional
import json
import logging


class MissionVisualizer:
    """Generates map visualization for mission planning and tracking."""
    
    def __init__(self):
        self.logger = logging.getLogger('MissionVisualizer')
        
        # Visualization settings
        self.path_colors = {
            'planned': '#2196F3',      # Blue for planned path
            'active': '#4CAF50',       # Green for active segment
            'completed': '#9E9E9E',    # Gray for completed segments
            'deviation': '#FF5722'     # Red for deviation indicators
        }
        
        self.path_styles = {
            'planned': {'weight': 3, 'opacity': 0.8, 'dashArray': None},
            'active': {'weight': 4, 'opacity': 1.0, 'dashArray': None},
            'completed': {'weight': 2, 'opacity': 0.5, 'dashArray': '5, 5'},
            'deviation': {'weight': 2, 'opacity': 0.7, 'dashArray': '3, 3'}
        }
    
    def generate_planned_path_js(self, path_points: List[Tuple[float, float]], mission_id: str = "mission") -> str:
        """
        Generate JavaScript code to display planned path on map.
        
        Args:
            path_points: List of path coordinates
            mission_id: Unique identifier for this mission path
            
        Returns:
            JavaScript code for map visualization
        """
        if not path_points:
            return ""
        
        # Convert path points to JavaScript array
        js_points = json.dumps([[lat, lng] for lat, lng in path_points])
        
        color = self.path_colors['planned']
        style = self.path_styles['planned']
        
        js_code = f"""
        // Clear existing mission path
        if (window.{mission_id}_path) {{
            map.removeLayer(window.{mission_id}_path);
        }}
        
        // Create planned path polyline
        var pathPoints = {js_points};
        window.{mission_id}_path = L.polyline(pathPoints, {{
            color: '{color}',
            weight: {style['weight']},
            opacity: {style['opacity']}
        }}).addTo(map);
        
        // Add path markers at key points
        {self._generate_path_markers_js(path_points, mission_id)}
        
        // Fit map to show entire path using helper
        if (pathPoints.length > 0) {{
            if (typeof fitMissionPath === 'function') {{
                fitMissionPath(pathPoints);
            }} else {{
                map.fitBounds(window.{mission_id}_path.getBounds().pad(0.1));
            }}
        }}
        
        console.log('Mission path displayed: {len(path_points)} points');
        """
        
        return js_code
    
    def generate_mission_progress_js(self, 
                                   current_position: Tuple[float, float],
                                   current_segment_idx: int,
                                   path_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
                                   mission_id: str = "mission") -> str:
        """
        Generate JavaScript code to update mission progress visualization.
        
        Args:
            current_position: Current rover position
            current_segment_idx: Index of current path segment
            path_segments: List of path segments as (start, end) tuples
            mission_id: Mission identifier
            
        Returns:
            JavaScript code for progress visualization
        """
        lat, lng = current_position
        
        js_code = f"""
        // Update rover position
        setRoverPosition({lat}, {lng});
        
        // Update path segment highlighting
        {self._generate_segment_highlighting_js(current_segment_idx, path_segments, mission_id)}
        
        console.log('Mission progress updated: segment {current_segment_idx + 1}/{len(path_segments)}');
        """
        
        return js_code
    
    def generate_cross_track_error_js(self, 
                                    current_position: Tuple[float, float],
                                    path_start: Tuple[float, float],
                                    path_end: Tuple[float, float],
                                    error_distance: float) -> str:
        """
        Generate JavaScript code to visualize cross-track error.
        
        Args:
            current_position: Current rover position
            path_start: Current path segment start
            path_end: Current path segment end
            error_distance: Cross-track error in meters
            
        Returns:
            JavaScript code for error visualization
        """
        if abs(error_distance) < 1.0:  # Don't show small errors
            return self._clear_deviation_indicators_js()
        
        # Calculate perpendicular line from rover to path
        perpendicular_point = self._calculate_perpendicular_point(
            current_position, path_start, path_end
        )
        
        color = self.path_colors['deviation']
        
        js_code = f"""
        // Clear existing deviation indicators
        {self._clear_deviation_indicators_js()}
        
        // Draw cross-track error line
        var currentPos = [{current_position[0]}, {current_position[1]}];
        var pathPoint = [{perpendicular_point[0]}, {perpendicular_point[1]}];
        
        window.deviation_line = L.polyline([currentPos, pathPoint], {{
            color: '{color}',
            weight: 2,
            opacity: 0.8,
            dashArray: '3, 3'
        }}).addTo(map);
        
        // Add error distance popup
        var errorText = 'Cross-track error: {abs(error_distance):.1f}m';
        if ({error_distance} > 0) {{
            errorText += ' (right of path)';
        }} else {{
            errorText += ' (left of path)';
        }}
        
        window.deviation_popup = L.popup()
            .setLatLng([{(current_position[0] + perpendicular_point[0]) / 2}, 
                       {(current_position[1] + perpendicular_point[1]) / 2}])
            .setContent('<div style="color: {color}; font-weight: bold;">' + errorText + '</div>')
            .openOn(map);
        
        console.log('Cross-track error displayed: {error_distance:.1f}m');
        """
        
        return js_code
    
    def generate_rover_trail_js(self, position_history: List[Tuple[float, float]], max_points: int = 50) -> str:
        """
        Generate JavaScript code to display rover position trail.
        
        Args:
            position_history: List of historical rover positions
            max_points: Maximum number of trail points to display
            
        Returns:
            JavaScript code for trail visualization
        """
        if len(position_history) < 2:
            return ""
        
        # Limit trail points for performance
        trail_points = position_history[-max_points:] if len(position_history) > max_points else position_history
        
        js_points = json.dumps([[lat, lng] for lat, lng in trail_points])
        
        js_code = f"""
        // Clear existing rover trail
        if (window.rover_trail) {{
            map.removeLayer(window.rover_trail);
        }}
        
        // Create rover trail with fading effect
        var trailPoints = {js_points};
        window.rover_trail = L.polyline(trailPoints, {{
            color: '#FF9800',
            weight: 2,
            opacity: 0.6,
            dashArray: '2, 4'
        }}).addTo(map);
        
        console.log('Rover trail updated: {len(trail_points)} points');
        """
        
        return js_code
    
    def generate_mission_statistics_js(self, mission_stats: Dict[str, Any]) -> str:
        """
        Generate JavaScript code to update mission statistics overlay.
        
        Args:
            mission_stats: Dictionary of mission statistics
            
        Returns:
            JavaScript code for statistics display
        """
        stats_html = self._format_mission_stats_html(mission_stats)
        
        js_code = f"""
        // Update or create mission statistics overlay
        if (!window.mission_stats_control) {{
            window.mission_stats_control = L.control({{ position: 'topright' }});
            window.mission_stats_control.onAdd = function (map) {{
                var div = L.DomUtil.create('div', 'mission-stats-panel');
                div.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                div.style.padding = '10px';
                div.style.borderRadius = '5px';
                div.style.boxShadow = '0 2px 5px rgba(0,0,0,0.3)';
                div.style.fontSize = '12px';
                div.style.minWidth = '200px';
                return div;
            }};
            window.mission_stats_control.addTo(map);
        }}
        
        // Update statistics content
        var statsPanel = document.querySelector('.mission-stats-panel');
        if (statsPanel) {{
            statsPanel.innerHTML = `{stats_html}`;
        }}
        """
        
        return js_code
    
    def _generate_path_markers_js(self, path_points: List[Tuple[float, float]], mission_id: str) -> str:
        """Generate JavaScript for path markers at key points."""
        if not path_points:
            return ""
        
        # Add markers at start and end points
        start_point = path_points[0]
        end_point = path_points[-1]
        
        js_code = f"""
        // Add start marker
        if (window.{mission_id}_start_marker) {{
            map.removeLayer(window.{mission_id}_start_marker);
        }}
        window.{mission_id}_start_marker = L.marker([{start_point[0]}, {start_point[1]}], {{
            icon: L.icon({{
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41]
            }})
        }}).addTo(map).bindPopup('<strong>Mission Start</strong>');
        
        // Add end marker  
        if (window.{mission_id}_end_marker) {{
            map.removeLayer(window.{mission_id}_end_marker);
        }}
        window.{mission_id}_end_marker = L.marker([{end_point[0]}, {end_point[1]}], {{
            icon: L.icon({{
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41]
            }})
        }}).addTo(map).bindPopup('<strong>Mission End</strong>');
        """
        
        return js_code
    
    def _generate_segment_highlighting_js(self, 
                                        current_segment_idx: int,
                                        path_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
                                        mission_id: str) -> str:
        """Generate JavaScript for highlighting current path segment."""
        if not path_segments or current_segment_idx >= len(path_segments):
            return ""
        
        # Clear existing segment highlights
        js_code = f"""
        // Clear existing segment highlights
        if (window.{mission_id}_segments) {{
            window.{mission_id}_segments.forEach(function(segment) {{
                map.removeLayer(segment);
            }});
        }}
        window.{mission_id}_segments = [];
        """
        
        # Add segment highlighting
        for i, (start, end) in enumerate(path_segments):
            if i < current_segment_idx:
                # Completed segment
                color = self.path_colors['completed']
                style = self.path_styles['completed']
            elif i == current_segment_idx:
                # Active segment
                color = self.path_colors['active']
                style = self.path_styles['active']
            else:
                # Future segment
                color = self.path_colors['planned']
                style = self.path_styles['planned']
            
            dash_array = f"dashArray: '{style['dashArray']}'" if style['dashArray'] else "dashArray: null"
            
            js_code += f"""
            var segment{i} = L.polyline([[{start[0]}, {start[1]}], [{end[0]}, {end[1]}]], {{
                color: '{color}',
                weight: {style['weight']},
                opacity: {style['opacity']},
                {dash_array}
            }}).addTo(map);
            window.{mission_id}_segments.push(segment{i});
            """
        
        return js_code
    
    def _clear_deviation_indicators_js(self) -> str:
        """Generate JavaScript to clear deviation indicators."""
        return """
        // Clear deviation indicators
        if (window.deviation_line) {
            map.removeLayer(window.deviation_line);
            window.deviation_line = null;
        }
        if (window.deviation_popup) {
            map.closePopup(window.deviation_popup);
            window.deviation_popup = null;
        }
        """
    
    def _calculate_perpendicular_point(self, 
                                     rover_pos: Tuple[float, float],
                                     path_start: Tuple[float, float], 
                                     path_end: Tuple[float, float]) -> Tuple[float, float]:
        """Calculate perpendicular point on path segment from rover position."""
        # Simplified calculation - find closest point on line segment
        # This is an approximation for visualization purposes
        
        # Calculate vectors
        px, py = rover_pos[0] - path_start[0], rover_pos[1] - path_start[1]
        dx, dy = path_end[0] - path_start[0], path_end[1] - path_start[1]
        
        # Calculate projection parameter
        if dx == 0 and dy == 0:
            return path_start
        
        t = max(0, min(1, (px * dx + py * dy) / (dx * dx + dy * dy)))
        
        # Calculate perpendicular point
        perp_lat = path_start[0] + t * dx
        perp_lng = path_start[1] + t * dy
        
        return (perp_lat, perp_lng)
    
    def _format_mission_stats_html(self, stats: Dict[str, Any]) -> str:
        """Format mission statistics as HTML."""
        html_parts = ["<h4 style='margin: 0 0 8px 0; color: #333;'>Mission Status</h4>"]
        
        # Format key statistics
        if 'completion_pct' in stats:
            html_parts.append(f"<div><strong>Progress:</strong> {stats['completion_pct']:.1f}%</div>")
        
        if 'current_waypoint' in stats:
            html_parts.append(f"<div><strong>Waypoint:</strong> {stats['current_waypoint']}</div>")
        
        if 'distance_to_target_m' in stats:
            html_parts.append(f"<div><strong>Distance to Target:</strong> {stats['distance_to_target_m']:.1f}m</div>")
        
        if 'current_speed_mps' in stats:
            html_parts.append(f"<div><strong>Speed:</strong> {stats['current_speed_mps']:.1f} m/s</div>")
        
        if 'cross_track_error_m' in stats:
            error = stats['cross_track_error_m']
            error_color = 'red' if abs(error) > 2.0 else 'orange' if abs(error) > 1.0 else 'green'
            html_parts.append(f"<div><strong>Path Error:</strong> <span style='color: {error_color}'>{error:.1f}m</span></div>")
        
        if 'eta_min' in stats and stats['eta_min'] > 0:
            html_parts.append(f"<div><strong>ETA:</strong> {stats['eta_min']:.1f} min</div>")
        
        return "\\n".join(html_parts)
    
    def clear_mission_visualization_js(self, mission_id: str = "mission") -> str:
        """Generate JavaScript to clear all mission visualization elements."""
        return f"""
        // Clear mission path
        if (window.{mission_id}_path) {{
            map.removeLayer(window.{mission_id}_path);
            window.{mission_id}_path = null;
        }}
        
        // Clear path markers
        if (window.{mission_id}_start_marker) {{
            map.removeLayer(window.{mission_id}_start_marker);
            window.{mission_id}_start_marker = null;
        }}
        if (window.{mission_id}_end_marker) {{
            map.removeLayer(window.{mission_id}_end_marker);
            window.{mission_id}_end_marker = null;
        }}
        
        // Clear segment highlights
        if (window.{mission_id}_segments) {{
            window.{mission_id}_segments.forEach(function(segment) {{
                map.removeLayer(segment);
            }});
            window.{mission_id}_segments = [];
        }}
        
        // Clear rover trail
        if (window.rover_trail) {{
            map.removeLayer(window.rover_trail);
            window.rover_trail = null;
        }}
        
        // Clear deviation indicators
        {self._clear_deviation_indicators_js()}
        
        // Clear statistics panel
        if (window.mission_stats_control) {{
            map.removeControl(window.mission_stats_control);
            window.mission_stats_control = null;
        }}
        
        console.log('Mission visualization cleared');
        """
