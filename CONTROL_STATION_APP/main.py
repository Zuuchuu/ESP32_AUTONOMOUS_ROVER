"""
ESP32 Rover Control Station Application
Entry point for the modular PyQt5 desktop application.

This application provides a comprehensive control interface for ESP32-based
autonomous rovers with features including:
- Interactive map-based waypoint selection
- Real-time telemetry display and monitoring
- TCP communication with rover
- Navigation control and speed adjustment
- Modular, scalable architecture

Requirements:
- Python 3.8+
- PyQt5
- Internet connection for map tiles

Author: ESP32 Rover Project
Version: 1.0.0
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.services import ApplicationService
from gui.main_window import MainWindow
from network.client import RoverClient
from utils.config import ConfigManager


class RoverControlApplication:
    """Main application class that coordinates all components."""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        self.app_service = None
        self.network_client = None
        self.config_manager = None
        self.logger = None
        
    def initialize(self) -> bool:
        """
        Initialize the application components.
        
        Returns:
            True if initialization successful
        """
        try:
            # Create QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("ESP32 Rover Control Station")
            self.app.setApplicationVersion("1.0.0")
            self.app.setOrganizationName("ESP32 Rover Project")
            
            # Set up logging
            self.setup_logging()
            
            # Initialize configuration manager
            self.config_manager = ConfigManager()
            self.logger.info("Configuration manager initialized")
            
            # Initialize network client
            self.network_client = RoverClient()
            self.logger.info("Network client initialized")
            
            # Initialize application service with configuration
            self.app_service = ApplicationService(self.config_manager)
            self.app_service.set_network_client(self.network_client)
            self.logger.info("Application service initialized")
            
            # Initialize main window
            self.main_window = MainWindow(self.app_service)
            self.logger.info("Main window initialized")
            
            # Apply saved window settings
            self.restore_window_state()
            
            # Set up auto-save timer
            self.setup_auto_save()
            
            self.logger.info("Application initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {str(e)}")
            QMessageBox.critical(None, "Initialization Error", 
                               f"Failed to initialize application:\n{str(e)}")
            return False
    
    def setup_logging(self):
        """Set up application logging."""
        # Get log level from config (fallback to INFO)
        log_level = getattr(logging, 
                           self.config_manager.get("application.log_level", "INFO").upper() 
                           if self.config_manager else "INFO")
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('RoverControlApp')
        self.logger.info("Logging system initialized")
        
        # Set PyQt5 warnings to WARNING level to reduce noise
        logging.getLogger('PyQt5').setLevel(logging.WARNING)
    
    def restore_window_state(self):
        """Restore window state from configuration."""
        if not self.config_manager or not self.main_window:
            return
        
        try:
            if self.config_manager.get("gui.remember_window_state", True):
                # Restore window geometry
                width = self.config_manager.get("gui.window_width", 1400)
                height = self.config_manager.get("gui.window_height", 900)
                x = self.config_manager.get("gui.window_x", 100)
                y = self.config_manager.get("gui.window_y", 100)
                
                self.main_window.setGeometry(x, y, width, height)
                self.logger.info(f"Restored window state: {width}x{height} at ({x}, {y})")
        
        except Exception as e:
            self.logger.warning(f"Failed to restore window state: {e}")
    
    def save_window_state(self):
        """Save current window state to configuration."""
        if not self.config_manager or not self.main_window:
            return
        
        try:
            if self.config_manager.get("gui.remember_window_state", True):
                geometry = self.main_window.geometry()
                
                self.config_manager.set("gui.window_width", geometry.width(), False)
                self.config_manager.set("gui.window_height", geometry.height(), False)
                self.config_manager.set("gui.window_x", geometry.x(), False)
                self.config_manager.set("gui.window_y", geometry.y(), False)
                
                # Save all changes at once
                self.config_manager.save_config()
                self.logger.info("Window state saved to configuration")
        
        except Exception as e:
            self.logger.warning(f"Failed to save window state: {e}")
    
    def setup_auto_save(self):
        """Set up automatic configuration saving."""
        if not self.config_manager:
            return
        
        # Set up timer for periodic auto-save
        auto_save_interval = self.config_manager.get("application.auto_save_interval", 300) * 1000
        
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(auto_save_interval)
        
        self.logger.info(f"Auto-save configured for every {auto_save_interval/1000:.0f} seconds")
    
    def auto_save(self):
        """Perform automatic save of configuration and state."""
        try:
            self.save_window_state()
            # Add any other periodic save operations here
        except Exception as e:
            self.logger.warning(f"Auto-save failed: {e}")
    
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Application exit code
        """
        if not self.initialize():
            return 1
        
        try:
            # Show main window
            self.main_window.show()
            
            # Center window on screen if it's the first run
            if not self.config_manager.get("gui.remember_window_state", True):
                self.main_window.move(
                    self.app.desktop().screen().rect().center() - 
                    self.main_window.rect().center()
                )
            
            self.logger.info("Application started successfully")
            
            # Run the application event loop
            exit_code = self.app.exec_()
            
            self.logger.info(f"Application exiting with code {exit_code}")
            return exit_code
            
        except Exception as e:
            self.logger.error(f"Runtime error: {str(e)}")
            QMessageBox.critical(None, "Runtime Error", 
                               f"A runtime error occurred:\n{str(e)}")
            return 1
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up application resources."""
        try:
            # Save final state
            self.save_window_state()
            
            # Disconnect from rover if connected
            if self.app_service:
                self.app_service.disconnect_from_rover()
            
            self.logger.info("Application cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"Cleanup error: {e}")


def main():
    """Main entry point for the application."""
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("ESP32 Rover Control Station v1.0")
            print("Usage: python main.py [options]")
            print("Options:")
            print("  -h, --help     Show this help message")
            print("  -v, --version  Show version information")
            print("  --reset-config Reset configuration to defaults")
            return 0
        elif sys.argv[1] in ['-v', '--version']:
            print("ESP32 Rover Control Station v1.0")
            print("Built with Python and PyQt5")
            return 0
        elif sys.argv[1] == '--reset-config':
            try:
                from utils.config import ConfigManager
                config = ConfigManager()
                config.reset_to_defaults()
                print("Configuration reset to defaults")
                return 0
            except Exception as e:
                print(f"Failed to reset configuration: {e}")
                return 1
    
    # Create and run application
    app = RoverControlApplication()
    return app.run()


if __name__ == '__main__':
    sys.exit(main())