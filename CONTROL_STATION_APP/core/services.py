"""
Business logic services for ESP32 Rover Control Station.

This module contains the main application service that coordinates
between GUI, network, and data layers. Provides high-level operations
for rover control, waypoint management, and telemetry processing.
"""

import logging
from typing import List, Optional, Tuple
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from .models import (AppState, ConnectionState, NavigationState, 
                    Waypoint, TelemetryData)


try:
    # Optional import for type hints; avoids hard dependency issues
    from utils.config import ConfigManager  # type: ignore
except Exception:  # pragma: no cover
    ConfigManager = None  # type: ignore


class ApplicationService(QObject):
    """
    Main application service that coordinates all business logic.
    
    Acts as the central controller between GUI, network, and data layers.
    Provides high-level operations and maintains application state.
    """
    
    # High-level signals for GUI coordination
    status_message = pyqtSignal(str)
    operation_completed = pyqtSignal(str, bool)  # operation, success
    
    def __init__(self, config_manager: Optional['ConfigManager'] = None):
        super().__init__()
        self.app_state = AppState()
        self.config_manager = config_manager
        self.network_client = None  # Will be injected by main application
        self.logger = self._setup_logging()
        
        # Apply configuration into application state if available
        self._apply_configuration()

        # Connection monitoring timer
        self.connection_monitor = QTimer()
        self.connection_monitor.timeout.connect(self._monitor_connection)
        self.connection_monitor.start(2000)  # Check every 2 seconds
        
        # Connect to app state signals
        self._connect_state_signals()

    def _apply_configuration(self):
        """Apply configuration values from ConfigManager into AppState."""
        try:
            if self.config_manager is None:
                return
            # Max waypoints
            max_wps = self.config_manager.get("map.max_waypoints", None)
            if isinstance(max_wps, int) and max_wps > 0:
                self.app_state.set_max_waypoints(max_wps)
            # Future: map defaults, telemetry intervals, etc.
        except Exception:
            # Non-fatal if configuration is unavailable
            pass
    
    def _setup_logging(self) -> logging.Logger:
        """Set up application logging."""
        logger = logging.getLogger('RoverControl')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _connect_state_signals(self):
        """Connect to application state signals."""
        self.app_state.connection_state_changed.connect(self._on_connection_state_changed)
        self.app_state.navigation_state_changed.connect(self._on_navigation_state_changed)
        self.app_state.error_occurred.connect(self._on_error_occurred)
    
    def set_network_client(self, client):
        """Inject network client dependency."""
        self.network_client = client
        if hasattr(client, 'telemetry_received'):
            client.telemetry_received.connect(self.process_telemetry)
        if hasattr(client, 'connection_lost'):
            client.connection_lost.connect(self._on_connection_lost)
    
    # Connection Management
    def connect_to_rover(self, ip: str, port: int = 80) -> bool:
        """
        Connect to ESP32 rover.
        
        Args:
            ip: Rover IP address
            port: TCP port (default 80)
            
        Returns:
            True if connection initiated successfully
        """
        if not self._validate_ip(ip):
            self.app_state.emit_error("Invalid IP address format")
            return False
        
        if self.app_state.rover_state.connection_state == ConnectionState.CONNECTED:
            self.logger.info("Already connected to rover")
            return True
        
        try:
            self.app_state.update_connection_state(ConnectionState.CONNECTING)
            self.app_state.set_connection_info(ip, port)
            self.status_message.emit(f"Connecting to rover at {ip}:{port}...")
            
            if self.network_client:
                success, message = self.network_client.connect(ip, port)
                if success:
                    self.app_state.update_connection_state(ConnectionState.CONNECTED)
                    self.status_message.emit("Successfully connected to rover")
                    self.operation_completed.emit("connect", True)
                    self.logger.info(f"Connected to rover at {ip}:{port}")
                    return True
                else:
                    self.app_state.update_connection_state(ConnectionState.ERROR, message)
                    self.operation_completed.emit("connect", False)
                    return False
            else:
                self.app_state.emit_error("Network client not available")
                return False
                
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            self.app_state.update_connection_state(ConnectionState.ERROR, error_msg)
            self.operation_completed.emit("connect", False)
            self.logger.error(error_msg)
            return False
    
    def disconnect_from_rover(self):
        """Disconnect from rover."""
        try:
            if self.network_client:
                self.network_client.disconnect()
            
            self.app_state.update_connection_state(ConnectionState.DISCONNECTED)
            self.app_state.update_navigation_state(NavigationState.STOPPED)
            self.status_message.emit("Disconnected from rover")
            self.operation_completed.emit("disconnect", True)
            self.logger.info("Disconnected from rover")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {str(e)}")
    
    # Waypoint Management
    def add_waypoint_from_map(self, map_data: dict) -> bool:
        """
        Add waypoint from map click data.
        
        Args:
            map_data: Dictionary with 'lat' and 'lng' keys
            
        Returns:
            True if waypoint added successfully
        """
        try:
            waypoint = Waypoint.from_map_format(map_data)
            if self.app_state.add_waypoint(waypoint):
                self.status_message.emit(f"Added waypoint {len(self.app_state.waypoints)}")
                self.logger.info(f"Added waypoint: {waypoint.latitude:.6f}, {waypoint.longitude:.6f}")
                return True
            else:
                self.app_state.emit_error(f"Maximum of {self.app_state.max_waypoints} waypoints allowed")
                return False
                
        except ValueError as e:
            self.app_state.emit_error(f"Invalid waypoint: {str(e)}")
            return False
    
    def add_waypoint_manual(self, latitude: float, longitude: float) -> bool:
        """
        Add waypoint from manual input.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            True if waypoint added successfully
        """
        try:
            waypoint = Waypoint(latitude, longitude)
            if self.app_state.add_waypoint(waypoint):
                self.status_message.emit(f"Added waypoint {len(self.app_state.waypoints)}")
                self.logger.info(f"Added manual waypoint: {latitude:.6f}, {longitude:.6f}")
                return True
            else:
                self.app_state.emit_error(f"Maximum of {self.app_state.max_waypoints} waypoints allowed")
                return False
                
        except ValueError as e:
            self.app_state.emit_error(f"Invalid coordinates: {str(e)}")
            return False
    
    def clear_waypoints(self):
        """Clear all waypoints."""
        self.app_state.clear_waypoints()
        self.status_message.emit("All waypoints cleared")
        self.logger.info("Cleared all waypoints")

    def remove_selected_waypoints(self, selected_rows):
        """Remove only selected waypoints by row indices."""
        try:
            if not selected_rows:
                return
            # Work on a single copy and remove from highest to lowest index
            wps = self.app_state.waypoints
            if not wps:
                return
            for row in sorted(selected_rows, reverse=True):
                if 0 <= row < len(wps):
                    del wps[row]
            # Set once (also renumbers IDs inside set_waypoints)
            self.app_state.set_waypoints(wps)
            self.status_message.emit(f"Removed {len(selected_rows)} waypoint(s)")
            self.logger.info(f"Removed waypoints at rows: {selected_rows}")
        except Exception as e:
            self.app_state.emit_error(f"Failed to remove selected waypoints: {e}")
    

    

    
    def set_rover_speed(self, speed: int) -> bool:
        """
        Set rover speed.
        
        Args:
            speed: Speed percentage (0-100)
            
        Returns:
            True if speed set successfully
        """
        self.logger.info(f"Speed change requested: {speed}%")
        
        if not 0 <= speed <= 100:
            self.app_state.emit_error("Speed must be between 0 and 100")
            return False
        
        if not self._check_connection():
            self.logger.warning("Speed change failed: Not connected to rover")
            return False
        
        try:
            if self.network_client:
                success, message = self.network_client.set_speed(speed)
                if success:
                    self.app_state.update_speed(speed)
                    self.logger.info(f"Successfully set rover speed to {speed}%")
                    self.status_message.emit(f"Speed set to {speed}%")
                    return True
                else:
                    self.app_state.emit_error(f"Failed to set speed: {message}")
                    return False
            else:
                self.app_state.emit_error("Network client not available")
                return False
                
        except Exception as e:
            error_msg = f"Error setting speed: {str(e)}"
            self.app_state.emit_error(error_msg)
            self.logger.error(error_msg)
            return False
    
    # Telemetry Processing
    def process_telemetry(self, raw_data: dict):
        """
        Process incoming telemetry data from ESP32.
        
        Args:
            raw_data: Raw telemetry dictionary from ESP32
        """
        try:
            telemetry = TelemetryData.from_esp32_data(raw_data)
            self.app_state.update_telemetry(telemetry)
            
            if telemetry.is_valid:
                self.logger.debug(f"Processed telemetry: pos=({telemetry.latitude:.6f}, {telemetry.longitude:.6f}), heading={telemetry.heading:.1f}°")
            else:
                self.logger.warning("Received invalid telemetry data")
                
        except Exception as e:
            self.logger.error(f"Error processing telemetry: {str(e)}")
    
    # Private helper methods
    def _check_connection(self) -> bool:
        """Check if rover is connected."""
        if self.app_state.rover_state.connection_state != ConnectionState.CONNECTED:
            self.app_state.emit_error("Not connected to rover")
            return False
        return True
    
    def _validate_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False
    
    def _monitor_connection(self):
        """Monitor connection status periodically."""
        if (self.app_state.rover_state.connection_state == ConnectionState.CONNECTED and
            self.network_client and not self.network_client.is_connected()):
            self.app_state.update_connection_state(ConnectionState.ERROR, "Connection lost")
            self.logger.warning("Connection to rover lost")
    
    # Signal handlers
    def _on_connection_state_changed(self, state: ConnectionState):
        """Handle connection state changes."""
        state_messages = {
            ConnectionState.DISCONNECTED: "Disconnected",
            ConnectionState.CONNECTING: "Connecting...",
            ConnectionState.CONNECTED: "Connected",
            ConnectionState.ERROR: "Connection Error"
        }
        self.logger.info(f"Connection state changed to: {state_messages.get(state, str(state))}")
    
    def _on_navigation_state_changed(self, state: NavigationState):
        """Handle navigation state changes."""
        state_messages = {
            NavigationState.STOPPED: "Navigation Stopped",
            NavigationState.RUNNING: "Navigation Running",
            NavigationState.PAUSED: "Navigation Paused",
            NavigationState.ERROR: "Navigation Error"
        }
        self.logger.info(f"Navigation state changed to: {state_messages.get(state, str(state))}")
    
    def _on_error_occurred(self, message: str):
        """Handle application errors."""
        self.logger.error(f"Application error: {message}")
    
    def _on_connection_lost(self, message: str):
        """Handle connection loss from network layer."""
        self.app_state.update_connection_state(ConnectionState.ERROR, message)
        self.app_state.update_navigation_state(NavigationState.STOPPED)
    
    # Public API for getting current state
    def get_connection_state(self) -> ConnectionState:
        """Get current connection state."""
        return self.app_state.rover_state.connection_state
    
    def get_navigation_state(self) -> NavigationState:
        """Get current navigation state."""
        return self.app_state.rover_state.navigation_state
    
    def get_waypoints(self) -> List[Waypoint]:
        """Get current waypoints."""
        return self.app_state.waypoints
    
    def get_current_telemetry(self) -> Optional[TelemetryData]:
        """Get latest telemetry data."""
        return self.app_state.rover_state.last_telemetry
    
    def get_rover_state(self):
        """Get complete rover state."""
        return self.app_state.rover_state
