"""
Main mission planner for ESP32 rover autonomous navigation.

Coordinates path planning, real-time tracking, and mission management
with comprehensive progress monitoring and deviation detection.
"""

import time
import logging
from typing import List, Tuple, Optional, Dict, Any
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from core.models import (
    Waypoint, TelemetryData, MissionPlan, MissionProgress, 
    MissionAnalytics, PathSegment
)
from .algorithms import PathPlanningAlgorithms, WaypointOptimizer, PathValidator
from .path_optimizer import PathOptimizer
from .trajectory import TrajectoryManager


class MissionPlanner(QObject):
    """
    Main mission planner service for autonomous rover navigation.
    
    Handles mission planning, real-time tracking, and performance analysis
    with intelligent path optimization and deviation monitoring.
    """
    
    # Signals for mission events
    mission_plan_ready = pyqtSignal(object)         # MissionPlan
    mission_started = pyqtSignal(object)            # MissionPlan
    mission_progress_updated = pyqtSignal(object)   # MissionProgress
    mission_completed = pyqtSignal(object)          # MissionAnalytics
    mission_aborted = pyqtSignal(str)               # reason
    
    # Path tracking signals
    waypoint_reached = pyqtSignal(int)              # waypoint_index
    path_deviation_detected = pyqtSignal(float)     # cross_track_error
    speed_adjustment_recommended = pyqtSignal(float) # recommended_speed
    
    # Status signals
    planning_status_changed = pyqtSignal(str)       # status_message
    error_occurred = pyqtSignal(str)                # error_message
    
    def __init__(self):
        super().__init__()
        
        # Core components
        self.path_algorithms = PathPlanningAlgorithms()
        self.waypoint_optimizer = WaypointOptimizer()
        self.path_optimizer = PathOptimizer()
        self.trajectory_manager = TrajectoryManager()
        self.path_validator = PathValidator()
        
        # Mission state
        self.current_mission: Optional[MissionPlan] = None
        self.current_progress: Optional[MissionProgress] = None
        self.mission_start_time: Optional[float] = None
        self.position_history: List[Tuple[float, float]] = []
        
        # Configuration
        self.default_speed = 1.0  # m/s
        self.waypoint_reach_threshold = 2.0  # meters
        self.deviation_threshold = 5.0  # meters
        self.max_deviation_count = 5
        
        # Timers
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_mission_metrics)
        
        # Logging
        self.logger = logging.getLogger('MissionPlanner')
        
        self.logger.info("Mission planner initialized")
    
    def plan_mission(self, 
                    waypoints: List[Waypoint], 
                    start_position: Optional[Tuple[float, float]] = None,
                    optimize_order: bool = True,
                    rover_speed: float = None,
                    cte_threshold: float = 2.0) -> bool:
        """
        Plan a complete mission from waypoints.
        
        Args:
            waypoints: List of mission waypoints
            start_position: Current rover position (optional)
            optimize_order: Whether to optimize waypoint order
            rover_speed: Expected rover speed in m/s
            
        Returns:
            True if mission planning successful
        """
        try:
            if not waypoints:
                self.error_occurred.emit("No waypoints provided for mission planning")
                return False
            
            self.planning_status_changed.emit("Validating waypoints...")
            
            # Convert waypoints to coordinate tuples
            waypoint_coords = [(wp.latitude, wp.longitude) for wp in waypoints]
            
            # Validate waypoint sequence
            is_valid, error_msg = self.path_validator.validate_waypoint_sequence(waypoint_coords)
            if not is_valid:
                self.error_occurred.emit(f"Waypoint validation failed: {error_msg}")
                return False
            
            self.planning_status_changed.emit("Optimizing waypoint order...")
            
            # Optimize waypoint order if requested
            optimized_waypoints = waypoints.copy()
            if optimize_order and len(waypoints) > 1:
                if start_position:
                    optimized_coords = self.waypoint_optimizer.optimize_waypoint_sequence(
                        waypoint_coords, start_position
                    )
                    # Reorder waypoints to match optimized sequence
                    waypoint_map = {(wp.latitude, wp.longitude): wp for wp in waypoints}
                    optimized_waypoints = [waypoint_map[coord] for coord in optimized_coords]
                else:
                    self.logger.warning("No start position provided, skipping waypoint optimization")
            
            self.planning_status_changed.emit("Generating optimal path...")
            
            # Generate path through waypoints
            if start_position:
                all_coords = [start_position] + [(wp.latitude, wp.longitude) for wp in optimized_waypoints]
            else:
                all_coords = [(wp.latitude, wp.longitude) for wp in optimized_waypoints]
            
            # Generate smooth path
            smooth_path = self.path_optimizer.generate_smooth_path(all_coords)
            
            self.planning_status_changed.emit("Creating path segments...")
            
            # Create path segments
            speed = rover_speed or self.default_speed
            path_segments = []
            
            for i in range(len(smooth_path) - 1):
                segment = PathSegment.create_from_points(
                    smooth_path[i], smooth_path[i + 1], speed
                )
                path_segments.append(segment)
            
            # Calculate mission statistics
            total_distance = sum(seg.distance for seg in path_segments)
            estimated_duration = sum(seg.estimated_time for seg in path_segments)
            
            # Create mission plan
            self.current_mission = MissionPlan(
                waypoints=optimized_waypoints,
                planned_path=smooth_path,
                path_segments=path_segments,
                total_distance=total_distance,
                estimated_duration=estimated_duration,
                average_speed=speed,
                optimization_method="nearest_neighbor" if optimize_order else "original_order",
                cte_threshold=cte_threshold
            )
            
            self.planning_status_changed.emit("Mission plan ready!")
            self.mission_plan_ready.emit(self.current_mission)
            
            self.logger.info(f"Mission planned: {len(optimized_waypoints)} waypoints, "
                           f"{total_distance:.2f}m, {estimated_duration:.1f}s")
            
            return True
            
        except Exception as e:
            error_msg = f"Mission planning failed: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def start_mission(self, current_position: Tuple[float, float]) -> bool:
        """
        Start mission execution with real-time tracking.
        
        Args:
            current_position: Current rover position
            
        Returns:
            True if mission started successfully
        """
        if not self.current_mission:
            self.error_occurred.emit("No mission plan available to start")
            return False
        
        try:
            # Initialize mission progress
            self.current_progress = MissionProgress(
                current_position=current_position,
                current_waypoint_index=0,
                target_waypoint=self.current_mission.waypoints[0] if self.current_mission.waypoints else None,
                total_segments=len(self.current_mission.path_segments),
                mission_status="active"
            )
            
            # Initialize tracking
            self.mission_start_time = time.time()
            self.position_history = [current_position]
            
            # Start progress monitoring
            self.progress_timer.start(1000)  # Update every second
            
            self.mission_started.emit(self.current_mission)
            self.logger.info("Mission started")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to start mission: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def update_rover_position(self, telemetry: TelemetryData):
        """
        Update rover position and calculate mission progress.
        
        Args:
            telemetry: Current rover telemetry data
        """
        if not self.current_progress or not self.current_mission:
            return
        
        if not telemetry.has_valid_position():
            return
        
        current_pos = (telemetry.latitude, telemetry.longitude)
        
        try:
            # Update position history
            self.position_history.append(current_pos)
            
            # Update current position
            self.current_progress.current_position = current_pos
            self.current_progress.current_speed = telemetry.get('speed', 0.0) if hasattr(telemetry, 'speed') else 0.0
            self.current_progress.last_update = time.time()
            
            # Calculate distance to current target waypoint
            if self.current_progress.target_waypoint:
                from utils.helpers import calculate_distance
                self.current_progress.distance_to_target = calculate_distance(
                    current_pos[0], current_pos[1],
                    self.current_progress.target_waypoint.latitude,
                    self.current_progress.target_waypoint.longitude
                )
                
                # Check if waypoint reached
                if self.current_progress.distance_to_target <= self.waypoint_reach_threshold:
                    self._handle_waypoint_reached()
            
            # Calculate cross-track error
            self._calculate_cross_track_error()
            
            # Update completion percentage
            self._update_completion_percentage()
            
            # Emit progress update
            self.mission_progress_updated.emit(self.current_progress)
            
        except Exception as e:
            self.logger.error(f"Error updating rover position: {str(e)}")
    
    def _handle_waypoint_reached(self):
        """Handle waypoint reached event."""
        if not self.current_progress or not self.current_mission:
            return
        
        current_idx = self.current_progress.current_waypoint_index
        self.waypoint_reached.emit(current_idx)
        
        # Move to next waypoint
        next_idx = current_idx + 1
        if next_idx < len(self.current_mission.waypoints):
            self.current_progress.current_waypoint_index = next_idx
            self.current_progress.target_waypoint = self.current_mission.waypoints[next_idx]
            self.logger.info(f"Moving to waypoint {next_idx + 1}")
        else:
            # Mission completed
            self._complete_mission()
    
    def _calculate_cross_track_error(self):
        """Calculate cross-track error from planned path."""
        if not self.current_progress or not self.current_mission:
            return
        
        # Find current path segment
        current_segment = self._get_current_path_segment()
        if not current_segment:
            return
        
        # Calculate cross-track error using trajectory manager
        error = self.trajectory_manager.calculate_cross_track_error(
            self.current_progress.current_position,
            current_segment.start_point,
            current_segment.end_point
        )
        
        self.current_progress.cross_track_error = error
        
        # Check for significant deviation
        if abs(error) > self.deviation_threshold:
            self.current_progress.deviation_count += 1
            self.path_deviation_detected.emit(error)
            
            if self.current_progress.deviation_count > self.max_deviation_count:
                self.logger.warning("Excessive path deviations detected")
    
    def _get_current_path_segment(self) -> Optional[PathSegment]:
        """Get current path segment based on progress."""
        if not self.current_progress or not self.current_mission:
            return None
        
        segment_idx = min(
            self.current_progress.current_waypoint_index,
            len(self.current_mission.path_segments) - 1
        )
        
        if 0 <= segment_idx < len(self.current_mission.path_segments):
            return self.current_mission.path_segments[segment_idx]
        
        return None
    
    def _update_completion_percentage(self):
        """Update mission completion percentage."""
        if not self.current_progress or not self.current_mission:
            return
        
        total_waypoints = len(self.current_mission.waypoints)
        if total_waypoints == 0:
            return
        
        completed_waypoints = self.current_progress.current_waypoint_index
        self.current_progress.completion_percentage = (completed_waypoints / total_waypoints) * 100
    
    def _update_mission_metrics(self):
        """Update mission timing metrics."""
        if not self.current_progress or not self.mission_start_time:
            return
        
        current_time = time.time()
        self.current_progress.elapsed_time = current_time - self.mission_start_time
        
        # Calculate average speed
        if len(self.position_history) > 1:
            from utils.helpers import calculate_distance
            total_distance = 0
            for i in range(len(self.position_history) - 1):
                pos1 = self.position_history[i]
                pos2 = self.position_history[i + 1]
                total_distance += calculate_distance(pos1[0], pos1[1], pos2[0], pos2[1])
            
            if self.current_progress.elapsed_time > 0:
                self.current_progress.average_speed = total_distance / self.current_progress.elapsed_time
        
        # Estimate time remaining
        remaining_percentage = 100 - self.current_progress.completion_percentage
        if self.current_progress.completion_percentage > 0:
            estimated_total_time = self.current_progress.elapsed_time / (self.current_progress.completion_percentage / 100)
            self.current_progress.estimated_time_remaining = max(0, estimated_total_time - self.current_progress.elapsed_time)
    
    def _complete_mission(self):
        """Complete current mission and generate analytics."""
        if not self.current_progress or not self.current_mission:
            return
        
        self.current_progress.mission_status = "completed"
        self.current_progress.completion_percentage = 100.0
        
        # Stop progress monitoring
        self.progress_timer.stop()
        
        # Generate mission analytics
        analytics = self._generate_mission_analytics()
        
        self.mission_completed.emit(analytics)
        self.logger.info("Mission completed successfully")
    
    def _generate_mission_analytics(self) -> MissionAnalytics:
        """Generate comprehensive mission analytics."""
        if not self.current_progress or not self.current_mission:
            raise ValueError("No mission data available for analytics")
        
        completion_time = self.current_progress.elapsed_time
        waypoints_reached = self.current_progress.current_waypoint_index
        max_deviation = max((abs(self.current_progress.cross_track_error), 0))
        
        # Calculate efficiency rating
        time_efficiency = (self.current_mission.estimated_duration / completion_time) * 100 if completion_time > 0 else 0
        waypoint_efficiency = (waypoints_reached / len(self.current_mission.waypoints)) * 100
        deviation_penalty = max(0, 100 - (self.current_progress.deviation_count * 10))
        
        efficiency_rating = (time_efficiency * 0.4 + waypoint_efficiency * 0.4 + deviation_penalty * 0.2)
        efficiency_rating = min(100, max(0, efficiency_rating))
        
        return MissionAnalytics(
            planned_mission=self.current_mission,
            actual_path=self.position_history.copy(),
            completion_time=completion_time,
            average_speed=self.current_progress.average_speed,
            max_cross_track_error=max_deviation,
            total_deviation_time=0,  # Could be calculated from deviation events
            waypoints_reached=waypoints_reached,
            mission_success=waypoints_reached == len(self.current_mission.waypoints),
            efficiency_rating=efficiency_rating
        )
    
    def pause_mission(self):
        """Pause current mission."""
        if self.current_progress:
            self.current_progress.mission_status = "paused"
            self.progress_timer.stop()
            self.logger.info("Mission paused")
    
    def resume_mission(self):
        """Resume paused mission."""
        if self.current_progress and self.current_progress.mission_status == "paused":
            self.current_progress.mission_status = "active"
            self.progress_timer.start(1000)
            self.logger.info("Mission resumed")
    
    def abort_mission(self, reason: str = "User requested"):
        """Abort current mission."""
        if self.current_progress:
            self.current_progress.mission_status = "aborted"
            self.progress_timer.stop()
            self.mission_aborted.emit(reason)
            self.logger.info(f"Mission aborted: {reason}")
    
    def get_mission_status(self) -> Dict[str, Any]:
        """Get current mission status."""
        if not self.current_mission or not self.current_progress:
            return {"status": "no_mission"}
        
        return {
            "status": self.current_progress.mission_status,
            "mission_summary": self.current_mission.get_mission_summary(),
            "progress": self.current_progress.get_progress_summary()
        }
    
    def replan_mission(self, new_waypoints: List[Waypoint], current_position: Tuple[float, float]) -> bool:
        """
        Replan mission with new waypoints during execution.
        
        Args:
            new_waypoints: Updated waypoint list
            current_position: Current rover position
            
        Returns:
            True if replanning successful
        """
        self.logger.info("Replanning mission with updated waypoints")
        
        # Store current progress state
        was_active = self.current_progress and self.current_progress.is_active
        
        # Plan new mission
        success = self.plan_mission(new_waypoints, current_position, optimize_order=True)
        
        if success and was_active:
            # Restart mission with new plan
            self.start_mission(current_position)
        
        return success
