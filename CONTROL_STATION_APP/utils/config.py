"""
Configuration management for ESP32 Rover Control Station.

This module handles loading, saving, and managing application configuration
settings including connection preferences, UI state, and user preferences.
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal


class ConfigManager(QObject):
    """
    Manages application configuration with file persistence.
    
    Handles loading and saving of settings to JSON file, with sensible
    defaults and automatic migration of configuration format changes.
    """
    
    # Signals
    config_changed = pyqtSignal(str, object)  # key, value
    config_loaded = pyqtSignal()
    config_saved = pyqtSignal()
    
    def __init__(self, config_file: str = "config.json"):
        super().__init__()
        self.config_file = config_file
        self.config_path = os.path.join(os.path.dirname(__file__), "..", config_file)
        self.logger = self._setup_logging()
        self._config: Dict[str, Any] = {}
        self._defaults = self._get_default_config()
        
        # Load configuration on initialization
        self.load_config()
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for configuration operations."""
        logger = logging.getLogger('ConfigManager')
        logger.setLevel(logging.INFO)
        return logger
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            # Connection settings
            "connection": {
                "default_ip": "192.168.1.100",
                "default_port": 80,
                "timeout": 5,
                "reconnect_attempts": 3,
                "remember_last_ip": True,
                "last_connected_ip": ""
            },
            
            # Map settings
            "map": {
                "default_center_lat": 37.7749,
                "default_center_lng": -122.4194,
                "default_zoom": 13,
                "max_waypoints": 10,
                "auto_center_on_rover": False,
                "show_path_lines": True
            },
            
            # Telemetry settings
            "telemetry": {
                "update_interval_ms": 1000,
                "timeout_seconds": 5,
                "log_to_file": False,
                "max_log_size_mb": 10
            },
            
            # GUI settings
            "gui": {
                "window_width": 1400,
                "window_height": 900,
                "window_x": 100,
                "window_y": 100,
                "remember_window_state": True,
                "theme": "default",
                "splitter_position": 70,  # Percentage for map panel
                "show_status_bar": True
            },
            
            # Application settings
            "application": {
                "log_level": "INFO",
                "check_updates": True,
                "minimize_to_tray": False,
                "confirm_exit": True,
                "auto_save_interval": 300  # seconds
            },
            
            # Advanced settings
            "advanced": {
                "tcp_buffer_size": 4096,
                "max_telemetry_buffer": 1000,
                "connection_retry_delay": 2000,  # milliseconds
                "debug_mode": False
            }
        }
    
    def load_config(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if configuration loaded successfully
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                self._config = self._merge_with_defaults(loaded_config)
                
                self.logger.info(f"Configuration loaded from {self.config_path}")
                self.config_loaded.emit()
                return True
            else:
                # Use defaults if no config file exists
                self._config = self._defaults.copy()
                self.logger.info("Using default configuration (no config file found)")
                self.save_config()  # Create initial config file
                return True
                
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            self.logger.error(f"Error loading configuration: {e}")
            # Fall back to defaults
            self._config = self._defaults.copy()
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error loading configuration: {e}")
            self._config = self._defaults.copy()
            return False
    
    def save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if configuration saved successfully
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save configuration with pretty formatting
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, sort_keys=True)
            
            self.logger.info(f"Configuration saved to {self.config_path}")
            self.config_saved.emit()
            return True
            
        except (PermissionError, OSError) as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error saving configuration: {e}")
            return False
    
    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge loaded configuration with defaults to ensure all keys exist.
        
        Args:
            loaded_config: Configuration loaded from file
            
        Returns:
            Merged configuration
        """
        merged = self._defaults.copy()
        
        def deep_merge(default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
            """Recursively merge dictionaries."""
            result = default.copy()
            
            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            
            return result
        
        return deep_merge(merged, loaded_config)
    
    def get(self, key_path: str, default=None):
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to configuration value (e.g., "connection.default_ip")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            keys = key_path.split('.')
            value = self._config
            
            for key in keys:
                value = value[key]
            
            return value
            
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any, save_immediately: bool = True):
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to configuration value
            value: Value to set
            save_immediately: Whether to save configuration to file immediately
        """
        try:
            keys = key_path.split('.')
            config = self._config
            
            # Navigate to parent dictionary
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set the value
            config[keys[-1]] = value
            
            # Emit change signal
            self.config_changed.emit(key_path, value)
            
            # Save if requested
            if save_immediately:
                self.save_config()
                
        except Exception as e:
            self.logger.error(f"Error setting configuration value {key_path}: {e}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name (e.g., "connection", "gui")
            
        Returns:
            Configuration section dictionary
        """
        return self._config.get(section, {}).copy()
    
    def set_section(self, section: str, values: Dict[str, Any], save_immediately: bool = True):
        """
        Set entire configuration section.
        
        Args:
            section: Section name
            values: Dictionary of values to set
            save_immediately: Whether to save immediately
        """
        if section not in self._config:
            self._config[section] = {}
        
        self._config[section].update(values)
        
        # Emit signals for changed values
        for key, value in values.items():
            self.config_changed.emit(f"{section}.{key}", value)
        
        if save_immediately:
            self.save_config()
    
    def reset_to_defaults(self, section: Optional[str] = None):
        """
        Reset configuration to defaults.
        
        Args:
            section: Specific section to reset, or None for all
        """
        if section:
            if section in self._defaults:
                self._config[section] = self._defaults[section].copy()
                self.logger.info(f"Reset {section} section to defaults")
            else:
                self.logger.warning(f"Unknown section: {section}")
        else:
            self._config = self._defaults.copy()
            self.logger.info("Reset all configuration to defaults")
        
        self.save_config()
    
    def export_config(self, file_path: str) -> bool:
        """
        Export configuration to specified file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if export successful
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, sort_keys=True)
            
            self.logger.info(f"Configuration exported to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """
        Import configuration from specified file.
        
        Args:
            file_path: Path to import file
            
        Returns:
            True if import successful
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Merge with defaults
            self._config = self._merge_with_defaults(imported_config)
            
            # Save the merged configuration
            self.save_config()
            
            self.logger.info(f"Configuration imported from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        Get information about the configuration.
        
        Returns:
            Dictionary with configuration metadata
        """
        try:
            stat = os.stat(self.config_path)
            return {
                'file_path': self.config_path,
                'file_exists': os.path.exists(self.config_path),
                'file_size': stat.st_size if os.path.exists(self.config_path) else 0,
                'last_modified': stat.st_mtime if os.path.exists(self.config_path) else 0,
                'sections': list(self._config.keys()),
                'total_keys': sum(len(v) if isinstance(v, dict) else 1 for v in self._config.values())
            }
        except Exception as e:
            self.logger.error(f"Error getting configuration info: {e}")
            return {
                'file_path': self.config_path,
                'file_exists': False,
                'error': str(e)
            }
