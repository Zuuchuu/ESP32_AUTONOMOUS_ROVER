"""
Styling and theme management for ESP32 Rover Control Station.

This module manages application themes, CSS stylesheets, and dynamic
styling based on application state (connection status, etc.).
"""

from PyQt5.QtCore import QObject
from PyQt5.QtGui import QFont


class StyleManager(QObject):
    """Manages application styling and themes."""
    
    def __init__(self):
        super().__init__()
        self.current_theme = "default"
    
    def get_main_stylesheet(self) -> str:
        """Get the main application stylesheet."""
        return """
        QMainWindow {
            background-color: #f0f0f0;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        /* Group Box Styling */
        QGroupBox {
            font-weight: bold;
            font-size: 11px;
            border: 2px solid #cccccc;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 15px;
            background-color: white;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            color: #333333;
        }
        
        /* Button Styling */
        QPushButton {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 10px 20px;
            text-align: center;
            font-size: 12px;
            font-weight: bold;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QPushButton:hover {
            background-color: #45a049;
        }
        
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        /* Special Button Types */
        QPushButton#connectButton {
            background-color: #2196F3;
        }
        
        QPushButton#connectButton:hover {
            background-color: #1976D2;
        }
        
        QPushButton#connectButton:pressed {
            background-color: #1565C0;
        }
        
        QPushButton#disconnectButton {
            background-color: #f44336;
        }
        
        QPushButton#disconnectButton:hover {
            background-color: #d32f2f;
        }
        
        QPushButton#startButton {
            background-color: #4CAF50;
        }
        
        QPushButton#stopButton {
            background-color: #FF9800;
        }
        
        QPushButton#stopButton:hover {
            background-color: #F57C00;
        }
        
        QPushButton#clearButton {
            background-color: #9E9E9E;
        }
        
        QPushButton#clearButton:hover {
            background-color: #757575;
        }
        
        /* Input Field Styling */
        QLineEdit {
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 11px;
            background-color: white;
        }
        
        QLineEdit:focus {
            border-color: #2196F3;
            outline: none;
        }
        
        QLineEdit:disabled {
            background-color: #f5f5f5;
            color: #999999;
        }
        
        /* Table Styling */
        QTableWidget {
            border: 1px solid #ddd;
            border-radius: 6px;
            background-color: white;
            gridline-color: #eee;
            font-size: 10px;
        }
        
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #eee;
        }
        
        QTableWidget::item:selected {
            background-color: #e3f2fd;
        }
        
        QHeaderView::section {
            background-color: #f5f5f5;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #ddd;
            font-weight: bold;
        }
        
        /* Slider Styling */
        QSlider::groove:horizontal {
            border: 1px solid #999999;
            height: 8px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
            margin: 2px 0;
            border-radius: 4px;
        }
        
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
            border: 1px solid #5c5c5c;
            width: 18px;
            margin: -2px 0;
            border-radius: 9px;
        }
        
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #d4d4d4, stop:1 #afafaf);
        }
        
        /* Label Styling */
        QLabel {
            font-size: 11px;
            color: #333333;
        }
        
        QLabel#statusLabel {
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 10px;
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px;
        }
        
        QLabel#connectionStatus {
            font-weight: bold;
            font-size: 12px;
        }
        
        /* Frame Styling */
        QFrame {
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: white;
        }
        
        /* Splitter Styling */
        QSplitter::handle {
            background-color: #ddd;
            width: 3px;
        }
        
        QSplitter::handle:hover {
            background-color: #bbb;
        }
        
        /* Tab Widget Styling */
        QTabWidget::pane {
            border: 1px solid #ddd;
            background-color: white;
            border-radius: 6px;
        }
        
        QTabBar::tab {
            background: #f5f5f5;
            color: #333333;
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-size: 11px;
            font-weight: 500;
            min-width: 120px;
            min-height: 30px;
        }
        
        QTabBar::tab:selected {
            background: white;
            color: #2196F3;
            border-bottom: 2px solid #2196F3;
        }
        
        QTabBar::tab:hover {
            background: #e8f4fd;
        }
        
        /* Scroll Area Styling */
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            background: #f5f5f5;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background: #cccccc;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #999999;
        }
        
        /* Mission Control Panel Specific Styles */
        QPushButton#planButton {
            background-color: #17a2b8;
        }
        
        QPushButton#planButton:hover {
            background-color: #138496;
        }
        
        QPushButton#startMissionButton {
            background-color: #28a745;
        }
        
        QPushButton#startMissionButton:hover {
            background-color: #1e7e34;
        }
        
        QPushButton#pauseMissionButton {
            background-color: #ffc107;
            color: #212529;
        }
        
        QPushButton#pauseMissionButton:hover {
            background-color: #e0a800;
        }
        
        QPushButton#abortButton {
            background-color: #dc3545;
        }
        
        QPushButton#abortButton:hover {
            background-color: #c82333;
        }
        """
    
    def get_connection_status_style(self, connected: bool) -> str:
        """Get style for connection status label."""
        if connected:
            return "color: #4CAF50; font-weight: bold; font-size: 12px;"
        else:
            return "color: #f44336; font-weight: bold; font-size: 12px;"
    
    def get_navigation_status_style(self, running: bool) -> str:
        """Get style for navigation status."""
        if running:
            return "color: #FF9800; font-weight: bold;"
        else:
            return "color: #666666; font-weight: normal;"
    
    def get_error_style(self) -> str:
        """Get style for error messages."""
        return "color: #f44336; font-weight: bold; background-color: #ffebee; padding: 8px; border-radius: 4px;"
    
    def get_success_style(self) -> str:
        """Get style for success messages."""
        return "color: #4CAF50; font-weight: bold; background-color: #e8f5e8; padding: 8px; border-radius: 4px;"
    
    def get_map_container_style(self) -> str:
        """Get style for map container."""
        return """
        QFrame#mapContainer {
            border: 2px solid #ddd;
            border-radius: 8px;
            background-color: white;
        }
        """
    
    def get_telemetry_style(self) -> str:
        """Get style for telemetry display."""
        return """
        QLabel#telemetryData {
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 10px;
            background-color: #2b2b2b;
            color: #00ff00;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 12px;
            line-height: 1.4;
        }
        """
    
    def apply_widget_style(self, widget, style_name: str):
        """Apply specific style to a widget."""
        styles = {
            'map_container': self.get_map_container_style(),
            'telemetry': self.get_telemetry_style(),
            'error': self.get_error_style(),
            'success': self.get_success_style()
        }
        
        if style_name in styles:
            widget.setStyleSheet(styles[style_name])
    
    def get_application_font(self) -> QFont:
        """Get the main application font."""
        font = QFont("Segoe UI", 9)
        font.setStyleStrategy(QFont.PreferAntialias)
        return font
