"""
Telemetry processor for ESP32 Rover communication.

This module handles the continuous reception and processing of telemetry
data from the ESP32 rover in a separate thread to keep the GUI responsive.
Compatible with ESP32 telemetry format.
"""

import socket
import json
import time
import logging
from typing import Optional, Dict, Any
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker


class TelemetryProcessor(QThread):
    """
    Background thread for processing telemetry data from ESP32 rover.
    
    Receives and parses JSON telemetry data continuously while maintaining
    GUI responsiveness. Compatible with ESP32 telemetry format:
    
    {
        "lat": float, "lon": float, "heading": float,
        "imu_data": {"accel": [x,y,z], "gyro": [x,y,z], "mag": [x,y,z]},
        "temperature": float, "wifi_strength": int
    }
    """
    
    # Signals
    telemetry_received = pyqtSignal(dict)  # Parsed telemetry data
    connection_lost = pyqtSignal(str)      # Connection lost with reason
    parsing_error = pyqtSignal(str)        # JSON parsing error
    
    def __init__(self, sock: socket.socket):
        super().__init__()
        self.sock = sock
        self.running = True
        self.mutex = QMutex()
        self.logger = self._setup_logging()
        
        # Telemetry processing parameters
        self.buffer_size = 4096
        self.timeout_seconds = 1.0
        self.max_buffer_size = 65536  # Prevent memory issues
        
        # Statistics
        self.messages_received = 0
        self.parsing_errors = 0
        self.last_message_time = 0
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for telemetry processing."""
        logger = logging.getLogger('TelemetryProcessor')
        logger.setLevel(logging.INFO)
        return logger
    
    def run(self):
        """Main thread loop for receiving and processing telemetry."""
        buffer = ""
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        self.logger.info("Telemetry processor started")
        
        while self.running:
            try:
                # Set socket timeout for periodic running check
                self.sock.settimeout(self.timeout_seconds)
                
                # Receive data from rover
                data = self.sock.recv(self.buffer_size)
                
                if not data:
                    self.connection_lost.emit("Connection closed by rover")
                    break
                
                # Reset consecutive error counter on successful receive
                consecutive_errors = 0
                
                # Decode and add to buffer
                try:
                    decoded_data = data.decode('utf-8')
                    buffer += decoded_data
                except UnicodeDecodeError as e:
                    self.logger.warning(f"Unicode decode error: {e}")
                    continue
                
                # Prevent buffer from growing too large
                if len(buffer) > self.max_buffer_size:
                    self.logger.warning("Buffer overflow, clearing buffer")
                    buffer = buffer[-self.buffer_size:]  # Keep last portion
                
                # Process complete JSON messages in buffer
                buffer = self._process_buffer(buffer)
                
            except socket.timeout:
                # Timeout is normal, continue to check running flag
                continue
            except ConnectionResetError:
                self.connection_lost.emit("Connection reset by rover")
                break
            except ConnectionAbortedError:
                self.connection_lost.emit("Connection aborted")
                break
            except OSError as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    self.connection_lost.emit(f"Multiple network errors: {str(e)}")
                    break
                else:
                    self.logger.warning(f"Network error ({consecutive_errors}/{max_consecutive_errors}): {e}")
                    time.sleep(0.1)  # Brief pause before retry
            except Exception as e:
                self.logger.error(f"Unexpected error in telemetry processing: {str(e)}")
                self.connection_lost.emit(f"Telemetry processing error: {str(e)}")
                break
        
        self.logger.info(f"Telemetry processor stopped. Messages processed: {self.messages_received}, Errors: {self.parsing_errors}")
    
    def _process_buffer(self, buffer: str) -> str:
        """
        Process buffer for complete JSON messages.
        
        Args:
            buffer: Current buffer content
            
        Returns:
            Remaining buffer content after processing
        """
        # Split buffer by newlines (ESP32 sends line-delimited JSON)
        lines = buffer.split('\n')
        
        # Process all complete lines (except the last one which might be incomplete)
        for line in lines[:-1]:
            line = line.strip()
            if line:
                self._process_json_line(line)
        
        # Return the last line as remaining buffer (might be incomplete)
        return lines[-1] if lines else ""
    
    def _process_json_line(self, line: str):
        """
        Process a single JSON line from ESP32.
        
        Args:
            line: JSON string to process
        """
        try:
            # Parse JSON
            telemetry = json.loads(line)
            
            # Validate basic structure for ESP32 compatibility
            if self._validate_telemetry_structure(telemetry):
                self.messages_received += 1
                self.last_message_time = time.time()
                
                # Emit the telemetry data
                self.telemetry_received.emit(telemetry)
                
                self.logger.debug(f"Processed telemetry: lat={telemetry.get('lat', 'N/A')}, lon={telemetry.get('lon', 'N/A')}")
            else:
                self.parsing_errors += 1
                self.logger.warning(f"Invalid telemetry structure: {line[:100]}...")
                self.parsing_error.emit("Invalid telemetry data structure")
                
        except json.JSONDecodeError as e:
            self.parsing_errors += 1
            self.logger.warning(f"JSON decode error: {e}, data: {line[:100]}...")
            self.parsing_error.emit(f"JSON parsing error: {str(e)}")
        except Exception as e:
            self.parsing_errors += 1
            self.logger.error(f"Error processing telemetry line: {str(e)}")
            self.parsing_error.emit(f"Processing error: {str(e)}")
    
    def _validate_telemetry_structure(self, data: Dict[str, Any]) -> bool:
        """
        Validate telemetry data structure matches ESP32 format.
        
        Expected ESP32 format:
        {
            "lat": float, "lon": float, "heading": float,
            "imu_data": {"accel": [x,y,z], "gyro": [x,y,z], "mag": [x,y,z]},
            "temperature": float, "wifi_strength": int
        }
        
        Args:
            data: Parsed JSON data
            
        Returns:
            True if structure is valid
        """
        try:
            # Check required top-level fields
            required_fields = ['lat', 'lon', 'heading', 'temperature', 'wifi_strength']
            for field in required_fields:
                if field not in data:
                    return False
            
            # Check numeric types
            if not isinstance(data['lat'], (int, float)):
                return False
            if not isinstance(data['lon'], (int, float)):
                return False
            if not isinstance(data['heading'], (int, float)):
                return False
            if not isinstance(data['temperature'], (int, float)):
                return False
            if not isinstance(data['wifi_strength'], (int, float)):
                return False
            
            # Check IMU data structure if present
            if 'imu_data' in data:
                imu = data['imu_data']
                if isinstance(imu, dict):
                    for sensor in ['accel', 'gyro', 'mag']:
                        if sensor in imu:
                            sensor_data = imu[sensor]
                            if not (isinstance(sensor_data, list) and len(sensor_data) == 3):
                                return False
                            for value in sensor_data:
                                if not isinstance(value, (int, float)):
                                    return False
            
            return True
            
        except (KeyError, TypeError, ValueError):
            return False
    
    def stop(self):
        """Stop the telemetry processor gracefully."""
        with QMutexLocker(self.mutex):
            self.running = False
            self.logger.info("Telemetry processor stop requested")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get telemetry processing statistics."""
        return {
            'messages_received': self.messages_received,
            'parsing_errors': self.parsing_errors,
            'last_message_time': self.last_message_time,
            'error_rate': self.parsing_errors / max(1, self.messages_received) * 100
        }
