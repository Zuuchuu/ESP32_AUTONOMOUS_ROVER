"""
GUI module for ESP32 Rover Control Station.

This module contains the user interface layer including the main window,
modular panels, dialogs, and styling components.
"""

from .main_window import MainWindow
from .panels import (
    ConnectionPanel, WaypointPanel, 
    TelemetryPanel, MapWidget
)
from .styles import StyleManager

__all__ = [
    'MainWindow', 'ConnectionPanel', 'WaypointPanel', 
    'TelemetryPanel', 'MapWidget', 'StyleManager'
]
