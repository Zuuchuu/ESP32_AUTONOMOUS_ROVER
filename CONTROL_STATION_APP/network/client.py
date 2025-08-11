"""
TCP client for ESP32 Rover communication.

This module implements the TCP client that connects to the ESP32 rover,
sends commands and waypoints, and manages the connection lifecycle.
Fully compatible with ESP32 rover communication protocol.
"""

import socket
import json
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QMutex, QMutexLocker

from .telemetry import TelemetryProcessor


class RoverClient(QObject):
    """
    TCP client for communicating with ESP32 rover.
    
    Handles connection management, command sending, and telemetry reception.
    Compatible with ESP32 rover protocol: JSON over TCP on port 80.
    """
    
    # Signals
    telemetry_received = pyqtSignal(dict)  # Raw telemetry data from ESP32
    connection_lost = pyqtSignal(str)      # Connection lost with reason
    connection_status = pyqtSignal(bool)   # Connection status changed
    
    def __init__(self):
        super().__init__()
        self.sock: Optional[socket.socket] = None
        self.connected = False
        self.connection_mutex = QMutex()
        self.telemetry_processor: Optional[TelemetryProcessor] = None
        self.logger = self._setup_logging()
        
        # Connection parameters
        self.current_ip = ""
        self.current_port = 80
        self.connection_timeout = 5.0
        self.send_timeout = 2.0
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for network operations."""
        logger = logging.getLogger('RoverClient')
        logger.setLevel(logging.INFO)
        return logger
    
    def connect(self, ip_address: str, port: int = 80) -> Tuple[bool, str]:
        """
        Connect to ESP32 rover.
        
        Args:
            ip_address: Rover IP address
            port: TCP port (default 80 for ESP32)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        with QMutexLocker(self.connection_mutex):
            try:
                # Close existing connection if any
                self._close_socket()
                
                # Validate IP address
                if not self._validate_ip(ip_address):
                    return False, "Invalid IP address format"
                
                self.logger.info(f"Attempting to connect to {ip_address}:{port}")
                
                # Create socket with timeout
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(self.connection_timeout)
                
                # Connect to rover
                self.sock.connect((ip_address, port))
                
                # Set socket to non-blocking for telemetry reception
                self.sock.settimeout(self.send_timeout)
                
                # Start telemetry processor
                self.telemetry_processor = TelemetryProcessor(self.sock)
                self.telemetry_processor.telemetry_received.connect(self.telemetry_received.emit)
                self.telemetry_processor.connection_lost.connect(self._on_telemetry_connection_lost)
                self.telemetry_processor.start()
                
                # Update state
                self.connected = True
                self.current_ip = ip_address
                self.current_port = port
                
                self.connection_status.emit(True)
                self.logger.info(f"Successfully connected to rover at {ip_address}:{port}")
                
                return True, f"Connected to rover at {ip_address}:{port}"
                
            except socket.timeout:
                self._cleanup_connection()
                return False, "Connection timeout - rover not responding"
            except ConnectionRefusedError:
                self._cleanup_connection()
                return False, "Connection refused - check if rover is running"
            except socket.gaierror:
                self._cleanup_connection()
                return False, "Invalid IP address or network error"
            except OSError as e:
                self._cleanup_connection()
                return False, f"Network error: {str(e)}"
            except Exception as e:
                self._cleanup_connection()
                return False, f"Unexpected error: {str(e)}"
    
    def disconnect(self):
        """Disconnect from rover and clean up resources."""
        with QMutexLocker(self.connection_mutex):
            self._cleanup_connection()
            self.logger.info("Disconnected from rover")
    
    def _cleanup_connection(self):
        """Clean up connection resources."""
        self.connected = False
        
        # Stop telemetry processor
        if self.telemetry_processor:
            self.telemetry_processor.stop()
            self.telemetry_processor.wait(3000)  # Wait up to 3 seconds
            if self.telemetry_processor.isRunning():
                self.telemetry_processor.terminate()
            self.telemetry_processor = None
        
        # Close socket
        self._close_socket()
        
        self.connection_status.emit(False)
    
    def _close_socket(self):
        """Close the socket connection."""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
    
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
    
    def _on_telemetry_connection_lost(self, reason: str):
        """Handle connection loss detected by telemetry processor."""
        with QMutexLocker(self.connection_mutex):
            if self.connected:
                self.connected = False
                self._cleanup_connection()
                self.connection_lost.emit(reason)
    
    def send_command(self, command: str, **kwargs) -> Tuple[bool, str]:
        """
        Send command to rover.
        
        ESP32 rover expects: {"command": "start|stop|set_speed", "speed": int}
        
        Args:
            command: Command string
            **kwargs: Additional parameters
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_connected():
            return False, "Not connected to rover"
        
        try:
            # Build command data compatible with ESP32
            data = {"command": command}
            data.update(kwargs)
            
            # Convert to JSON with newline (ESP32 expects line-delimited JSON)
            json_data = json.dumps(data) + '\n'
            
            with QMutexLocker(self.connection_mutex):
                if self.sock:
                    self.sock.sendall(json_data.encode('utf-8'))
                    self.logger.debug(f"Sent command: {data}")
                    return True, f"Command '{command}' sent successfully"
                else:
                    return False, "Socket not available"
                    
        except socket.timeout:
            return False, "Send timeout - rover not responding"
        except ConnectionResetError:
            self._on_telemetry_connection_lost("Connection reset by rover")
            return False, "Connection lost during send"
        except Exception as e:
            self.logger.error(f"Error sending command: {str(e)}")
            return False, f"Send error: {str(e)}"
    

    

    
    def set_speed(self, speed: int) -> Tuple[bool, str]:
        """
        Set rover speed.
        
        Args:
            speed: Speed percentage (0-100)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not 0 <= speed <= 100:
            return False, "Speed must be between 0 and 100"
        
        return self.send_command("set_speed", speed=speed)
    
    def is_connected(self) -> bool:
        """Check if connected to rover."""
        return self.connected and self.sock is not None
    
    def get_connection_info(self) -> Tuple[str, int]:
        """Get current connection information."""
        return self.current_ip, self.current_port
    
    def get_telemetry_processor(self) -> Optional[TelemetryProcessor]:
        """Get telemetry processor for direct access if needed."""
        return self.telemetry_processor
    
    def send_mission_plan(self, mission_plan_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Send complete mission plan to the rover."""
        return self._send_command(mission_plan_data)
    
    def pause_mission(self) -> Tuple[bool, str]:
        """Send pause mission command to the rover."""
        command = {"command": "pause_mission"}
        return self._send_command(command)
    
    def abort_mission(self) -> Tuple[bool, str]:
        """Send abort mission command to the rover."""
        command = {"command": "abort_mission"}
        return self._send_command(command)
    
    def resume_mission(self) -> Tuple[bool, str]:
        """Send resume mission command to the rover."""
        command = {"command": "resume_mission"}
        return self._send_command(command)
