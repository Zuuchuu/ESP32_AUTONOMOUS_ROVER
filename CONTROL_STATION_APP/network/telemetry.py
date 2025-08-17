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
    GUI responsiveness. Compatible with both legacy and BNO055 ESP32 formats:
    
    Legacy format:
    {
        "lat": float, "lon": float, "heading": float,
        "imu_data": {"accel": [x,y,z], "gyro": [x,y,z], "mag": [x,y,z]},
        "temperature": float, "wifi_strength": int
    }
    
    BNO055 Enhanced format:
    {
        "lat": float, "lon": float, "heading": float,
        "imu_data": {
            "roll": float, "pitch": float,
            "quaternion": [w, x, y, z],
            "accel": [x,y,z], "gyro": [x,y,z], "mag": [x,y,z],
            "linear_accel": [x,y,z], "gravity": [x,y,z],
            "calibration": {"sys": 0-3, "gyro": 0-3, "accel": 0-3, "mag": 0-3},
            "temperature": float
        },
        "wifi_strength": int
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
            
            # Check if this is a command response (not actual telemetry)
            if self._is_command_response(telemetry):
                # Log command responses but don't treat as telemetry
                self._log_command_response(telemetry)
                return
            
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
    
    def _is_command_response(self, data: Dict[str, Any]) -> bool:
        """
        Check if the JSON data is a command response rather than telemetry data.
        
        Command responses have this structure:
        {"status": "success|error", "message": "..."}
        
        Args:
            data: Parsed JSON data
            
        Returns:
            True if this is a command response
        """
        try:
            # Command responses have status and message fields
            if 'status' in data and 'message' in data:
                # Check if it's missing telemetry-specific fields
                telemetry_fields = ['lat', 'lon', 'heading', 'wifi_strength']
                has_telemetry_fields = any(field in data for field in telemetry_fields)
                
                # If it has status/message but no telemetry fields, it's a command response
                if not has_telemetry_fields:
                    return True
                
                # Additional check: if status is success/error and message contains command-related text
                status = data.get('status', '').lower()
                message = data.get('message', '').lower()
                
                if status in ['success', 'error'] and any(keyword in message for keyword in [
                    'manual', 'command', 'enabled', 'disabled', 'executed', 'started', 'stopped'
                ]):
                    return True
                
                # Also catch connection messages like "Rover ready"
                if status == 'connected' or 'ready' in message:
                    return True
            
            return False
            
        except (KeyError, TypeError, ValueError):
            return False
    
    def _log_command_response(self, data: Dict[str, Any]):
        """
        Log command responses in a clean, informative way.
        
        Args:
            data: Command response data
        """
        try:
            status = data.get('status', 'unknown')
            message = data.get('message', 'No message')
            
            # Use appropriate log level based on status
            if status == 'success':
                self.logger.info(f"Command successful: {message}")
            elif status == 'error':
                self.logger.warning(f"Command failed: {message}")
            else:
                self.logger.info(f"Command response ({status}): {message}")
                
        except (KeyError, TypeError, ValueError) as e:
            self.logger.debug(f"Error logging command response: {str(e)}")
    
    def _validate_telemetry_structure(self, data: Dict[str, Any]) -> bool:
        """
        Validate telemetry data structure matches ESP32 format (legacy or BNO055).
        
        Supports both legacy and BNO055 enhanced formats.
        
        Args:
            data: Parsed JSON data
            
        Returns:
            True if structure is valid
        """
        try:
            # Check required top-level fields
            required_fields = ['lat', 'lon', 'heading', 'wifi_strength']
            for field in required_fields:
                if field not in data:
                    self.logger.debug(f"Missing required field: {field}")
                    return False
            
            # Check numeric types for required fields
            numeric_fields = ['lat', 'lon', 'heading', 'wifi_strength']
            for field in numeric_fields:
                if not isinstance(data[field], (int, float)):
                    self.logger.debug(f"Invalid type for {field}: {type(data[field])}")
                    return False
            
            # Temperature can be at top level or in imu_data (backward compatibility)
            has_temperature = ('temperature' in data and isinstance(data['temperature'], (int, float)))
            
            # Validate IMU data structure if present
            if 'imu_data' in data:
                imu = data['imu_data']
                if not isinstance(imu, dict):
                    self.logger.debug("IMU data is not a dictionary")
                    return False
                
                # Check for BNO055 enhanced fields
                has_bno055 = any(key in imu for key in ['roll', 'pitch', 'quaternion', 'calibration'])
                
                if has_bno055:
                    # Validate BNO055 enhanced structure
                    if not self._validate_bno055_imu_data(imu):
                        return False
                    
                    # Temperature should be in imu_data for BNO055
                    if 'temperature' in imu and not isinstance(imu['temperature'], (int, float)):
                        self.logger.debug("Invalid temperature type in IMU data")
                        return False
                    has_temperature = has_temperature or 'temperature' in imu
                else:
                    # Validate legacy IMU structure
                    if not self._validate_legacy_imu_data(imu):
                        return False
            
            # Ensure temperature is present somewhere
            if not has_temperature:
                self.logger.debug("Temperature not found in telemetry data")
                return False
            
            return True
            
        except (KeyError, TypeError, ValueError) as e:
            self.logger.debug(f"Validation error: {str(e)}")
            return False
    
    def _validate_legacy_imu_data(self, imu: Dict[str, Any]) -> bool:
        """Validate legacy IMU data format."""
        try:
            for sensor in ['accel', 'gyro', 'mag']:
                if sensor in imu:
                    sensor_data = imu[sensor]
                    if not (isinstance(sensor_data, list) and len(sensor_data) == 3):
                        self.logger.debug(f"Invalid {sensor} data structure")
                        return False
                    for value in sensor_data:
                        if not isinstance(value, (int, float)):
                            self.logger.debug(f"Invalid {sensor} value type: {type(value)}")
                            return False
            return True
        except (KeyError, TypeError, ValueError) as e:
            self.logger.debug(f"Legacy IMU validation error: {str(e)}")
            return False
    
    def _validate_bno055_imu_data(self, imu: Dict[str, Any]) -> bool:
        """Validate BNO055 enhanced IMU data format."""
        try:
            # Validate orientation fields
            orientation_fields = ['roll', 'pitch']
            for field in orientation_fields:
                if field in imu and not isinstance(imu[field], (int, float)):
                    self.logger.debug(f"Invalid {field} type: {type(imu[field])}")
                    return False
            
            # Validate quaternion if present
            if 'quaternion' in imu:
                quat = imu['quaternion']
                if not (isinstance(quat, list) and len(quat) == 4):
                    self.logger.debug("Invalid quaternion structure")
                    return False
                for value in quat:
                    if not isinstance(value, (int, float)):
                        self.logger.debug(f"Invalid quaternion value type: {type(value)}")
                        return False
            
            # Validate enhanced sensor arrays
            enhanced_arrays = ['linear_accel', 'gravity']
            for field in enhanced_arrays:
                if field in imu:
                    array_data = imu[field]
                    if not (isinstance(array_data, list) and len(array_data) == 3):
                        self.logger.debug(f"Invalid {field} structure")
                        return False
                    for value in array_data:
                        if not isinstance(value, (int, float)):
                            self.logger.debug(f"Invalid {field} value type: {type(value)}")
                            return False
            
            # Validate calibration status
            if 'calibration' in imu:
                cal = imu['calibration']
                if not isinstance(cal, dict):
                    self.logger.debug("Invalid calibration structure")
                    return False
                
                cal_fields = ['sys', 'gyro', 'accel', 'mag']
                for field in cal_fields:
                    if field in cal:
                        value = cal[field]
                        if not (isinstance(value, int) and 0 <= value <= 3):
                            self.logger.debug(f"Invalid calibration {field}: {value}")
                            return False
            
            # Still validate legacy sensor arrays for backward compatibility
            return self._validate_legacy_imu_data(imu)
            
        except (KeyError, TypeError, ValueError) as e:
            self.logger.debug(f"BNO055 IMU validation error: {str(e)}")
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
