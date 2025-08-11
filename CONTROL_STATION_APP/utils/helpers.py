"""
Utility helper functions for the Control Station App.

Contains common mathematical functions, data validation,
and formatting utilities used throughout the application.
"""

import math
from typing import Tuple


def normalize_angle(angle: float) -> float:
    """
    Normalize angle to -180 to 180 degree range.
    
    Args:
        angle: Angle in degrees
        
    Returns:
        Normalized angle in degrees (-180 to 180)
    """
    angle = angle % 360
    if angle > 180:
        angle -= 360
    elif angle <= -180:
        angle += 360
    return angle


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate great circle distance between two GPS coordinates using Haversine formula.
    
    Args:
        lat1, lng1: First coordinate in decimal degrees
        lat2, lng2: Second coordinate in decimal degrees
        
    Returns:
        Distance in meters
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2)
    
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in meters
    earth_radius = 6371000
    
    return earth_radius * c


def calculate_bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate bearing (heading) from first point to second point.
    
    Args:
        lat1, lng1: Starting coordinate in decimal degrees
        lat2, lng2: Ending coordinate in decimal degrees
        
    Returns:
        Bearing in degrees (0-360, where 0 is North)
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Calculate bearing
    dlng = lng2_rad - lng1_rad
    
    y = math.sin(dlng) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlng))
    
    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)
    
    # Normalize to 0-360 range
    return (bearing_deg + 360) % 360


def validate_gps_coordinate(latitude: float, longitude: float) -> bool:
    """
    Validate GPS coordinates are within valid ranges.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        True if coordinates are valid
    """
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "2h 30m 15s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.0f}s"


def format_distance(meters: float) -> str:
    """
    Format distance in meters to human-readable format.
    
    Args:
        meters: Distance in meters
        
    Returns:
        Formatted distance string (e.g., "1.2km" or "150m")
    """
    if meters < 1000:
        return f"{meters:.0f}m"
    else:
        kilometers = meters / 1000
        return f"{kilometers:.1f}km"


def format_speed(meters_per_second: float) -> str:
    """
    Format speed in m/s to human-readable format.
    
    Args:
        meters_per_second: Speed in meters per second
        
    Returns:
        Formatted speed string (e.g., "1.5 m/s" or "5.4 km/h")
    """
    kmh = meters_per_second * 3.6
    
    if meters_per_second < 1.0:
        return f"{meters_per_second:.2f} m/s"
    else:
        return f"{meters_per_second:.1f} m/s ({kmh:.1f} km/h)"


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamp value to specified range.
    
    Args:
        value: Value to clamp
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Clamped value
    """
    return max(min_value, min(value, max_value))


def lerp(start: float, end: float, t: float) -> float:
    """
    Linear interpolation between two values.
    
    Args:
        start: Starting value
        end: Ending value
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated value
    """
    return start + t * (end - start)


def calculate_gps_offset(latitude: float, longitude: float, 
                        distance_m: float, bearing_deg: float) -> Tuple[float, float]:
    """
    Calculate new GPS coordinate from starting point, distance, and bearing.
    
    Args:
        latitude: Starting latitude in decimal degrees
        longitude: Starting longitude in decimal degrees
        distance_m: Distance to travel in meters
        bearing_deg: Bearing in degrees (0-360, where 0 is North)
        
    Returns:
        Tuple of (new_latitude, new_longitude)
    """
    # Earth's radius in meters
    earth_radius = 6371000
    
    # Convert to radians
    lat_rad = math.radians(latitude)
    lng_rad = math.radians(longitude)
    bearing_rad = math.radians(bearing_deg)
    
    # Calculate new latitude
    new_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(distance_m / earth_radius) +
        math.cos(lat_rad) * math.sin(distance_m / earth_radius) * math.cos(bearing_rad)
    )
    
    # Calculate new longitude
    new_lng_rad = lng_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(distance_m / earth_radius) * math.cos(lat_rad),
        math.cos(distance_m / earth_radius) - math.sin(lat_rad) * math.sin(new_lat_rad)
    )
    
    # Convert back to degrees
    new_latitude = math.degrees(new_lat_rad)
    new_longitude = math.degrees(new_lng_rad)
    
    return new_latitude, new_longitude


def estimate_travel_time(distance_m: float, speed_mps: float, 
                        waypoint_count: int = 0) -> float:
    """
    Estimate travel time including stops and course corrections.
    
    Args:
        distance_m: Total distance in meters
        speed_mps: Average speed in meters per second
        waypoint_count: Number of waypoints (for stop time estimation)
        
    Returns:
        Estimated travel time in seconds
    """
    if speed_mps <= 0:
        return float('inf')
    
    # Base travel time
    travel_time = distance_m / speed_mps
    
    # Add time for waypoint stops (5 seconds per waypoint)
    stop_time = waypoint_count * 5
    
    # Add buffer for course corrections (15% of travel time)
    correction_buffer = travel_time * 0.15
    
    return travel_time + stop_time + correction_buffer