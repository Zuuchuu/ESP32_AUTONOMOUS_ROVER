"""
Network communication module for ESP32 Rover Control Station.

This module handles all network communication with the ESP32 rover,
including TCP client functionality, protocol handling, and telemetry processing.
"""

from .client import RoverClient
from .telemetry import TelemetryProcessor

__all__ = ['RoverClient', 'TelemetryProcessor']
