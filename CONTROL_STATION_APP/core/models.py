"""
Data models for ESP32 Rover Control Station.

This module defines all data structures, enums, and state management
classes used throughout the application. Models include validation
and are compatible with ESP32 rover communication protocol.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import time
from PyQt5.QtCore import QObject, pyqtSignal


class ConnectionState(Enum):
    """Connection state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class NavigationState(Enum):
    """Navigation state enumeration."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class Waypoint:
    """
    Waypoint data model compatible with ESP32 rover protocol.
    
    ESP32 expects: {"lat": float, "lon": float}
    """
    latitude: float
    longitude: float
    id: Optional[int] = None
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Validate waypoint coordinates."""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Invalid latitude: {self.latitude}. Must be between -90 and 90.")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Invalid longitude: {self.longitude}. Must be between -180 and 180.")
    
    def to_esp32_format(self) -> Dict[str, float]:
        """Convert to ESP32-compatible format."""
        return {
            "lat": self.latitude,
            "lon": self.longitude  # ESP32 uses "lon" not "lng"
        }
    
    @classmethod
    def from_map_format(cls, data: Dict[str, Any]) -> 'Waypoint':
        """Create waypoint from map JavaScript format."""
        lat = data.get("lat", 0.0)
        lng = data.get("lng", data.get("lon", 0.0))
        
        # Normalize longitude to valid range (-180 to 180)
        while lng > 180:
            lng -= 360
        while lng < -180:
            lng += 360
            
        return cls(latitude=lat, longitude=lng)


@dataclass
class TelemetryData:
    """
    Telemetry data model matching ESP32 rover output format.
    
    ESP32 sends: {
        "lat": float, "lon": float, "heading": float,
        "imu_data": {"accel": [x,y,z], "gyro": [x,y,z], "mag": [x,y,z]},
        "temperature": float, "wifi_strength": int
    }
    """
    latitude: float = 0.0
    longitude: float = 0.0
    heading: float = 0.0
    acceleration: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    gyroscope: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    magnetometer: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    temperature: float = 0.0
    pressure: float = None  # hPa (optional)
    wifi_strength: int = 0
    timestamp: float = field(default_factory=time.time)
    is_valid: bool = True
    
    @classmethod
    def from_esp32_data(cls, data: Dict[str, Any]) -> 'TelemetryData':
        """Create telemetry from ESP32 JSON data."""
        try:
            imu_data = data.get("imu_data", {})
            return cls(
                latitude=data.get("lat", 0.0),
                longitude=data.get("lon", 0.0),
                heading=data.get("heading", 0.0),
                acceleration=imu_data.get("accel", [0.0, 0.0, 0.0]),
                gyroscope=imu_data.get("gyro", [0.0, 0.0, 0.0]),
                magnetometer=imu_data.get("mag", [0.0, 0.0, 0.0]),
                temperature=data.get("temperature", 0.0),
                pressure=data.get("pressure"),
                wifi_strength=data.get("wifi_strength", 0),
                is_valid=True
            )
        except (KeyError, TypeError, ValueError) as e:
            # Return invalid telemetry data for error cases
            return cls(is_valid=False)
    
    def has_valid_position(self) -> bool:
        """Check if position data is valid."""
        return (self.is_valid and 
                -90 <= self.latitude <= 90 and 
                -180 <= self.longitude <= 180 and
                (self.latitude != 0.0 or self.longitude != 0.0))


@dataclass
class RoverState:
    """Current rover state information."""
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    navigation_state: NavigationState = NavigationState.STOPPED
    current_speed: int = 50  # Speed percentage 0-100
    target_waypoint_index: int = 0
    total_waypoints: int = 0
    last_telemetry: Optional[TelemetryData] = None
    connection_ip: str = ""
    connection_port: int = 80
    error_message: str = ""
    
    def is_operational(self) -> bool:
        """Check if rover is operational (connected and has valid telemetry)."""
        return (self.connection_state == ConnectionState.CONNECTED and
                self.last_telemetry is not None and
                self.last_telemetry.is_valid)


@dataclass
class AppConfig:
    """Deprecated: retained minimal fields for compatibility; ConfigManager is the source of truth."""
    # Map settings used in code; values overridden by ConfigManager when available
    max_waypoints: int = 10


class AppState(QObject):
    """
    Application state manager with signal emission for GUI updates.
    
    Centralizes state management and provides signals for reactive UI updates.
    """
    
    # Signals for state changes
    connection_state_changed = pyqtSignal(ConnectionState)
    navigation_state_changed = pyqtSignal(NavigationState)
    telemetry_updated = pyqtSignal(TelemetryData)
    waypoints_changed = pyqtSignal(list)  # List[Waypoint]
    speed_changed = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._rover_state = RoverState()
        self._waypoints: List[Waypoint] = []
        self._config = AppConfig()
    
    @property
    def rover_state(self) -> RoverState:
        """Get current rover state."""
        return self._rover_state
    
    @property
    def waypoints(self) -> List[Waypoint]:
        """Get current waypoints list."""
        return self._waypoints.copy()
    
    @property
    def config(self) -> AppConfig:
        """Get application configuration."""
        return self._config
    
    def update_connection_state(self, state: ConnectionState, error_msg: str = ""):
        """Update connection state and emit signal."""
        if self._rover_state.connection_state != state:
            self._rover_state.connection_state = state
            self._rover_state.error_message = error_msg
            self.connection_state_changed.emit(state)
            if error_msg:
                self.error_occurred.emit(error_msg)
    
    def update_navigation_state(self, state: NavigationState):
        """Update navigation state and emit signal."""
        if self._rover_state.navigation_state != state:
            self._rover_state.navigation_state = state
            self.navigation_state_changed.emit(state)
    
    def update_telemetry(self, telemetry: TelemetryData):
        """Update telemetry data and emit signal."""
        self._rover_state.last_telemetry = telemetry
        self.telemetry_updated.emit(telemetry)
    
    def update_speed(self, speed: int):
        """Update rover speed and emit signal."""
        if 0 <= speed <= 100 and self._rover_state.current_speed != speed:
            self._rover_state.current_speed = speed
            self.speed_changed.emit(speed)
    
    def set_waypoints(self, waypoints: List[Waypoint]):
        """Set waypoints list and emit signal."""
        # Copy and renumber waypoints to maintain contiguous ordering
        self._waypoints = waypoints.copy()
        for index, waypoint in enumerate(self._waypoints):
            waypoint.id = index + 1
        self._rover_state.total_waypoints = len(self._waypoints)
        self.waypoints_changed.emit(self._waypoints)
    
    def add_waypoint(self, waypoint: Waypoint) -> bool:
        """Add waypoint if under limit."""
        if len(self._waypoints) < self._config.max_waypoints:
            waypoint.id = len(self._waypoints) + 1
            self._waypoints.append(waypoint)
            self._rover_state.total_waypoints = len(self._waypoints)
            self.waypoints_changed.emit(self._waypoints)
            return True
        return False
    
    def clear_waypoints(self):
        """Clear all waypoints."""
        self._waypoints.clear()
        self._rover_state.total_waypoints = 0
        self._rover_state.target_waypoint_index = 0
        self.waypoints_changed.emit(self._waypoints)
    
    def get_waypoints_for_esp32(self) -> List[Dict[str, float]]:
        """Get waypoints in ESP32-compatible format."""
        return [wp.to_esp32_format() for wp in self._waypoints]
    
    def set_connection_info(self, ip: str, port: int = 80):
        """Set connection information."""
        self._rover_state.connection_ip = ip
        self._rover_state.connection_port = port
    
    def emit_error(self, message: str):
        """Emit error signal."""
        self._rover_state.error_message = message
        self.error_occurred.emit(message)


@dataclass
class PathSegment:
    """A segment of the planned mission path."""
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    distance: float
    bearing: float
    estimated_time: float
    speed_profile: List[float] = field(default_factory=list)
    
    @classmethod
    def create_from_points(cls, start: Tuple[float, float], end: Tuple[float, float], 
                          speed_mps: float = 1.0) -> 'PathSegment':
        """Create path segment from two points."""
        from utils.helpers import calculate_distance, calculate_bearing
        
        distance = calculate_distance(start[0], start[1], end[0], end[1])
        bearing = calculate_bearing(start[0], start[1], end[0], end[1])
        estimated_time = distance / speed_mps if speed_mps > 0 else 0
        
        return cls(
            start_point=start,
            end_point=end,
            distance=distance,
            bearing=bearing,
            estimated_time=estimated_time
        )


@dataclass
class MissionPlan:
    """Complete mission plan with waypoints, path, and metadata."""
    waypoints: List[Waypoint]
    planned_path: List[Tuple[float, float]] = field(default_factory=list)
    path_segments: List[PathSegment] = field(default_factory=list)
    total_distance: float = 0.0
    estimated_duration: float = 0.0
    average_speed: float = 1.0
    created_timestamp: float = field(default_factory=time.time)
    optimization_method: str = "nearest_neighbor"
    # Enhanced ESP32 parameters
    cte_threshold: float = 2.0
    mission_timeout: float = 3600.0  # 1 hour default
    mission_id: str = field(default_factory=lambda: f"mission_{int(time.time())}")
    
    def __post_init__(self):
        """Calculate mission statistics if not provided."""
        if self.path_segments and not self.total_distance:
            self.total_distance = sum(segment.distance for segment in self.path_segments)
        
        if self.path_segments and not self.estimated_duration:
            self.estimated_duration = sum(segment.estimated_time for segment in self.path_segments)
    
    @property
    def waypoint_count(self) -> int:
        """Get number of waypoints in mission."""
        return len(self.waypoints)
    
    @property
    def segment_count(self) -> int:
        """Get number of path segments."""
        return len(self.path_segments)
    
    def get_mission_summary(self) -> Dict[str, Any]:
        """Get mission summary statistics."""
        return {
            "waypoints": self.waypoint_count,
            "segments": self.segment_count,
            "total_distance_m": round(self.total_distance, 2),
            "estimated_duration_sec": round(self.estimated_duration, 2),
            "estimated_duration_min": round(self.estimated_duration / 60, 2),
            "average_speed_mps": self.average_speed,
            "created": self.created_timestamp,
            "optimization": self.optimization_method
        }
    
    def to_esp32_format(self) -> Dict[str, Any]:
        """Convert mission plan to ESP32-compatible JSON format."""
        return {
            "mission_id": self.mission_id,
            "command": "start_mission",
            "waypoints": [wp.to_esp32_format() for wp in self.waypoints],
            "path_segments": [
                {
                    "start_lat": seg.start_point[0],
                    "start_lon": seg.start_point[1],
                    "end_lat": seg.end_point[0],
                    "end_lon": seg.end_point[1],
                    "distance": round(seg.distance, 2),
                    "bearing": round(seg.bearing, 2),
                    "speed": self.average_speed
                }
                for seg in self.path_segments
            ],
            "parameters": {
                "speed_mps": self.average_speed,
                "cte_threshold_m": self.cte_threshold,
                "mission_timeout_s": int(self.mission_timeout),
                "total_distance_m": round(self.total_distance, 2),
                "estimated_duration_s": int(self.estimated_duration),
                "optimization_method": self.optimization_method
            },
            "metadata": {
                "created_timestamp": self.created_timestamp,
                "waypoint_count": self.waypoint_count,
                "segment_count": self.segment_count
            }
        }


@dataclass
class MissionProgress:
    """Real-time mission progress tracking."""
    current_position: Tuple[float, float]
    current_waypoint_index: int
    target_waypoint: Optional[Waypoint] = None
    distance_to_target: float = 0.0
    cross_track_error: float = 0.0
    completion_percentage: float = 0.0
    segments_completed: int = 0
    total_segments: int = 0
    elapsed_time: float = 0.0
    estimated_time_remaining: float = 0.0
    current_speed: float = 0.0
    average_speed: float = 0.0
    mission_status: str = "not_started"  # not_started, active, paused, completed, aborted
    deviation_count: int = 0
    last_update: float = field(default_factory=time.time)
    
    @property
    def is_active(self) -> bool:
        """Check if mission is currently active."""
        return self.mission_status == "active"
    
    @property
    def is_completed(self) -> bool:
        """Check if mission is completed."""
        return self.mission_status == "completed"
    
    @property
    def has_significant_deviation(self) -> bool:
        """Check if rover has significant path deviation."""
        return abs(self.cross_track_error) > 5.0  # 5 meter threshold
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get progress summary for display."""
        return {
            "completion_pct": round(self.completion_percentage, 1),
            "current_waypoint": self.current_waypoint_index + 1,
            "segments_done": self.segments_completed,
            "total_segments": self.total_segments,
            "distance_to_target_m": round(self.distance_to_target, 2),
            "cross_track_error_m": round(self.cross_track_error, 2),
            "elapsed_min": round(self.elapsed_time / 60, 2),
            "eta_min": round(self.estimated_time_remaining / 60, 2),
            "current_speed_mps": round(self.current_speed, 2),
            "status": self.mission_status,
            "deviations": self.deviation_count
        }


@dataclass
class MissionAnalytics:
    """Post-mission analysis and performance metrics."""
    planned_mission: MissionPlan
    actual_path: List[Tuple[float, float]]
    completion_time: float
    average_speed: float
    max_cross_track_error: float
    total_deviation_time: float
    waypoints_reached: int
    mission_success: bool
    efficiency_rating: float  # 0-100 scale
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary."""
        return {
            "success": self.mission_success,
            "completion_time_min": round(self.completion_time / 60, 2),
            "planned_time_min": round(self.planned_mission.estimated_duration / 60, 2),
            "time_efficiency_pct": round((self.planned_mission.estimated_duration / self.completion_time) * 100, 1),
            "average_speed_mps": round(self.average_speed, 2),
            "max_deviation_m": round(self.max_cross_track_error, 2),
            "waypoints_reached": self.waypoints_reached,
            "total_waypoints": self.planned_mission.waypoint_count,
            "efficiency_rating": round(self.efficiency_rating, 1),
            "deviation_time_min": round(self.total_deviation_time / 60, 2)
        }
