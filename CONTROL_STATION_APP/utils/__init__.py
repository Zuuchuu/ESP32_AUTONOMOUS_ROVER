"""
Utilities module for ESP32 Rover Control Station.

This module contains utility functions, validation helpers, and
configuration management used throughout the application.
"""

from .helpers import (
    normalize_angle, calculate_distance, calculate_bearing,
    validate_gps_coordinate, format_duration, format_distance,
    format_speed, clamp, lerp, calculate_gps_offset, estimate_travel_time
)
from .config import ConfigManager

__all__ = [
    'normalize_angle', 'calculate_distance', 'calculate_bearing',
    'validate_gps_coordinate', 'format_duration', 'format_distance',
    'format_speed', 'clamp', 'lerp', 'calculate_gps_offset', 
    'estimate_travel_time', 'ConfigManager'
]
