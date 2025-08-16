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
class BNO055CalibrationStatus:
    """
    BNO055 calibration status matching ESP32 BNO055CalibrationStatus structure.
    
    Each sensor calibration ranges from 0-3:
    - 0: Uncalibrated
    - 1: Poor calibration
    - 2: Good calibration  
    - 3: Fully calibrated
    """
    system: int = 0          # System calibration status (0-3)
    gyroscope: int = 0       # Gyroscope calibration status (0-3)
    accelerometer: int = 0   # Accelerometer calibration status (0-3)
    magnetometer: int = 0    # Magnetometer calibration status (0-3)
    
    def __post_init__(self):
        """Validate calibration values are in valid range."""
        for field_name, value in [("system", self.system), ("gyroscope", self.gyroscope), 
                                 ("accelerometer", self.accelerometer), ("magnetometer", self.magnetometer)]:
            if not (0 <= value <= 3):
                raise ValueError(f"Invalid {field_name} calibration: {value}. Must be 0-3.")
    
    def is_fully_calibrated(self) -> bool:
        """Check if all sensors are fully calibrated."""
        return (self.system >= 3 and self.gyroscope >= 3 and 
                self.accelerometer >= 3 and self.magnetometer >= 3)
    
    def is_magnetometer_calibrated(self) -> bool:
        """Check if magnetometer is sufficiently calibrated for heading accuracy."""
        return self.magnetometer >= 3
    
    def get_overall_status(self) -> str:
        """Get human-readable overall calibration status."""
        if self.is_fully_calibrated():
            return "Fully Calibrated"
        elif self.magnetometer >= 3:
            return "Heading Ready"
        elif max(self.system, self.gyroscope, self.accelerometer, self.magnetometer) >= 2:
            return "Calibrating..."
        else:
            return "Needs Calibration"
    
    @classmethod
    def from_esp32_data(cls, data: Dict[str, Any]) -> 'BNO055CalibrationStatus':
        """Create calibration status from ESP32 telemetry data."""
        return cls(
            system=data.get("sys", 0),
            gyroscope=data.get("gyro", 0),
            accelerometer=data.get("accel", 0),
            magnetometer=data.get("mag", 0)
        )


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
    Enhanced telemetry data model for BNO055 ESP32 rover output format.
    
    ESP32 BNO055 sends: {
        "lat": float, "lon": float, "heading": float,
        "imu_data": {
            "roll": float, "pitch": float,
            "quaternion": [w, x, y, z],
            "accel": [x,y,z], "gyro": [x,y,z], "mag": [x,y,z],
            "linear_accel": [x,y,z], "gravity": [x,y,z],
            "calibration": {"sys": 0-3, "gyro": 0-3, "accel": 0-3, "mag": 0-3},
            "temperature": float
        },
        "wifi_strength": int
    }
    """
    # Position and orientation
    latitude: float = 0.0
    longitude: float = 0.0
    heading: float = 0.0
    roll: float = 0.0        # Roll angle in degrees (aviation convention)
    pitch: float = 0.0       # Pitch angle in degrees (aviation convention)
    
    # Quaternion data for advanced navigation
    quaternion: List[float] = field(default_factory=lambda: [1.0, 0.0, 0.0, 0.0])  # [w, x, y, z]
    
    # Raw sensor data (legacy compatibility)
    acceleration: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    gyroscope: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    magnetometer: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    
    # Enhanced BNO055 sensor data
    linear_acceleration: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])  # Gravity removed
    gravity_vector: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])      # Gravity only
    
    # Calibration status
    calibration_status: BNO055CalibrationStatus = field(default_factory=BNO055CalibrationStatus)
    
    # Environmental and system data
    temperature: float = 0.0
    pressure: float = None  # hPa (optional)
    wifi_strength: int = 0
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    is_valid: bool = True
    has_enhanced_imu: bool = False  # True if BNO055 data is present
    
    @classmethod
    def from_esp32_data(cls, data: Dict[str, Any]) -> 'TelemetryData':
        """Create telemetry from ESP32 JSON data, supporting both legacy and BNO055 formats."""
        try:
            imu_data = data.get("imu_data", {})
            
            # Check if this is enhanced BNO055 format
            has_enhanced = any(key in imu_data for key in ["roll", "pitch", "quaternion", "calibration"])
            
            # Create calibration status
            calibration_data = imu_data.get("calibration", {})
            calibration_status = BNO055CalibrationStatus.from_esp32_data(calibration_data) if calibration_data else BNO055CalibrationStatus()
            
            return cls(
                # Position and basic orientation
                latitude=data.get("lat", 0.0),
                longitude=data.get("lon", 0.0),
                heading=data.get("heading", 0.0),
                
                # BNO055 enhanced orientation (if available)
                roll=imu_data.get("roll", 0.0) if has_enhanced else 0.0,
                pitch=imu_data.get("pitch", 0.0) if has_enhanced else 0.0,
                quaternion=imu_data.get("quaternion", [1.0, 0.0, 0.0, 0.0]) if has_enhanced else [1.0, 0.0, 0.0, 0.0],
                
                # Raw sensor data (legacy compatibility)
                acceleration=imu_data.get("accel", [0.0, 0.0, 0.0]),
                gyroscope=imu_data.get("gyro", [0.0, 0.0, 0.0]),
                magnetometer=imu_data.get("mag", [0.0, 0.0, 0.0]),
                
                # Enhanced BNO055 data (if available)
                linear_acceleration=imu_data.get("linear_accel", [0.0, 0.0, 0.0]) if has_enhanced else [0.0, 0.0, 0.0],
                gravity_vector=imu_data.get("gravity", [0.0, 0.0, 0.0]) if has_enhanced else [0.0, 0.0, 0.0],
                
                # Calibration status
                calibration_status=calibration_status,
                
                # Environmental and system
                temperature=imu_data.get("temperature", data.get("temperature", 0.0)),
                pressure=data.get("pressure"),
                wifi_strength=data.get("wifi_strength", 0),
                
                # Metadata
                is_valid=True,
                has_enhanced_imu=has_enhanced
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
    
    def is_navigation_ready(self) -> bool:
        """Check if BNO055 is calibrated enough for reliable navigation."""
        return (self.is_valid and self.has_enhanced_imu and 
                self.calibration_status.is_magnetometer_calibrated())
    
    def get_orientation_summary(self) -> str:
        """Get human-readable orientation summary."""
        if not self.has_enhanced_imu:
            return f"Heading: {self.heading:.1f}°"
        return f"H: {self.heading:.1f}° R: {self.roll:.1f}° P: {self.pitch:.1f}°"
    
    def get_calibration_summary(self) -> str:
        """Get human-readable calibration status summary."""
        if not self.has_enhanced_imu:
            return "Legacy IMU"
        return self.calibration_status.get_overall_status()


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
        self._max_waypoints = 10  # Default value, can be overridden by ConfigManager
    
    @property
    def rover_state(self) -> RoverState:
        """Get current rover state."""
        return self._rover_state
    
    @property
    def waypoints(self) -> List[Waypoint]:
        """Get current waypoints list."""
        return self._waypoints.copy()
    
    @property
    def max_waypoints(self) -> int:
        """Get maximum waypoints limit."""
        return self._max_waypoints
    
    def set_max_waypoints(self, value: int):
        """Set maximum waypoints limit (called by ConfigManager)."""
        self._max_waypoints = value
    
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
        if len(self._waypoints) < self._max_waypoints:
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
