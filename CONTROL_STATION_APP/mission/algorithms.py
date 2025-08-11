"""
Core path planning algorithms for autonomous rover mission planning.

Implements A* pathfinding, TSP waypoint optimization, and supporting
algorithms for efficient and optimal route planning.
"""

import math
import heapq
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass
import logging

# Import utility functions for distance and bearing calculations
from utils.helpers import calculate_distance, calculate_bearing


@dataclass
class Node:
    """A* algorithm node for pathfinding."""
    position: Tuple[float, float]  # (lat, lng)
    g_cost: float = 0.0  # Cost from start
    h_cost: float = 0.0  # Heuristic cost to goal
    f_cost: float = 0.0  # Total cost (g + h)
    parent: Optional['Node'] = None
    
    def __post_init__(self):
        self.f_cost = self.g_cost + self.h_cost
    
    def __lt__(self, other):
        return self.f_cost < other.f_cost


class PathPlanningAlgorithms:
    """Core path planning algorithms for rover navigation."""
    
    def __init__(self):
        self.logger = logging.getLogger('PathPlanning')
        
    def a_star_pathfind(self, 
                       start: Tuple[float, float], 
                       goal: Tuple[float, float],
                       waypoints: List[Tuple[float, float]] = None,
                       grid_resolution: float = 0.0001) -> List[Tuple[float, float]]:
        """
        A* pathfinding algorithm for optimal route planning.
        
        Args:
            start: Starting position (lat, lng)
            goal: Goal position (lat, lng)
            waypoints: Optional intermediate waypoints to include
            grid_resolution: Grid resolution for pathfinding (degrees)
            
        Returns:
            List of coordinate points forming the optimal path
        """
        if waypoints:
            # Multi-waypoint pathfinding
            return self._multi_waypoint_a_star(start, goal, waypoints, grid_resolution)
        else:
            # Direct A* from start to goal
            return self._single_a_star(start, goal, grid_resolution)
    
    def _single_a_star(self, 
                      start: Tuple[float, float], 
                      goal: Tuple[float, float],
                      grid_resolution: float) -> List[Tuple[float, float]]:
        """Single-segment A* pathfinding."""
        open_set = []
        closed_set: Set[Tuple[float, float]] = set()
        
        start_node = Node(start)
        start_node.g_cost = 0
        start_node.h_cost = self._heuristic_cost(start, goal)
        start_node.f_cost = start_node.g_cost + start_node.h_cost
        
        heapq.heappush(open_set, start_node)
        
        while open_set:
            current = heapq.heappop(open_set)
            
            if self._is_goal_reached(current.position, goal, grid_resolution * 2):
                # Reconstruct path
                path = []
                while current:
                    path.append(current.position)
                    current = current.parent
                return path[::-1]  # Reverse to get start-to-goal order
            
            closed_set.add(current.position)
            
            # Generate neighbors (simplified grid-based approach)
            neighbors = self._get_neighbors(current.position, grid_resolution)
            
            for neighbor_pos in neighbors:
                if neighbor_pos in closed_set:
                    continue
                
                neighbor = Node(neighbor_pos)
                neighbor.g_cost = current.g_cost + self._heuristic_cost(current.position, neighbor_pos)
                neighbor.h_cost = self._heuristic_cost(neighbor_pos, goal)
                neighbor.f_cost = neighbor.g_cost + neighbor.h_cost
                neighbor.parent = current
                
                # Check if this path to neighbor is better
                existing_in_open = None
                for node in open_set:
                    if node.position == neighbor_pos:
                        existing_in_open = node
                        break
                
                if existing_in_open is None or neighbor.g_cost < existing_in_open.g_cost:
                    heapq.heappush(open_set, neighbor)
        
        # No path found, return direct line
        self.logger.warning("A* pathfinding failed, returning direct path")
        return [start, goal]
    
    def _multi_waypoint_a_star(self, 
                              start: Tuple[float, float], 
                              goal: Tuple[float, float],
                              waypoints: List[Tuple[float, float]],
                              grid_resolution: float) -> List[Tuple[float, float]]:
        """Multi-waypoint A* pathfinding by connecting segments."""
        full_path = []
        current_start = start
        
        # Plan path through each waypoint
        for waypoint in waypoints:
            segment_path = self._single_a_star(current_start, waypoint, grid_resolution)
            if full_path:
                # Remove duplicate point at segment connection
                segment_path = segment_path[1:]
            full_path.extend(segment_path)
            current_start = waypoint
        
        # Final segment to goal
        if current_start != goal:
            final_segment = self._single_a_star(current_start, goal, grid_resolution)
            if full_path:
                final_segment = final_segment[1:]
            full_path.extend(final_segment)
        
        return full_path
    
    def _heuristic_cost(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate heuristic cost (straight-line distance) between two positions."""
        return calculate_distance(pos1[0], pos1[1], pos2[0], pos2[1])
    
    def _is_goal_reached(self, current: Tuple[float, float], goal: Tuple[float, float], tolerance: float) -> bool:
        """Check if current position is close enough to goal."""
        distance = calculate_distance(current[0], current[1], goal[0], goal[1])
        return distance <= tolerance
    
    def _get_neighbors(self, position: Tuple[float, float], resolution: float) -> List[Tuple[float, float]]:
        """Generate neighbor positions for grid-based pathfinding."""
        lat, lng = position
        neighbors = []
        
        # 8-directional movement
        for dlat in [-resolution, 0, resolution]:
            for dlng in [-resolution, 0, resolution]:
                if dlat == 0 and dlng == 0:
                    continue
                neighbors.append((lat + dlat, lng + dlng))
        
        return neighbors


class WaypointOptimizer:
    """Waypoint ordering optimization using Traveling Salesman Problem algorithms."""
    
    def __init__(self):
        self.logger = logging.getLogger('WaypointOptimizer')
    
    def optimize_waypoint_sequence(self, 
                                 waypoints: List[Tuple[float, float]], 
                                 start_pos: Tuple[float, float],
                                 return_to_start: bool = False) -> List[Tuple[float, float]]:
        """
        Optimize waypoint visitation order using nearest neighbor heuristic.
        
        For small numbers of waypoints (≤10), this provides good results quickly.
        For larger sets, could be enhanced with 2-opt or genetic algorithms.
        
        Args:
            waypoints: List of waypoint coordinates
            start_pos: Starting position
            return_to_start: Whether to return to starting position
            
        Returns:
            Optimized sequence of waypoints
        """
        if len(waypoints) <= 1:
            return waypoints
        
        # Use nearest neighbor heuristic for TSP
        return self._nearest_neighbor_tsp(waypoints, start_pos, return_to_start)
    
    def _nearest_neighbor_tsp(self, 
                             waypoints: List[Tuple[float, float]], 
                             start_pos: Tuple[float, float],
                             return_to_start: bool) -> List[Tuple[float, float]]:
        """Nearest neighbor algorithm for TSP approximation."""
        unvisited = waypoints.copy()
        visited = []
        current_pos = start_pos
        total_distance = 0.0
        
        while unvisited:
            # Find nearest unvisited waypoint
            nearest_idx = 0
            nearest_distance = float('inf')
            
            for i, waypoint in enumerate(unvisited):
                distance = calculate_distance(current_pos[0], current_pos[1], 
                                            waypoint[0], waypoint[1])
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_idx = i
            
            # Move to nearest waypoint
            nearest_waypoint = unvisited.pop(nearest_idx)
            visited.append(nearest_waypoint)
            total_distance += nearest_distance
            current_pos = nearest_waypoint
        
        # Optional return to start
        if return_to_start and visited:
            return_distance = calculate_distance(current_pos[0], current_pos[1], 
                                               start_pos[0], start_pos[1])
            total_distance += return_distance
        
        self.logger.info(f"Optimized waypoint sequence: {len(visited)} waypoints, "
                        f"total distance: {total_distance:.2f}m")
        
        return visited
    
    def calculate_total_distance(self, 
                               waypoint_sequence: List[Tuple[float, float]], 
                               start_pos: Tuple[float, float] = None) -> float:
        """Calculate total distance for a waypoint sequence."""
        if not waypoint_sequence:
            return 0.0
        
        total_distance = 0.0
        current_pos = start_pos or waypoint_sequence[0]
        
        for waypoint in waypoint_sequence:
            if current_pos != waypoint:
                distance = calculate_distance(current_pos[0], current_pos[1], 
                                            waypoint[0], waypoint[1])
                total_distance += distance
                current_pos = waypoint
        
        return total_distance
    
    def estimate_mission_time(self, 
                            waypoint_sequence: List[Tuple[float, float]], 
                            start_pos: Tuple[float, float],
                            average_speed_mps: float = 1.0) -> float:
        """
        Estimate mission completion time.
        
        Args:
            waypoint_sequence: Optimized waypoint sequence
            start_pos: Starting position
            average_speed_mps: Average rover speed in meters per second
            
        Returns:
            Estimated mission time in seconds
        """
        total_distance = self.calculate_total_distance(waypoint_sequence, start_pos)
        
        if average_speed_mps <= 0:
            return float('inf')
        
        # Add buffer time for waypoint stops and path corrections
        mission_time = total_distance / average_speed_mps
        buffer_factor = 1.2  # 20% buffer for stops and corrections
        
        return mission_time * buffer_factor


class PathValidator:
    """Validates path segments and waypoint sequences for feasibility."""
    
    def __init__(self):
        self.logger = logging.getLogger('PathValidator')
    
    def validate_waypoint_sequence(self, waypoints: List[Tuple[float, float]]) -> Tuple[bool, str]:
        """
        Validate a sequence of waypoints for basic feasibility.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not waypoints:
            return False, "No waypoints provided"
        
        if len(waypoints) > 50:  # Reasonable limit
            return False, f"Too many waypoints: {len(waypoints)} (max: 50)"
        
        # Check for duplicate waypoints
        unique_waypoints = set(waypoints)
        if len(unique_waypoints) != len(waypoints):
            return False, "Duplicate waypoints detected"
        
        # Check coordinate validity
        for i, (lat, lng) in enumerate(waypoints):
            if not (-90 <= lat <= 90):
                return False, f"Invalid latitude at waypoint {i+1}: {lat}"
            if not (-180 <= lng <= 180):
                return False, f"Invalid longitude at waypoint {i+1}: {lng}"
        
        # Check for unreasonably long segments
        max_segment_distance = 10000  # 10km in meters
        for i in range(len(waypoints) - 1):
            current = waypoints[i]
            next_wp = waypoints[i + 1]
            distance = calculate_distance(current[0], current[1], next_wp[0], next_wp[1])
            
            if distance > max_segment_distance:
                return False, f"Segment {i+1}-{i+2} too long: {distance:.0f}m (max: {max_segment_distance}m)"
        
        return True, "Waypoint sequence is valid"
    
    def estimate_path_difficulty(self, waypoints: List[Tuple[float, float]]) -> Dict[str, float]:
        """
        Estimate path difficulty metrics.
        
        Returns:
            Dictionary with difficulty metrics
        """
        if not waypoints:
            return {"difficulty": 0.0, "turns": 0, "distance": 0.0}
        
        total_distance = 0.0
        total_turn_angle = 0.0
        turn_count = 0
        
        for i in range(len(waypoints) - 1):
            current = waypoints[i]
            next_wp = waypoints[i + 1]
            
            # Calculate segment distance
            segment_distance = calculate_distance(current[0], current[1], next_wp[0], next_wp[1])
            total_distance += segment_distance
            
            # Calculate turn angle for next segment
            if i < len(waypoints) - 2:
                next_next = waypoints[i + 2]
                
                bearing1 = calculate_bearing(current[0], current[1], next_wp[0], next_wp[1])
                bearing2 = calculate_bearing(next_wp[0], next_wp[1], next_next[0], next_next[1])
                
                turn_angle = abs(bearing2 - bearing1)
                if turn_angle > 180:
                    turn_angle = 360 - turn_angle
                
                total_turn_angle += turn_angle
                if turn_angle > 15:  # Significant turn threshold
                    turn_count += 1
        
        # Calculate difficulty score (0-10 scale)
        distance_factor = min(total_distance / 1000, 5)  # Normalize to 5km max
        turn_factor = min(total_turn_angle / 360, 3)     # Normalize to full circle max
        complexity_factor = min(len(waypoints) / 10, 2) # Normalize to 10 waypoints max
        
        difficulty = distance_factor + turn_factor + complexity_factor
        
        return {
            "difficulty": min(difficulty, 10.0),
            "turns": turn_count,
            "distance": total_distance,
            "avg_turn_angle": total_turn_angle / max(len(waypoints) - 2, 1)
        }
