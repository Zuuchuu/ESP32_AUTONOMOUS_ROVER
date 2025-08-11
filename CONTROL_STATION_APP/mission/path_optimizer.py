"""
Path optimization and smoothing algorithms for rover navigation.

Provides path smoothing, curve generation, and trajectory optimization
for smooth and efficient rover movement along planned routes.
"""

import math
from typing import List, Tuple, Optional
import logging


class PathOptimizer:
    """Path smoothing and optimization for rover navigation."""
    
    def __init__(self):
        self.logger = logging.getLogger('PathOptimizer')
    
    def generate_smooth_path(self, 
                           waypoints: List[Tuple[float, float]], 
                           smoothing_factor: float = 0.3,
                           resolution: float = 0.0001) -> List[Tuple[float, float]]:
        """
        Generate smooth path through waypoints using spline interpolation.
        
        Args:
            waypoints: List of waypoint coordinates
            smoothing_factor: Path smoothing intensity (0.0 to 1.0)
            resolution: Path resolution in degrees
            
        Returns:
            List of smoothed path coordinates
        """
        if len(waypoints) < 2:
            return waypoints
        
        if smoothing_factor <= 0:
            return waypoints
        
        # For now, implement simple linear interpolation with curve smoothing
        # Could be enhanced with Bezier curves or B-splines for more advanced smoothing
        smooth_path = []
        
        for i in range(len(waypoints) - 1):
            current = waypoints[i]
            next_point = waypoints[i + 1]
            
            # Add current waypoint
            smooth_path.append(current)
            
            # Add interpolated points for smooth transition
            segment_points = self._interpolate_segment(current, next_point, resolution)
            
            # Apply smoothing if this is not the last segment
            if i < len(waypoints) - 2:
                prev_point = waypoints[i - 1] if i > 0 else current
                next_next = waypoints[i + 2]
                
                smoothed_segment = self._apply_curve_smoothing(
                    prev_point, current, next_point, next_next, 
                    segment_points, smoothing_factor
                )
                smooth_path.extend(smoothed_segment[1:])  # Skip duplicate current point
            else:
                smooth_path.extend(segment_points[1:])  # Skip duplicate current point
        
        # Add final waypoint
        smooth_path.append(waypoints[-1])
        
        self.logger.debug(f"Generated smooth path: {len(waypoints)} waypoints -> {len(smooth_path)} points")
        
        return smooth_path
    
    def _interpolate_segment(self, 
                           start: Tuple[float, float], 
                           end: Tuple[float, float], 
                           resolution: float) -> List[Tuple[float, float]]:
        """Interpolate points between two waypoints."""
        from utils.helpers import calculate_distance
        
        distance = calculate_distance(start[0], start[1], end[0], end[1])
        
        # Calculate number of interpolation points based on distance
        num_points = max(2, int(distance / (resolution * 111000)))  # Rough conversion to meters
        
        points = []
        for i in range(num_points):
            t = i / (num_points - 1)
            lat = start[0] + t * (end[0] - start[0])
            lng = start[1] + t * (end[1] - start[1])
            points.append((lat, lng))
        
        return points
    
    def _apply_curve_smoothing(self, 
                             prev_point: Tuple[float, float],
                             current: Tuple[float, float], 
                             next_point: Tuple[float, float],
                             next_next: Tuple[float, float],
                             segment_points: List[Tuple[float, float]], 
                             smoothing_factor: float) -> List[Tuple[float, float]]:
        """Apply curve smoothing to path segment."""
        # Simple curve smoothing using control points
        # More advanced implementation could use Catmull-Rom splines
        
        smoothed_points = []
        
        for i, point in enumerate(segment_points):
            if i == 0 or i == len(segment_points) - 1:
                # Keep start and end points unchanged
                smoothed_points.append(point)
                continue
            
            # Calculate smoothing offset
            t = i / (len(segment_points) - 1)
            
            # Simple curve calculation
            curve_offset = self._calculate_curve_offset(
                prev_point, current, next_point, next_next, t, smoothing_factor
            )
            
            smoothed_lat = point[0] + curve_offset[0]
            smoothed_lng = point[1] + curve_offset[1]
            
            smoothed_points.append((smoothed_lat, smoothed_lng))
        
        return smoothed_points
    
    def _calculate_curve_offset(self, 
                              prev_point: Tuple[float, float],
                              current: Tuple[float, float], 
                              next_point: Tuple[float, float],
                              next_next: Tuple[float, float],
                              t: float, 
                              smoothing_factor: float) -> Tuple[float, float]:
        """Calculate curve offset for smooth transitions."""
        # Calculate turn angle
        from utils.helpers import calculate_bearing
        
        bearing1 = calculate_bearing(prev_point[0], prev_point[1], current[0], current[1])
        bearing2 = calculate_bearing(current[0], current[1], next_point[0], next_point[1])
        bearing3 = calculate_bearing(next_point[0], next_point[1], next_next[0], next_next[1])
        
        # Calculate turn angles
        turn_angle1 = self._normalize_angle(bearing2 - bearing1)
        turn_angle2 = self._normalize_angle(bearing3 - bearing2)
        
        # Calculate curve intensity based on turn angle
        curve_intensity = smoothing_factor * (abs(turn_angle1) + abs(turn_angle2)) / 360
        
        # Calculate perpendicular offset for smooth curve
        mid_bearing = self._normalize_angle((bearing1 + bearing2) / 2)
        perp_bearing = self._normalize_angle(mid_bearing + 90)
        
        # Convert to offset in degrees (simplified)
        offset_distance = curve_intensity * 0.0001  # Small offset in degrees
        
        offset_lat = offset_distance * math.cos(math.radians(perp_bearing))
        offset_lng = offset_distance * math.sin(math.radians(perp_bearing))
        
        # Apply smoothing curve (bell curve)
        curve_factor = math.sin(t * math.pi)
        
        return (offset_lat * curve_factor, offset_lng * curve_factor)
    
    def _normalize_angle(self, angle: float) -> float:
        """Normalize angle to -180 to 180 range."""
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle
    
    def optimize_for_rover_constraints(self, 
                                     path_points: List[Tuple[float, float]], 
                                     max_turn_rate: float = 45.0,
                                     min_segment_length: float = 1.0) -> List[Tuple[float, float]]:
        """
        Optimize path for rover physical constraints.
        
        Args:
            path_points: Original path points
            max_turn_rate: Maximum turn rate in degrees per meter
            min_segment_length: Minimum segment length in meters
            
        Returns:
            Optimized path respecting rover constraints
        """
        if len(path_points) < 3:
            return path_points
        
        optimized_path = [path_points[0]]  # Always keep first point
        
        for i in range(1, len(path_points) - 1):
            prev_point = optimized_path[-1]
            current_point = path_points[i]
            next_point = path_points[i + 1]
            
            # Check segment length constraint
            from utils.helpers import calculate_distance
            segment_length = calculate_distance(
                prev_point[0], prev_point[1], current_point[0], current_point[1]
            )
            
            if segment_length < min_segment_length:
                continue  # Skip point if segment too short
            
            # Check turn rate constraint
            if len(optimized_path) >= 2:
                turn_rate = self._calculate_turn_rate(
                    optimized_path[-2], prev_point, current_point, segment_length
                )
                
                if abs(turn_rate) > max_turn_rate:
                    # Insert intermediate points to reduce turn rate
                    intermediate_points = self._insert_turn_smoothing_points(
                        prev_point, current_point, next_point, max_turn_rate
                    )
                    optimized_path.extend(intermediate_points)
                    continue
            
            optimized_path.append(current_point)
        
        # Always keep last point
        optimized_path.append(path_points[-1])
        
        self.logger.debug(f"Rover constraint optimization: {len(path_points)} -> {len(optimized_path)} points")
        
        return optimized_path
    
    def _calculate_turn_rate(self, 
                           point1: Tuple[float, float], 
                           point2: Tuple[float, float], 
                           point3: Tuple[float, float], 
                           segment_length: float) -> float:
        """Calculate turn rate in degrees per meter."""
        from utils.helpers import calculate_bearing
        
        bearing1 = calculate_bearing(point1[0], point1[1], point2[0], point2[1])
        bearing2 = calculate_bearing(point2[0], point2[1], point3[0], point3[1])
        
        turn_angle = self._normalize_angle(bearing2 - bearing1)
        
        if segment_length > 0:
            return abs(turn_angle) / segment_length
        
        return 0.0
    
    def _insert_turn_smoothing_points(self, 
                                    prev_point: Tuple[float, float],
                                    current_point: Tuple[float, float], 
                                    next_point: Tuple[float, float],
                                    max_turn_rate: float) -> List[Tuple[float, float]]:
        """Insert additional points to smooth sharp turns."""
        from utils.helpers import calculate_bearing, calculate_distance
        
        # Calculate required smoothing
        bearing1 = calculate_bearing(prev_point[0], prev_point[1], current_point[0], current_point[1])
        bearing2 = calculate_bearing(current_point[0], current_point[1], next_point[0], next_point[1])
        
        turn_angle = abs(self._normalize_angle(bearing2 - bearing1))
        
        if turn_angle < max_turn_rate:
            return [current_point]
        
        # Calculate smoothing arc
        smoothing_points = []
        
        # Simple approach: create arc around turn point
        arc_radius = 0.0001  # Small radius in degrees
        num_arc_points = max(3, int(turn_angle / max_turn_rate))
        
        for i in range(num_arc_points):
            t = i / (num_arc_points - 1)
            interpolated_bearing = bearing1 + t * (bearing2 - bearing1)
            
            # Calculate point on smoothing arc
            arc_lat = current_point[0] + arc_radius * math.cos(math.radians(interpolated_bearing))
            arc_lng = current_point[1] + arc_radius * math.sin(math.radians(interpolated_bearing))
            
            smoothing_points.append((arc_lat, arc_lng))
        
        return smoothing_points
    
    def calculate_path_curvature(self, path_points: List[Tuple[float, float]]) -> List[float]:
        """
        Calculate curvature at each point along the path.
        
        Args:
            path_points: Path coordinates
            
        Returns:
            List of curvature values (1/radius)
        """
        if len(path_points) < 3:
            return [0.0] * len(path_points)
        
        curvatures = [0.0]  # First point has zero curvature
        
        for i in range(1, len(path_points) - 1):
            prev_point = path_points[i - 1]
            current_point = path_points[i]
            next_point = path_points[i + 1]
            
            curvature = self._calculate_point_curvature(prev_point, current_point, next_point)
            curvatures.append(curvature)
        
        curvatures.append(0.0)  # Last point has zero curvature
        
        return curvatures
    
    def _calculate_point_curvature(self, 
                                 point1: Tuple[float, float], 
                                 point2: Tuple[float, float], 
                                 point3: Tuple[float, float]) -> float:
        """Calculate curvature at a specific point."""
        from utils.helpers import calculate_distance, calculate_bearing
        
        # Calculate distances
        d1 = calculate_distance(point1[0], point1[1], point2[0], point2[1])
        d2 = calculate_distance(point2[0], point2[1], point3[0], point3[1])
        
        if d1 == 0 or d2 == 0:
            return 0.0
        
        # Calculate bearings
        bearing1 = calculate_bearing(point1[0], point1[1], point2[0], point2[1])
        bearing2 = calculate_bearing(point2[0], point2[1], point3[0], point3[1])
        
        # Calculate turn angle
        turn_angle = abs(self._normalize_angle(bearing2 - bearing1))
        turn_angle_rad = math.radians(turn_angle)
        
        # Approximate curvature (1/radius)
        avg_distance = (d1 + d2) / 2
        if avg_distance > 0:
            curvature = turn_angle_rad / avg_distance
        else:
            curvature = 0.0
        
        return curvature
