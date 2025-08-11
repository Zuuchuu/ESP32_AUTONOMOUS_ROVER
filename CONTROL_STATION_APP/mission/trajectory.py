"""
Trajectory management and path following algorithms for rover navigation.

Provides cross-track error calculation, path following algorithms,
and real-time trajectory corrections for precise rover guidance.
"""

import math
from typing import Tuple, List, Optional
import logging


class TrajectoryManager:
    """Manages rover trajectory following and path corrections."""
    
    def __init__(self):
        self.logger = logging.getLogger('TrajectoryManager')
        
        # Path following parameters
        self.look_ahead_distance = 3.0  # meters
        self.cross_track_tolerance = 1.0  # meters
        self.heading_tolerance = 5.0  # degrees
    
    def calculate_cross_track_error(self, 
                                  current_position: Tuple[float, float],
                                  path_start: Tuple[float, float], 
                                  path_end: Tuple[float, float]) -> float:
        """
        Calculate cross-track error (perpendicular distance) from path segment.
        
        Args:
            current_position: Current rover position (lat, lng)
            path_start: Path segment start point
            path_end: Path segment end point
            
        Returns:
            Cross-track error in meters (positive = right of path, negative = left)
        """
        from utils.helpers import calculate_distance, calculate_bearing
        
        # Calculate distance from current position to path start
        dist_to_start = calculate_distance(
            current_position[0], current_position[1],
            path_start[0], path_start[1]
        )
        
        # Calculate bearing from path start to current position
        bearing_to_current = calculate_bearing(
            path_start[0], path_start[1],
            current_position[0], current_position[1]
        )
        
        # Calculate path bearing (desired track)
        path_bearing = calculate_bearing(
            path_start[0], path_start[1],
            path_end[0], path_end[1]
        )
        
        # Calculate angle difference
        angle_diff = self._normalize_angle(bearing_to_current - path_bearing)
        
        # Calculate cross-track error using trigonometry
        cross_track_error = dist_to_start * math.sin(math.radians(angle_diff))
        
        self.logger.debug(f"Cross-track error: {cross_track_error:.2f}m")
        
        return cross_track_error
    
    def calculate_along_track_distance(self, 
                                     current_position: Tuple[float, float],
                                     path_start: Tuple[float, float], 
                                     path_end: Tuple[float, float]) -> float:
        """
        Calculate along-track distance (progress along path segment).
        
        Args:
            current_position: Current rover position
            path_start: Path segment start point  
            path_end: Path segment end point
            
        Returns:
            Along-track distance in meters
        """
        from utils.helpers import calculate_distance, calculate_bearing
        
        # Distance from start to current position
        dist_to_current = calculate_distance(
            path_start[0], path_start[1],
            current_position[0], current_position[1]
        )
        
        # Bearing from start to current position
        bearing_to_current = calculate_bearing(
            path_start[0], path_start[1],
            current_position[0], current_position[1]
        )
        
        # Path bearing
        path_bearing = calculate_bearing(
            path_start[0], path_start[1],
            path_end[0], path_end[1]
        )
        
        # Calculate angle difference
        angle_diff = self._normalize_angle(bearing_to_current - path_bearing)
        
        # Calculate along-track distance using trigonometry
        along_track_distance = dist_to_current * math.cos(math.radians(angle_diff))
        
        return along_track_distance
    
    def calculate_pure_pursuit_steering(self, 
                                      current_position: Tuple[float, float],
                                      current_heading: float,
                                      target_point: Tuple[float, float]) -> float:
        """
        Calculate steering angle using Pure Pursuit algorithm.
        
        Args:
            current_position: Current rover position
            current_heading: Current rover heading in degrees
            target_point: Target point to pursue
            
        Returns:
            Steering angle in degrees (-180 to 180)
        """
        from utils.helpers import calculate_distance, calculate_bearing
        
        # Calculate distance to target
        distance_to_target = calculate_distance(
            current_position[0], current_position[1],
            target_point[0], target_point[1]
        )
        
        # Calculate bearing to target
        bearing_to_target = calculate_bearing(
            current_position[0], current_position[1],
            target_point[0], target_point[1]
        )
        
        # Calculate heading error
        heading_error = self._normalize_angle(bearing_to_target - current_heading)
        
        # Pure pursuit steering calculation
        # For differential drive: steering_angle ≈ 2 * sin(heading_error) * distance / look_ahead_distance
        look_ahead = max(self.look_ahead_distance, distance_to_target)
        
        if look_ahead > 0:
            steering_angle = math.degrees(2 * math.asin(
                min(1.0, abs(math.sin(math.radians(heading_error)) * distance_to_target / look_ahead))
            ))
            
            # Preserve sign
            if heading_error < 0:
                steering_angle = -steering_angle
        else:
            steering_angle = 0.0
        
        self.logger.debug(f"Pure pursuit steering: {steering_angle:.1f}°")
        
        return steering_angle
    
    def find_look_ahead_point(self, 
                            current_position: Tuple[float, float],
                            path_points: List[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
        """
        Find look-ahead point on path for Pure Pursuit algorithm.
        
        Args:
            current_position: Current rover position
            path_points: List of path points
            
        Returns:
            Look-ahead point or None if not found
        """
        from utils.helpers import calculate_distance
        
        if not path_points:
            return None
        
        # Find closest point on path
        closest_idx = 0
        min_distance = float('inf')
        
        for i, point in enumerate(path_points):
            distance = calculate_distance(
                current_position[0], current_position[1],
                point[0], point[1]
            )
            if distance < min_distance:
                min_distance = distance
                closest_idx = i
        
        # Find look-ahead point starting from closest point
        for i in range(closest_idx, len(path_points)):
            point = path_points[i]
            distance = calculate_distance(
                current_position[0], current_position[1],
                point[0], point[1]
            )
            
            if distance >= self.look_ahead_distance:
                return point
        
        # If no point found at look-ahead distance, return last point
        if path_points:
            return path_points[-1]
        
        return None
    
    def calculate_path_progress(self, 
                              current_position: Tuple[float, float],
                              path_points: List[Tuple[float, float]]) -> Tuple[float, int]:
        """
        Calculate progress along path.
        
        Args:
            current_position: Current rover position
            path_points: Complete path points
            
        Returns:
            Tuple of (progress_percentage, closest_segment_index)
        """
        if len(path_points) < 2:
            return 0.0, 0
        
        from utils.helpers import calculate_distance
        
        # Find closest segment
        min_distance = float('inf')
        closest_segment_idx = 0
        
        for i in range(len(path_points) - 1):
            # Calculate distance to path segment
            segment_distance = self._point_to_segment_distance(
                current_position, path_points[i], path_points[i + 1]
            )
            
            if segment_distance < min_distance:
                min_distance = segment_distance
                closest_segment_idx = i
        
        # Calculate total path length
        total_path_length = 0.0
        for i in range(len(path_points) - 1):
            segment_length = calculate_distance(
                path_points[i][0], path_points[i][1],
                path_points[i + 1][0], path_points[i + 1][1]
            )
            total_path_length += segment_length
        
        # Calculate distance traveled to closest segment
        distance_traveled = 0.0
        for i in range(closest_segment_idx):
            segment_length = calculate_distance(
                path_points[i][0], path_points[i][1],
                path_points[i + 1][0], path_points[i + 1][1]
            )
            distance_traveled += segment_length
        
        # Add progress within current segment
        if closest_segment_idx < len(path_points) - 1:
            along_track = self.calculate_along_track_distance(
                current_position,
                path_points[closest_segment_idx],
                path_points[closest_segment_idx + 1]
            )
            distance_traveled += max(0, along_track)
        
        # Calculate progress percentage
        if total_path_length > 0:
            progress_percentage = (distance_traveled / total_path_length) * 100
        else:
            progress_percentage = 0.0
        
        progress_percentage = max(0.0, min(100.0, progress_percentage))
        
        return progress_percentage, closest_segment_idx
    
    def _point_to_segment_distance(self, 
                                 point: Tuple[float, float],
                                 segment_start: Tuple[float, float], 
                                 segment_end: Tuple[float, float]) -> float:
        """Calculate minimum distance from point to line segment."""
        from utils.helpers import calculate_distance
        
        # Calculate distance to start and end points
        dist_to_start = calculate_distance(
            point[0], point[1], segment_start[0], segment_start[1]
        )
        dist_to_end = calculate_distance(
            point[0], point[1], segment_end[0], segment_end[1]
        )
        
        # Calculate along-track distance
        along_track = self.calculate_along_track_distance(point, segment_start, segment_end)
        
        # Calculate segment length
        segment_length = calculate_distance(
            segment_start[0], segment_start[1], segment_end[0], segment_end[1]
        )
        
        # Check if projection falls within segment
        if 0 <= along_track <= segment_length:
            # Point projects onto segment - use cross-track error
            return abs(self.calculate_cross_track_error(point, segment_start, segment_end))
        elif along_track < 0:
            # Point is before segment start
            return dist_to_start
        else:
            # Point is after segment end
            return dist_to_end
    
    def calculate_heading_correction(self, 
                                   current_heading: float,
                                   desired_heading: float) -> float:
        """
        Calculate heading correction needed.
        
        Args:
            current_heading: Current rover heading in degrees
            desired_heading: Desired heading in degrees
            
        Returns:
            Heading correction in degrees (-180 to 180)
        """
        heading_error = self._normalize_angle(desired_heading - current_heading)
        
        # Apply deadband to avoid oscillation
        if abs(heading_error) < self.heading_tolerance:
            heading_error = 0.0
        
        return heading_error
    
    def is_on_track(self, 
                   cross_track_error: float,
                   heading_error: float) -> bool:
        """
        Check if rover is following path within tolerances.
        
        Args:
            cross_track_error: Cross-track error in meters
            heading_error: Heading error in degrees
            
        Returns:
            True if rover is on track
        """
        position_ok = abs(cross_track_error) <= self.cross_track_tolerance
        heading_ok = abs(heading_error) <= self.heading_tolerance
        
        return position_ok and heading_ok
    
    def predict_intercept_point(self, 
                              current_position: Tuple[float, float],
                              current_velocity: float,
                              target_point: Tuple[float, float],
                              target_velocity: float = 0.0) -> Tuple[float, float]:
        """
        Predict intercept point for moving target.
        
        Args:
            current_position: Current rover position
            current_velocity: Rover velocity in m/s
            target_point: Target position
            target_velocity: Target velocity in m/s (0 for stationary)
            
        Returns:
            Predicted intercept point
        """
        from utils.helpers import calculate_distance, calculate_bearing
        
        if target_velocity == 0.0 or current_velocity == 0.0:
            return target_point
        
        # Distance to target
        distance_to_target = calculate_distance(
            current_position[0], current_position[1],
            target_point[0], target_point[1]
        )
        
        # Time to intercept (simplified calculation)
        time_to_intercept = distance_to_target / current_velocity
        
        # For stationary target, return target point
        if target_velocity == 0.0:
            return target_point
        
        # For moving target, predict future position
        # (This is a simplified calculation - real implementation would need target heading)
        target_bearing = calculate_bearing(
            current_position[0], current_position[1],
            target_point[0], target_point[1]
        )
        
        # Predict target movement (assuming constant bearing for simplicity)
        predicted_distance = target_velocity * time_to_intercept
        
        # Convert to lat/lng offset (approximate)
        lat_offset = predicted_distance * math.cos(math.radians(target_bearing)) / 111000
        lng_offset = predicted_distance * math.sin(math.radians(target_bearing)) / (111000 * math.cos(math.radians(target_point[0])))
        
        predicted_position = (
            target_point[0] + lat_offset,
            target_point[1] + lng_offset
        )
        
        return predicted_position
    
    def _normalize_angle(self, angle: float) -> float:
        """Normalize angle to -180 to 180 range."""
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle
    
    def set_look_ahead_distance(self, distance: float):
        """Set look-ahead distance for path following."""
        self.look_ahead_distance = max(0.5, distance)
        self.logger.info(f"Look-ahead distance set to {self.look_ahead_distance:.1f}m")
    
    def set_tolerances(self, cross_track_tolerance: float, heading_tolerance: float):
        """Set path following tolerances."""
        self.cross_track_tolerance = max(0.1, cross_track_tolerance)
        self.heading_tolerance = max(1.0, heading_tolerance)
        self.logger.info(f"Tolerances set: cross-track={self.cross_track_tolerance:.1f}m, "
                        f"heading={self.heading_tolerance:.1f}°")
