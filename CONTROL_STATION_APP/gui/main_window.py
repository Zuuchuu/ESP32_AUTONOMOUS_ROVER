"""
Main window for ESP32 Rover Control Station.

This module contains the main window coordinator that manages the overall
GUI layout and coordinates between different panels. It acts as the central
hub for all GUI interactions.
"""

from typing import List
from PyQt5.QtWidgets import (QMainWindow, QSplitter, QVBoxLayout, 
                             QWidget, QMessageBox, QMenuBar, QStatusBar,
                              QLabel, QFrame, QGridLayout, QHBoxLayout, QPushButton, QCheckBox, QDoubleSpinBox, QSlider, QSizePolicy,
                              QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QAbstractItemView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont

from core.services import ApplicationService
from core.models import ConnectionState, NavigationState, MissionPlan, MissionProgress, MissionAnalytics, Waypoint, TelemetryData
from mission.planner import MissionPlanner
from .panels import MapWidget
from .styles import StyleManager


class MainWindow(QMainWindow):
    """
    Main application window that coordinates all GUI components.
    
    Acts as the central coordinator between panels and the application service.
    Manages layout, menu bar, status bar, and high-level GUI operations.
    """
    
    def __init__(self, app_service: ApplicationService):
        super().__init__()
        self.app_service = app_service
        self.style_manager = StyleManager()
        
        # Initialize mission planner
        self.mission_planner = MissionPlanner()
        self.current_mission = None
        self.current_mission_progress = None
        
        # UI state
        self.last_status_message = ""
        
        self.init_ui()
        self.connect_signals()
        self.setup_timers()
        
        # Apply initial styling
        self.setStyleSheet(self.style_manager.get_main_stylesheet())
        self.setFont(self.style_manager.get_application_font())

    def _create_slider(self, min_val: float, max_val: float, default: float, step: float = 0.1) -> QSlider:
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        steps = int(round((max_val - min_val) / step))
        slider.setMaximum(steps)
        slider.setSingleStep(1)
        slider.setPageStep(2)
        slider.setValue(int(round((default - min_val) / step)))
        slider.setTracking(True)
        # Make slider expand to take remaining horizontal space
        slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        slider.setToolTip(f"{default:.1f}")
        # Store mapping to convert value back to float
        slider._min_val = min_val
        slider._step = step
        slider.valueChanged.connect(lambda v: slider.setToolTip(f"{(slider._min_val + v*slider._step):.1f}"))
        # Comfortable slider style (larger groove/handle)
        slider.setStyleSheet(
            """
            QSlider::groove:horizontal { height: 12px; background: #e0e0e0; border-radius: 6px; }
            QSlider::handle:horizontal { background: #888; border: 1px solid #666; width: 22px; height: 22px; margin: -6px 0; border-radius: 11px; }
            QSlider::handle:horizontal:hover { background: #777; }
            """
        )
        return slider
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("ESP32 Autonomous Rover - Mission Control Center v1.0")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        
        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(main_layout)
        
        # Create main splitter (horizontal: map | controls)
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Create panels
        self.create_panels()
        
        # Left side: Map
        self.main_splitter.addWidget(self.map_widget)
        
        # Right side: Control panels
        self.control_container = self.create_control_container()
        self.main_splitter.addWidget(self.control_container)
        
        # Set splitter proportions (2/3 map, 1/3 controls) and stretch factors
        self.main_splitter.setSizes([1000, 500])
        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 1)
        
        # Create menu bar and status bar
        self.create_menu_bar()
        self.create_status_bar()
    
    def create_panels(self):
        """Create all GUI panels."""
        # Only the map widget is required for the current UI layout
        self.map_widget = MapWidget()
    
    def create_control_container(self) -> QWidget:
        """Create the container for all control panels using redesigned workflow-oriented interface."""
        container = QWidget()
        # Make panel resizable with fixed reasonable constraints
        container.setMinimumWidth(320)  # Minimum width to show content
        container.setMaximumWidth(600)  # Maximum width to prevent over-expansion
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(3, 3, 3, 3)
        main_layout.setSpacing(2)
        
        # Top two-row status bars (connectivity + sensors)
        self.top_status_container = self.create_top_status_bars()
        main_layout.addWidget(self.top_status_container)
        
        # Direct section placement - all sections fit equally in vertical space
        self.collapsible_waypoint_section = self.create_collapsible_waypoint_section()
        main_layout.addWidget(self.collapsible_waypoint_section)
        
        self.mission_setup_section = self.create_mission_setup_section()
        main_layout.addWidget(self.mission_setup_section)
        
        self.mission_control_section = self.create_mission_control_section()
        main_layout.addWidget(self.mission_control_section)
        
        self.mission_progress_section = self.create_mission_progress_section()
        main_layout.addWidget(self.mission_progress_section)
        
        # Let mission progress take remaining space; keep setup/control compact
        main_layout.setStretchFactor(self.mission_progress_section, 1)
        
        container.setLayout(main_layout)
        return container
    
    def create_top_status_bars(self) -> QWidget:
        """Create two-row top status bars: connectivity row and sensors row."""
        from PyQt5.QtWidgets import QStatusBar
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(3, 3, 3, 3)
        vlayout.setSpacing(2)

        # Row 1: Connectivity
        self.connect_status_bar = QStatusBar()
        self.connect_status_bar.setSizeGripEnabled(False)
        self.connect_status_bar.setStyleSheet("QStatusBar{background:#f8f9fa;border:1px solid #dee2e6;border-radius:6px;}")

        self.connection_indicator = QLabel("●")
        self.connection_indicator.setStyleSheet("color: #dc3545; font-size: 16px; font-weight: bold;")
        self.connection_indicator.setToolTip("Connection Status")
        self.connect_status_bar.addWidget(self.connection_indicator)

        self.connection_status_label = QLabel("Disconnected")
        self.connection_status_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #6c757d;")
        self.connect_status_bar.addWidget(self.connection_status_label)

        # IP:Port display
        self.ip_port_label = QLabel("IP:Port —")
        self.ip_port_label.setStyleSheet("font-size: 10px; color: #6c757d; padding-left:6px;")
        self.connect_status_bar.addWidget(self.ip_port_label)

        # Stretch between left info and inputs/buttons
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.connect_status_bar.addPermanentWidget(spacer, 1)

        # IP input
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP Address")
        self.ip_input.setText("192.168.1.100")
        self.ip_input.setFixedWidth(110)
        self.ip_input.setStyleSheet("QLineEdit{border:1px solid #ced4da;border-radius:4px;padding:3px 6px;font-size:10px;}")
        self.connect_status_bar.addPermanentWidget(self.ip_input)

        # Port input
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Port")
        self.port_input.setText("80")
        self.port_input.setFixedWidth(60)
        self.port_input.setStyleSheet("QLineEdit{border:1px solid #ced4da;border-radius:4px;padding:3px 6px;font-size:10px;}")
        self.connect_status_bar.addPermanentWidget(self.port_input)

        # Connect/Disconnect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setStyleSheet("""
            QPushButton { background-color: #28a745; color: white; border: none; border-radius: 4px; padding: 4px 12px; font-size: 10px; font-weight: bold; min-width: 90px; }
            QPushButton:hover { background-color: #218838; }
            QPushButton:disabled { background-color: #6c757d; color: #adb5bd; }
        """)
        self.connect_btn.clicked.connect(self.on_connect_disconnect_requested)
        self.connect_status_bar.addPermanentWidget(self.connect_btn)

        # Row 2: Sensors
        self.sensors_status_bar = QStatusBar()
        self.sensors_status_bar.setSizeGripEnabled(False)
        self.sensors_status_bar.setStyleSheet(
            "QStatusBar{background:#fdfdfe;border:1px solid #e6e9ef;border-radius:8px;}"
        )

        def make_label(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                """
                QLabel {
                    font-size: 11px;
                    color: #2c3e50;
                    padding: 4px 8px;
                    background-color: #f8f9fb;
                    border: 1px solid #e3e7ee;
                    border-radius: 12px;
                }
                """
            )
            return lbl

        # Grouped segments with separators for readability
        self.sensor_acc_label = make_label("Acc: —")
        self.sensor_gyro_label = make_label("Gyro: —")
        self.sensor_heading_label = make_label("Heading: —")
        self.sensor_temp_label = make_label("Temp: —")
        self.sensor_pressure_label = make_label("Pressure: —")
        self.sensor_gps_label = make_label("GPS: —")

        def sep():
            s = QLabel("|")
            s.setStyleSheet("color:#d0d4db; padding: 0 6px; font-weight:bold;")
            return s

        for w in [
            self.sensor_acc_label,
            self.sensor_gyro_label,
            sep(),
            self.sensor_heading_label,
            sep(),
            self.sensor_temp_label,
            self.sensor_pressure_label,
            sep(),
            self.sensor_gps_label,
        ]:
            if isinstance(w, QLabel) and w.text() == "|":
                self.sensors_status_bar.addPermanentWidget(w)
            else:
                self.sensors_status_bar.addWidget(w)

        vlayout.addWidget(self.connect_status_bar)
        vlayout.addWidget(self.sensors_status_bar)
        container.setLayout(vlayout)
        return container
    

    
    def create_collapsible_waypoint_section(self) -> QWidget:
        """Create collapsible waypoint management section."""
        section = QFrame()
        section.setFrameStyle(QFrame.StyledPanel)
        section.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        section.setStyleSheet("""
            QFrame {
                background-color: #e8f5e8;
                border: 1px solid #c3e6c3;
                border-radius: 6px;
                margin: 1px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)
        
        # Collapsible header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        
        waypoint_title = QLabel("🎯 WAYPOINT MANAGEMENT")
        waypoint_title.setStyleSheet("""
            font-weight: bold; 
            font-size: 11px; 
            color: #27ae60; 
            padding: 4px;
        """)
        header_layout.addWidget(waypoint_title)
        
        header_layout.addStretch()
        
        # Waypoint count indicator
        self.waypoint_count_label = QLabel("0 waypoints")
        self.waypoint_count_label.setStyleSheet("font-size: 10px; color: #6c757d; font-weight: bold;")
        header_layout.addWidget(self.waypoint_count_label)
        
        layout.addLayout(header_layout)
        
        # Always visible content
        self.compact_waypoint_panel = self.create_compact_waypoint_panel()
        layout.addWidget(self.compact_waypoint_panel)
        
        # No stretch to avoid extra vertical space
        
        section.setLayout(layout)
        return section
    
    def create_compact_waypoint_panel(self) -> QWidget:
        """Create compact waypoint panel for the collapsible section."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Instructions
        instructions = QLabel("Click map or add manually:")
        instructions.setStyleSheet("color: #666; font-style: italic; font-size: 9px;")
        layout.addWidget(instructions)
        
        # Expanded table (increase visible rows and allow expansion)
        self.compact_waypoint_table = QTableWidget(0, 3)
        self.compact_waypoint_table.setHorizontalHeaderLabels(["#", "Latitude", "Longitude"])
        self.compact_waypoint_table.setMinimumHeight(200)
        self.compact_waypoint_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.compact_waypoint_table.setAlternatingRowColors(True)
        # Enable multi-row selection for targeted removal
        self.compact_waypoint_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.compact_waypoint_table.setSelectionMode(QAbstractItemView.MultiSelection)
        
        # Configure headers
        header = self.compact_waypoint_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        layout.addWidget(self.compact_waypoint_table)
        
        # Manual input row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(4)
        
        lat_label = QLabel("Lat:")
        lat_label.setStyleSheet("font-size: 10px; min-width: 25px;")
        input_layout.addWidget(lat_label)
        
        self.compact_lat_input = QLineEdit()
        self.compact_lat_input.setPlaceholderText("37.7749")
        self.compact_lat_input.setStyleSheet("font-size: 10px; padding: 2px;")
        self.compact_lat_input.returnPressed.connect(self.add_waypoint_from_compact)
        input_layout.addWidget(self.compact_lat_input)
        
        lng_label = QLabel("Lng:")
        lng_label.setStyleSheet("font-size: 10px; min-width: 25px;")
        input_layout.addWidget(lng_label)
        
        self.compact_lng_input = QLineEdit()
        self.compact_lng_input.setPlaceholderText("-122.4194")
        self.compact_lng_input.setStyleSheet("font-size: 10px; padding: 2px;")
        self.compact_lng_input.returnPressed.connect(self.add_waypoint_from_compact)
        input_layout.addWidget(self.compact_lng_input)
        
        add_btn = QPushButton("Add")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        add_btn.clicked.connect(self.add_waypoint_from_compact)
        input_layout.addWidget(add_btn)
        
        clear_btn = QPushButton("🗑️ Remove Selected")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        clear_btn.clicked.connect(self.remove_selected_from_compact)
        input_layout.addWidget(clear_btn)
        
        layout.addLayout(input_layout)
        
        panel.setLayout(layout)
        return panel

    def remove_selected_from_compact(self):
        """Remove only selected rows from the compact waypoint table via service."""
        table = self.compact_waypoint_table
        selection = table.selectionModel()
        if not selection:
            return
        selected_rows = sorted({idx.row() for idx in selection.selectedRows()})
        if not selected_rows:
            return
        # Delegate removal to application service (keeps state/signals consistent)
        self.app_service.remove_selected_waypoints(selected_rows)
    
    def create_mission_setup_section(self) -> QWidget:
        """Create mission setup section."""
        section = QFrame()
        section.setFrameStyle(QFrame.StyledPanel)
        section.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        section.setStyleSheet("""
            QFrame {
                background-color: #e8f4fd;
                border: 1px solid #bee5eb;
                border-radius: 6px;
                margin: 1px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 4, 6, 4)  # tighter margins, no bottom
        layout.setSpacing(4)
        
        # Header
        header = QLabel("📋 MISSION SETUP")
        header.setStyleSheet("""
            font-weight: bold; 
            font-size: 11px; 
            color: #2980b9; 
            padding: 4px;
        """)
        layout.addWidget(header)
        
        # Compact controls in grid
        controls_layout = QGridLayout()
        controls_layout.setContentsMargins(0, 0, 0, 4)
        controls_layout.setHorizontalSpacing(6)
        controls_layout.setVerticalSpacing(4)
        
        # Optimize checkbox
        self.setup_optimize_checkbox = QCheckBox("Optimize Route")
        self.setup_optimize_checkbox.setChecked(True)
        self.setup_optimize_checkbox.setStyleSheet("QCheckBox{font-size:10px;font-weight:500;}")
        controls_layout.addWidget(self.setup_optimize_checkbox, 0, 0, 1, 2)
        
        # Speed control row
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #2980b9;")
        controls_layout.addWidget(speed_label, 1, 0)
        
        speed_widget = QWidget()
        speed_layout = QHBoxLayout()
        speed_layout.setContentsMargins(0, 0, 0, 0)
        speed_layout.setSpacing(4)
        
        self.setup_speed_slider = self._create_slider(0.1, 5.0, 1.0, step=0.1)
        speed_layout.addWidget(self.setup_speed_slider, 1)
        
        self.setup_speed_spinner = QDoubleSpinBox()
        self.setup_speed_spinner.setRange(0.1, 5.0)
        self.setup_speed_spinner.setSingleStep(0.1)
        self.setup_speed_spinner.setValue(1.0)
        self.setup_speed_spinner.setSuffix(" m/s")
        self.setup_speed_spinner.setMinimumWidth(100)
        self.setup_speed_spinner.setMaximumWidth(130)
        self.setup_speed_spinner.setStyleSheet("QDoubleSpinBox{font-size:11px; padding: 4px 6px;} QDoubleSpinBox::up-button, QDoubleSpinBox::down-button{width:16px;height:14px;}")
        speed_layout.addWidget(self.setup_speed_spinner)
        
        speed_widget.setLayout(speed_layout)
        controls_layout.addWidget(speed_widget, 1, 1)
        
        # CTE control row
        cte_label = QLabel("CTE:")
        cte_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #e67e22;")
        controls_layout.addWidget(cte_label, 2, 0)
        
        cte_widget = QWidget()
        cte_layout = QHBoxLayout()
        cte_layout.setContentsMargins(0, 0, 0, 0)
        cte_layout.setSpacing(4)
        
        self.setup_cte_slider = self._create_slider(0.1, 10.0, 0.1, step=0.1)
        cte_layout.addWidget(self.setup_cte_slider, 1)
        
        self.setup_cte_spinner = QDoubleSpinBox()
        self.setup_cte_spinner.setRange(0.1, 10.0)
        self.setup_cte_spinner.setSingleStep(0.1)
        self.setup_cte_spinner.setValue(0.1)
        self.setup_cte_spinner.setSuffix(" m")
        self.setup_cte_spinner.setMinimumWidth(90)
        self.setup_cte_spinner.setMaximumWidth(120)
        self.setup_cte_spinner.setStyleSheet("QDoubleSpinBox{font-size:11px; padding: 4px 6px;} QDoubleSpinBox::up-button, QDoubleSpinBox::down-button{width:16px;height:14px;}")
        cte_layout.addWidget(self.setup_cte_spinner)
        
        cte_widget.setLayout(cte_layout)
        controls_layout.addWidget(cte_widget, 2, 1)
        
        layout.addLayout(controls_layout)
        
        # Prominent Plan Mission Button
        self.setup_plan_btn = QPushButton("📋 PLAN MISSION")
        self.setup_plan_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 10px;      /* halved from 8px 16px */
                font-size: 12px;        /* halved from 12px */
                font-weight: bold;
                min-height: 20px;      /* halved from 32px */
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.setup_plan_btn.setEnabled(False)
        self.setup_plan_btn.clicked.connect(self.on_mission_plan_requested)
        layout.addWidget(self.setup_plan_btn)

        # Persistent Mission Plan Summary (appears after planning)
        self.mission_plan_summary_frame = QFrame()
        self.mission_plan_summary_frame.setFrameStyle(QFrame.StyledPanel)
        self.mission_plan_summary_frame.setStyleSheet(
            """
            QFrame { background-color: #f7fbff; border: 1px solid #d6e9ff; border-radius: 6px; }
            QLabel#missionPlanTitle { font-weight: bold; font-size: 11px; color: #2980b9; }
            QLabel#missionPlanBody { background-color: white; border: 1px solid #e3e7ee; border-radius: 4px; padding: 8px; font-size: 10px; }
            """
        )
        mp_layout = QVBoxLayout()
        mp_layout.setContentsMargins(6, 6, 6, 6)
        mp_layout.setSpacing(4)
        mp_title = QLabel("📄 Mission Plan")
        mp_title.setObjectName("missionPlanTitle")
        self.mission_plan_summary_label = QLabel("No mission plan")
        self.mission_plan_summary_label.setObjectName("missionPlanBody")
        self.mission_plan_summary_label.setWordWrap(True)
        # Expand vertical size for Mission Plan information section
        self.mission_plan_summary_label.setMinimumHeight(80)
        self.mission_plan_summary_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        mp_layout.addWidget(mp_title)
        mp_layout.addWidget(self.mission_plan_summary_label)
        self.mission_plan_summary_frame.setLayout(mp_layout)
        self.mission_plan_summary_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout.addWidget(self.mission_plan_summary_frame)
        
        # No stretch to avoid extra vertical space
        
        section.setLayout(layout)
        return section
    
    def create_mission_control_section(self) -> QWidget:
        """Create mission control section with prominent action buttons."""
        section = QFrame()
        section.setFrameStyle(QFrame.StyledPanel)
        section.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        section.setStyleSheet("""
            QFrame {
                background-color: #eafaf1;
                border: 1px solid #c3e6cb;
                border-radius: 6px;
                margin: 1px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 6, 8, 0)  # bottom margin set to 0 per request
        layout.setSpacing(6)
        
        # Header
        header = QLabel("🚀 MISSION CONTROL")
        header.setStyleSheet("""
            font-weight: bold; 
            font-size: 11px; 
            color: #27ae60; 
            padding: 4px;
        """)
        layout.addWidget(header)
        
        # Control buttons in grid
        buttons_layout = QGridLayout()
        buttons_layout.setContentsMargins(6, 0, 0, 12)
        buttons_layout.setHorizontalSpacing(6)
        buttons_layout.setVerticalSpacing(4)
        
        # Prominent Start/Resume button
        self.control_start_btn = QPushButton("▶️ START MISSION")
        self.control_start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 6px;
                font-size: 9px;
                font-weight: bold;
                min-height: 18px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.control_start_btn.setEnabled(False)
        self.control_start_btn.clicked.connect(self.on_mission_start_requested)
        buttons_layout.addWidget(self.control_start_btn, 0, 0)
        
        # Pause button
        self.control_pause_btn = QPushButton("⏸️ PAUSE")
        self.control_pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 6px;
                padding: 4px 6px;
                font-size: 9px;
                font-weight: bold;
                min-height: 18px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.control_pause_btn.setEnabled(False)
        self.control_pause_btn.clicked.connect(self.on_mission_pause_requested)
        buttons_layout.addWidget(self.control_pause_btn, 0, 1)
        
        # Abort button
        self.control_abort_btn = QPushButton("🛑 ABORT")
        self.control_abort_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
                min-height: 18px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.control_abort_btn.setEnabled(False)
        self.control_abort_btn.clicked.connect(self.on_mission_abort_requested)
        buttons_layout.addWidget(self.control_abort_btn, 1, 0)
        
        # Clear button
        self.control_clear_btn = QPushButton("🗑️ CLEAR")
        self.control_clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
                min-height: 18px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.control_clear_btn.setEnabled(False)
        self.control_clear_btn.clicked.connect(self.on_mission_clear_requested)
        buttons_layout.addWidget(self.control_clear_btn, 1, 1)
        
        layout.addLayout(buttons_layout)
        
        # Add stretch to fill remaining space
        layout.addStretch()
        
        section.setLayout(layout)
        return section
    
    def create_mission_progress_section(self) -> QWidget:
        """Create mission progress section that expands to fill remaining space."""
        section = QFrame()
        section.setFrameStyle(QFrame.StyledPanel)
        section.setStyleSheet("""
            QFrame {
                background-color: #fef9e7;
                border: 1px solid #ffeaa7;
                border-radius: 6px;
                margin: 1px;
            }
        """)
        
        # Set size policy to expand vertically
        section.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # Header
        header = QLabel("📊 MISSION PROGRESS")
        header.setStyleSheet("""
            font-weight: bold; 
            font-size: 12px; 
            color: #e67e22; 
            padding: 6px;
        """)
        layout.addWidget(header)
        
        # Progress display - larger and more prominent
        self.progress_main_display = QLabel("No active mission")
        self.progress_main_display.setWordWrap(True)
        self.progress_main_display.setMinimumHeight(60)
        self.progress_main_display.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.progress_main_display.setStyleSheet("""
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 8px;
            font-size: 12px;
            font-weight: bold;
        """)
        layout.addWidget(self.progress_main_display)
        
        # Larger, more prominent metrics
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(8)
        
        self.progress_eta_label = QLabel("ETA: --")
        self.progress_eta_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #28a745;
            background-color: rgba(40, 167, 69, 0.1);
            border: 1px solid #28a745;
            border-radius: 4px;
            padding: 8px;
        """)
        metrics_layout.addWidget(self.progress_eta_label, 0, 0)
        
        self.progress_completion_label = QLabel("Progress: 0%")
        self.progress_completion_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #007bff;
            background-color: rgba(0, 123, 255, 0.1);
            border: 1px solid #007bff;
            border-radius: 4px;
            padding: 8px;
        """)
        metrics_layout.addWidget(self.progress_completion_label, 0, 1)
        
        self.progress_cte_label = QLabel("CTE: 0.0m")
        self.progress_cte_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #ffc107;
            background-color: rgba(255, 193, 7, 0.1);
            border: 1px solid #ffc107;
            border-radius: 4px;
            padding: 8px;
        """)
        metrics_layout.addWidget(self.progress_cte_label, 1, 0, 1, 2)
        
        layout.addLayout(metrics_layout)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        section.setLayout(layout)
        return section
    

    
    # Helper methods for new functionality

    
    def on_connect_disconnect_requested(self):
        """Handle connect/disconnect button click."""
        connection_state = self.app_service.get_connection_state()
        
        if connection_state == ConnectionState.CONNECTED:
            # Disconnect
            self.app_service.disconnect_from_rover()
        else:
            # Connect using IP/Port from header inputs
            try:
                ip = self.ip_input.text().strip()
                port = int(self.port_input.text().strip())
                
                if not ip:
                    ip = "192.168.1.100"  # Fallback default
                if port <= 0 or port > 65535:
                    port = 80  # Fallback default
                
                self.app_service.connect_to_rover(ip, port)
            except (ValueError, AttributeError):
                # Fallback to defaults
                self.app_service.connect_to_rover("192.168.1.100", 80)
    

    
    def add_waypoint_from_compact(self):
        """Add waypoint from compact input fields."""
        try:
            lat_text = self.compact_lat_input.text().strip()
            lng_text = self.compact_lng_input.text().strip()
            
            if not lat_text or not lng_text:
                return
            
            lat = float(lat_text)
            lng = float(lng_text)
            
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return
            
            self.app_service.add_waypoint_manual(lat, lng)
            self.compact_lat_input.clear()
            self.compact_lng_input.clear()
            
        except ValueError:
            pass  # Invalid input, ignore silently
    
    def update_connect_status_bar(self, connection_state):
        """Update connectivity row status bar (dot, text, inputs, button, IP:Port)."""
        if connection_state == ConnectionState.CONNECTED:
            self.connection_indicator.setStyleSheet("color: #28a745; font-size: 16px; font-weight: bold;")
            self.connection_status_label.setText("Connected")
            self.connection_status_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #28a745;")
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setStyleSheet("QPushButton{background-color:#dc3545;color:white;border:none;border-radius:4px;padding:4px 12px;font-size:10px;font-weight:bold;min-width:90px;} QPushButton:hover{background-color:#c82333;}")
            # Disable inputs when connected
            self.ip_input.setEnabled(False)
            self.port_input.setEnabled(False)
        else:
            self.connection_indicator.setStyleSheet("color: #dc3545; font-size: 16px; font-weight: bold;")
            self.connection_status_label.setText("Disconnected")
            self.connection_status_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #6c757d;")
            self.connect_btn.setText("Connect")
            self.connect_btn.setStyleSheet("QPushButton{background-color:#28a745;color:white;border:none;border-radius:4px;padding:4px 12px;font-size:10px;font-weight:bold;min-width:90px;} QPushButton:hover{background-color:#218838;}")
            self.ip_input.setEnabled(True)
            self.port_input.setEnabled(True)

        # Update IP:Port label
        try:
            ip = self.ip_input.text().strip() or "—"
            port = int(self.port_input.text().strip()) if self.port_input.text().strip().isdigit() else None
            port_text = str(port) if port is not None else "—"
            self.ip_port_label.setText(f"IP:Port {ip}:{port_text}")
        except Exception:
            self.ip_port_label.setText("IP:Port —")

    def update_sensors_status_bar(self, telemetry):
        """Update sensors row (acc, gyro, heading, temp, pressure, GPS)."""
        if telemetry and telemetry.is_valid:
            # Acc / Gyro arrays may not be full length if data missing
            acc = telemetry.acceleration if telemetry.acceleration and len(telemetry.acceleration) == 3 else [0.0, 0.0, 0.0]
            gyro = telemetry.gyroscope if telemetry.gyroscope and len(telemetry.gyroscope) == 3 else [0.0, 0.0, 0.0]
            self.sensor_acc_label.setText(f"Acc: {acc[0]:.2f}, {acc[1]:.2f}, {acc[2]:.2f} m/s²")
            self.sensor_gyro_label.setText(f"Gyro: {gyro[0]:.2f}, {gyro[1]:.2f}, {gyro[2]:.2f} °/s")
            self.sensor_heading_label.setText(f"Heading: {telemetry.heading:.1f}°")
            self.sensor_temp_label.setText(f"Temp: {telemetry.temperature:.1f} °C")
            if hasattr(telemetry, 'pressure') and telemetry.pressure is not None:
                self.sensor_pressure_label.setText(f"Pressure: {telemetry.pressure:.1f} hPa")
            else:
                self.sensor_pressure_label.setText("Pressure: —")
            if telemetry.has_valid_position():
                self.sensor_gps_label.setText(f"GPS: {telemetry.latitude:.5f}, {telemetry.longitude:.5f}")
            else:
                self.sensor_gps_label.setText("GPS: —")
        else:
            self.sensor_acc_label.setText("Acc: —")
            self.sensor_gyro_label.setText("Gyro: —")
            self.sensor_heading_label.setText("Heading: —")
            self.sensor_temp_label.setText("Temp: —")
            self.sensor_pressure_label.setText("Pressure: —")
            self.sensor_gps_label.setText("GPS: —")
    

    
    def update_compact_waypoint_table(self, waypoints):
        """Update the compact waypoint table."""
        # Clear selection and contents to avoid stale rows after deletions
        self.compact_waypoint_table.clearSelection()
        self.compact_waypoint_table.clearContents()
        self.compact_waypoint_table.setRowCount(0)
        self.compact_waypoint_table.setRowCount(len(waypoints))
        
        for i, waypoint in enumerate(waypoints):
            self.compact_waypoint_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.compact_waypoint_table.setItem(i, 1, QTableWidgetItem(f"{waypoint.latitude:.6f}"))
            self.compact_waypoint_table.setItem(i, 2, QTableWidgetItem(f"{waypoint.longitude:.6f}"))
        
        # Update waypoint count
        count = len(waypoints)
        self.waypoint_count_label.setText(f"{count} waypoint{'s' if count != 1 else ''}")
        
        # Update setup button
        self.setup_plan_btn.setEnabled(count >= 2)
        
        # Update clear button - enable only when waypoints exist
        if hasattr(self, 'control_clear_btn'):
            self.control_clear_btn.setEnabled(count > 0)
    
    def _adapt_ui_for_mission_state(self, state: str):
        """Adapt UI layout based on mission state."""
        if state == "planning":
            # Show setup section (waypoint section always visible now)
            pass
            
        elif state == "planned":
            # Show control section prominently (waypoint section always visible now)
            pass
            
        elif state == "active":
            # Show progress prominently (waypoint section always visible now)
            pass  # Mission status now shown in progress section
            
        elif state == "completed":
            # Show all sections
            pass  # Mission status now shown in progress section
            
        elif state == "idle":
            # Reset to planning state
            pass  # Mission status now shown in progress section
    
    # Legacy integrated mission tab removed
    
    # Legacy status tab removed
    
    def create_mission_planning_section(self) -> QWidget:
        """Create mission planning section with optimization and statistics."""
        from PyQt5.QtWidgets import QCheckBox, QDoubleSpinBox
        
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Planning controls frame
        planning_frame = QFrame()
        planning_frame.setFrameStyle(QFrame.StyledPanel)
        planning_layout = QGridLayout()
        planning_layout.setSpacing(6)
        
        # Plan Mission Button - Compact styling
        self.plan_mission_btn = QPushButton("📋 Plan Mission")
        self.plan_mission_btn.setObjectName("planButton")
        self.plan_mission_btn.setMinimumHeight(28)
        self.plan_mission_btn.setEnabled(False)
        self.plan_mission_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 11px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        planning_layout.addWidget(self.plan_mission_btn, 0, 0, 1, 2)
        
        # Mission parameters - Responsive grid layout
        params_widget = QWidget()
        params_layout = QGridLayout()
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(4)

        # Row 1: Optimize toggle
        self.optimize_route_checkbox = QCheckBox("Optimize Route")
        self.optimize_route_checkbox.setChecked(True)
        self.optimize_route_checkbox.setStyleSheet("QCheckBox{font-size:10px;font-weight:500;} QCheckBox::indicator{width:20px;height:12px;} QCheckBox::indicator:unchecked{border-radius:6px;background:#e9ecef;border:1px solid #ced4da;} QCheckBox::indicator:checked{border-radius:6px;background:#4caf50;border:1px solid #4caf50;}")
        params_layout.addWidget(self.optimize_route_checkbox, 0, 0, 1, 3)

        # Row 2: Speed control
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("font-size:10px; min-width: 35px;")
        params_layout.addWidget(speed_label, 1, 0)
        
        self.mission_speed_slider = self._create_slider(0.1, 5.0, 1.0, step=0.1)
        params_layout.addWidget(self.mission_speed_slider, 1, 1)
        
        self.mission_speed_spinner = QDoubleSpinBox()
        self.mission_speed_spinner.setRange(0.1, 5.0)
        self.mission_speed_spinner.setSingleStep(0.1)
        self.mission_speed_spinner.setValue(1.0)
        self.mission_speed_spinner.setSuffix(" m/s")
        self.mission_speed_spinner.setMinimumWidth(75)
        self.mission_speed_spinner.setMaximumWidth(85)
        self.mission_speed_spinner.setStyleSheet("font-size:10px; padding: 2px;")
        params_layout.addWidget(self.mission_speed_spinner, 1, 2)

        # Row 3: CTE Threshold
        cte_label = QLabel("CTE:")
        cte_label.setStyleSheet("font-size:10px; min-width: 35px;")
        params_layout.addWidget(cte_label, 2, 0)
        
        self.cte_threshold_slider = self._create_slider(0.1, 10.0, 0.1, step=0.1)
        params_layout.addWidget(self.cte_threshold_slider, 2, 1)
        
        self.cte_threshold_spinner = QDoubleSpinBox()
        self.cte_threshold_spinner.setRange(0.1, 10.0)
        self.cte_threshold_spinner.setSingleStep(0.1)
        self.cte_threshold_spinner.setValue(0.1)
        self.cte_threshold_spinner.setSuffix(" m")
        self.cte_threshold_spinner.setMinimumWidth(70)
        self.cte_threshold_spinner.setMaximumWidth(80)
        self.cte_threshold_spinner.setStyleSheet("font-size:10px; padding: 2px;")
        params_layout.addWidget(self.cte_threshold_spinner, 2, 2)

        params_widget.setLayout(params_layout)
        planning_layout.addWidget(params_widget, 1, 0, 1, 2)
        
        planning_frame.setLayout(planning_layout)
        layout.addWidget(planning_frame)
        
        # Mission Statistics - Compact
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.StyledPanel)
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(2)
        stats_layout.setContentsMargins(4, 4, 4, 4)
        
        stats_title = QLabel("📊 Mission Statistics")
        stats_title.setFont(QFont("Arial", 8, QFont.Bold))
        stats_layout.addWidget(stats_title)
        
        self.mission_stats_display = QLabel("Add waypoints to plan mission")
        self.mission_stats_display.setWordWrap(True)
        self.mission_stats_display.setMinimumHeight(40)
        self.mission_stats_display.setMaximumHeight(65)
        self.mission_stats_display.setStyleSheet("""
            background-color: #f8f9fa; 
            border: 1px solid #dee2e6; 
            border-radius: 3px; 
            padding: 4px; 
            font-size: 9px;
        """)
        stats_layout.addWidget(self.mission_stats_display)
        
        stats_frame.setLayout(stats_layout)
        layout.addWidget(stats_frame)
        
        panel.setLayout(layout)
        return panel
    
    def create_mission_execution_section(self) -> QWidget:
        """Create mission execution controls."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Execution controls frame
        exec_frame = QFrame()
        exec_frame.setFrameStyle(QFrame.StyledPanel)
        exec_layout = QGridLayout()
        exec_layout.setSpacing(4)
        exec_layout.setContentsMargins(4, 4, 4, 4)
        
        # Mission control buttons - Compact styling
        button_style = """
            QPushButton {
                font-weight: bold;
                font-size: 8px;
                border: none;
                border-radius: 4px;
                padding: 3px 4px;
                min-height: 13px;
            }
            QPushButton:hover {
                opacity: 0.8;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """
        
        self.start_mission_btn = QPushButton("▶️ Start Mission")
        self.start_mission_btn.setObjectName("startMissionButton")
        self.start_mission_btn.setEnabled(False)
        self.start_mission_btn.setStyleSheet(button_style + """
            QPushButton {
                background-color: #27ae60;
                color: white;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        exec_layout.addWidget(self.start_mission_btn, 0, 0)
        
        self.pause_mission_btn = QPushButton("⏸️ Pause")
        self.pause_mission_btn.setObjectName("pauseMissionButton")
        self.pause_mission_btn.setEnabled(False)
        self.pause_mission_btn.setStyleSheet(button_style + """
            QPushButton {
                background-color: #f39c12;
                color: white;
            }
            QPushButton:hover {
                background-color: #d68910;
            }
        """)
        exec_layout.addWidget(self.pause_mission_btn, 0, 1)
        
        self.abort_mission_btn = QPushButton("🛑 Abort")
        self.abort_mission_btn.setObjectName("abortButton")
        self.abort_mission_btn.setEnabled(False)
        self.abort_mission_btn.setStyleSheet(button_style + """
            QPushButton {
                background-color: #e74c3c;
                color: white;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        exec_layout.addWidget(self.abort_mission_btn, 1, 0)
        
        self.clear_mission_btn = QPushButton("🗑️ Clear")
        self.clear_mission_btn.setObjectName("clearButton")
        self.clear_mission_btn.setEnabled(False)
        self.clear_mission_btn.setStyleSheet(button_style + """
            QPushButton {
                background-color: #95a5a6;
                color: white;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        exec_layout.addWidget(self.clear_mission_btn, 1, 1)
        
        exec_frame.setLayout(exec_layout)
        layout.addWidget(exec_frame)
        
        panel.setLayout(layout)
        return panel
    
    def create_mission_monitoring_section(self) -> QWidget:
        """Create mission progress monitoring section."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Progress display frame
        progress_frame = QFrame()
        progress_frame.setFrameStyle(QFrame.StyledPanel)
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(2)
        progress_layout.setContentsMargins(4, 4, 4, 4)
        
        progress_title = QLabel("🎯 Mission Progress")
        progress_title.setFont(QFont("Arial", 8, QFont.Bold))
        progress_layout.addWidget(progress_title)
        
        self.mission_progress_display = QLabel("No active mission")
        self.mission_progress_display.setWordWrap(True)
        self.mission_progress_display.setMinimumHeight(50)
        self.mission_progress_display.setMaximumHeight(75)
        self.mission_progress_display.setStyleSheet("""
            background-color: #e8f4fd; 
            border: 1px solid #bee5eb; 
            border-radius: 4px; 
            padding: 6px; 
            font-size: 10px;
        """)
        progress_layout.addWidget(self.mission_progress_display)
        
        # ETA and metrics - Grid layout for better organization
        metrics_widget = QWidget()
        metrics_layout = QGridLayout()
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(3)
        
        self.eta_label = QLabel("ETA: --")
        self.eta_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #28a745; padding: 2px;")
        metrics_layout.addWidget(self.eta_label, 0, 0)
        
        self.completion_label = QLabel("Progress: 0%")
        self.completion_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #007bff; padding: 2px;")
        metrics_layout.addWidget(self.completion_label, 0, 1)
        
        self.cte_label = QLabel("CTE: 0.0m")
        self.cte_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #ffc107; padding: 2px;")
        metrics_layout.addWidget(self.cte_label, 1, 0, 1, 2)
        
        metrics_widget.setLayout(metrics_layout)
        progress_layout.addWidget(metrics_widget)
        
        progress_frame.setLayout(progress_layout)
        layout.addWidget(progress_frame)
        
        panel.setLayout(layout)
        return panel
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Settings action
        settings_action = file_menu.addAction('&Settings')
        settings_action.setShortcut('Ctrl+,')
        settings_action.triggered.connect(self.show_settings)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = file_menu.addAction('E&xit')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        
        # Connection menu
        conn_menu = menubar.addMenu('&Connection')
        
        # Connect action
        self.connect_action = conn_menu.addAction('&Connect')
        self.connect_action.setShortcut('Ctrl+C')
        self.connect_action.triggered.connect(self.on_connect_disconnect_requested)
        
        # Disconnect action
        self.disconnect_action = conn_menu.addAction('&Disconnect')
        self.disconnect_action.setShortcut('Ctrl+D')
        self.disconnect_action.triggered.connect(self.app_service.disconnect_from_rover)
        self.disconnect_action.setEnabled(False)
        

        
        # Mission menu  
        mission_menu = menubar.addMenu('&Mission')
        
        # Clear waypoints
        clear_waypoints_action = mission_menu.addAction('&Clear Waypoints')
        clear_waypoints_action.setShortcut('Ctrl+L')
        clear_waypoints_action.triggered.connect(self.app_service.clear_waypoints)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        # About action
        about_action = help_menu.addAction('&About')
        about_action.triggered.connect(self.show_about)
    
    def create_status_bar(self):
        """Create the application status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Connect to rover to begin")
    
    def connect_signals(self):
        """Connect all signals between components."""
        # Connect compact waypoint panel through MainWindow handlers only
        # Connect new mission control signals
        self.setup_plan_btn.clicked.connect(self.on_mission_plan_requested)
        self.control_start_btn.clicked.connect(self.on_mission_start_requested)
        self.control_pause_btn.clicked.connect(self.on_mission_pause_requested)
        self.control_abort_btn.clicked.connect(self.on_mission_abort_requested)
        self.control_clear_btn.clicked.connect(self.on_mission_clear_requested)
        self.setup_optimize_checkbox.toggled.connect(self.on_waypoint_optimization_toggled)
        self.setup_speed_spinner.valueChanged.connect(self.on_mission_speed_changed)
        # Sync sliders and spinboxes for new interface
        self.setup_speed_slider.valueChanged.connect(lambda v: self.setup_speed_spinner.setValue(self.setup_speed_slider._min_val + v*self.setup_speed_slider._step))
        self.setup_speed_spinner.valueChanged.connect(lambda val: self.setup_speed_slider.setValue(int(round((val - self.setup_speed_slider._min_val)/self.setup_speed_slider._step))))
        self.setup_cte_slider.valueChanged.connect(lambda v: self.setup_cte_spinner.setValue(self.setup_cte_slider._min_val + v*self.setup_cte_slider._step))
        self.setup_cte_spinner.valueChanged.connect(lambda val: self.setup_cte_slider.setValue(int(round((val - self.setup_cte_slider._min_val)/self.setup_cte_slider._step))))
        
        # Connect legacy mission control signals (for backward compatibility)
        if hasattr(self, 'plan_mission_btn'):
            self.plan_mission_btn.clicked.connect(self.on_mission_plan_requested)
        if hasattr(self, 'start_mission_btn'):
            self.start_mission_btn.clicked.connect(self.on_mission_start_requested)
        if hasattr(self, 'pause_mission_btn'):
            self.pause_mission_btn.clicked.connect(self.on_mission_pause_requested)
        if hasattr(self, 'abort_mission_btn'):
            self.abort_mission_btn.clicked.connect(self.on_mission_abort_requested)
        if hasattr(self, 'clear_mission_btn'):
            self.clear_mission_btn.clicked.connect(self.on_mission_clear_requested)
        if hasattr(self, 'optimize_route_checkbox'):
            self.optimize_route_checkbox.toggled.connect(self.on_waypoint_optimization_toggled)
        if hasattr(self, 'mission_speed_spinner'):
            self.mission_speed_spinner.valueChanged.connect(self.on_mission_speed_changed)
            # Sync sliders and spinboxes for legacy interface
            if hasattr(self, 'mission_speed_slider'):
                self.mission_speed_slider.valueChanged.connect(lambda v: self.mission_speed_spinner.setValue(self.mission_speed_slider._min_val + v*self.mission_speed_slider._step))
                self.mission_speed_spinner.valueChanged.connect(lambda val: self.mission_speed_slider.setValue(int(round((val - self.mission_speed_slider._min_val)/self.mission_speed_slider._step))))
            if hasattr(self, 'cte_threshold_slider') and hasattr(self, 'cte_threshold_spinner'):
                self.cte_threshold_slider.valueChanged.connect(lambda v: self.cte_threshold_spinner.setValue(self.cte_threshold_slider._min_val + v*self.cte_threshold_slider._step))
                self.cte_threshold_spinner.valueChanged.connect(lambda val: self.cte_threshold_slider.setValue(int(round((val - self.cte_threshold_slider._min_val)/self.cte_threshold_slider._step))))
        
        # Connect map signals
        self.map_widget.waypoint_added_from_map.connect(self.app_service.add_waypoint_from_map)
        self.map_widget.map_loaded.connect(self.on_map_loaded)
        
        # Connect mission planner signals
        self.mission_planner.mission_plan_ready.connect(self.on_mission_plan_ready)
        self.mission_planner.mission_started.connect(self.on_mission_started)
        self.mission_planner.mission_progress_updated.connect(self.on_mission_progress_updated)
        self.mission_planner.mission_completed.connect(self.on_mission_completed)
        self.mission_planner.mission_aborted.connect(self.on_mission_aborted)
        self.mission_planner.waypoint_reached.connect(self.on_waypoint_reached)
        self.mission_planner.path_deviation_detected.connect(self.on_path_deviation_detected)
        self.mission_planner.error_occurred.connect(self.on_error_occurred)
        
        # Connect application service signals to UI updates
        self.app_service.app_state.connection_state_changed.connect(self.on_connection_state_changed)
        self.app_service.app_state.navigation_state_changed.connect(self.on_navigation_state_changed)
        self.app_service.app_state.telemetry_updated.connect(self.on_telemetry_updated)
        self.app_service.app_state.waypoints_changed.connect(self.on_waypoints_changed)
        self.app_service.app_state.speed_changed.connect(self.on_speed_changed)
        self.app_service.app_state.error_occurred.connect(self.on_error_occurred)
        
        self.app_service.status_message.connect(self.update_status_message)
        self.app_service.operation_completed.connect(self.on_operation_completed)
    
    def setup_timers(self):
        """Set up periodic timers for UI updates."""
        # Status message timer (clear temporary messages after 5 seconds)
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.clear_temporary_status)
        self.status_timer.setSingleShot(True)
    
    # Event handlers
    def on_connection_state_changed(self, state: ConnectionState):
        """Handle connection state changes."""
        # Update all panels
        connected = (state == ConnectionState.CONNECTED)
        
        # No external panels to update; top bars reflect state

        # Update top connectivity bar
        self.update_connect_status_bar(state)
        
        # Update menu actions
        self.connect_action.setEnabled(not connected)
        self.disconnect_action.setEnabled(connected)

        
        # Update status bar
        state_messages = {
            ConnectionState.DISCONNECTED: "Disconnected from rover",
            ConnectionState.CONNECTING: "Connecting to rover...",
            ConnectionState.CONNECTED: "Connected to rover",
            ConnectionState.ERROR: f"Connection error: {self.app_service.app_state.rover_state.error_message}"
        }
        self.update_status_message(state_messages.get(state, "Unknown state"))
    
    def on_navigation_state_changed(self, state: NavigationState):
        """Handle navigation state changes."""
        # Legacy navigation state handling removed

        
        # Update status
        state_messages = {
            NavigationState.STOPPED: "Navigation stopped",
            NavigationState.RUNNING: "Navigation in progress",
            NavigationState.PAUSED: "Navigation paused",
            NavigationState.ERROR: "Navigation error"
        }
        self.update_status_message(state_messages.get(state, "Unknown navigation state"))
    
    def on_telemetry_updated(self, telemetry):
        """Handle telemetry updates."""
        # Update map and status bars
        self.map_widget.update_rover_position(telemetry)
        self.update_sensors_status_bar(telemetry)
        
        # Update top bars with telemetry
        connection_state = self.app_service.get_connection_state()
        self.update_connect_status_bar(connection_state)
        self.update_sensors_status_bar(telemetry)
    
    def on_waypoints_changed(self, waypoints):
        """Handle waypoint list changes."""
        # Update compact waypoint table
        self.update_compact_waypoint_table(waypoints)
        
        # Update setup section button state
        waypoint_count = len(waypoints)
        self.setup_plan_btn.setEnabled(waypoint_count >= 2)
        
        # Update map waypoints programmatically when list shrinks or clears.
        # Suppress map monitoring to avoid re-adding via map callbacks.
        if len(waypoints) == 0:
            # Clear operation
            self.map_widget.begin_programmatic_waypoint_update()
            try:
                self.map_widget.clear_waypoints()
            finally:
                self.map_widget.end_programmatic_waypoint_update()
        elif hasattr(self, '_last_waypoint_count_gui') and len(waypoints) < self._last_waypoint_count_gui:
            # Waypoints were removed — resync map markers to current list
            self.map_widget.sync_waypoints(waypoints)
            # If a mission exists, re-plan route with updated waypoints
            if getattr(self, 'current_mission', None):
                current_position = None
                telemetry = self.app_service.get_current_telemetry()
                if telemetry and telemetry.has_valid_position():
                    current_position = (telemetry.latitude, telemetry.longitude)
                elif waypoints:
                    # Fallback to first waypoint as reference point
                    current_position = (waypoints[0].latitude, waypoints[0].longitude)
                if current_position:
                    try:
                        self.mission_planner.replan_mission(waypoints, current_position)
                    except Exception:
                        pass
        
        # Track waypoint count for GUI synchronization
        self._last_waypoint_count_gui = len(waypoints)
    
    def on_speed_changed(self, speed: int):
        """Handle speed changes."""
        # Speed is now handled by mission speed parameters
    
    def on_error_occurred(self, message: str):
        """Handle application errors."""
        QMessageBox.critical(self, "Error", message)
        self.update_status_message(f"Error: {message}")
    
    def on_operation_completed(self, operation: str, success: bool):
        """Handle operation completion."""
        if success:
            messages = {
                "connect": "Successfully connected to rover",
                "disconnect": "Disconnected from rover"
            }
            self.update_status_message(messages.get(operation, f"{operation} completed"))
        else:
            self.update_status_message(f"{operation} failed")
    
    def on_map_loaded(self, success: bool):
        """Handle map loading result."""
        if success:
            self.update_status_message("Map loaded successfully")
        else:
            self.update_status_message("Failed to load map")
    
    # UI helper methods
    def update_status_message(self, message: str):
        """Update status bar message."""
        self.status_bar.showMessage(message)
        self.last_status_message = message
        
        # Clear temporary messages after 5 seconds
        if "Error" not in message and "Failed" not in message:
            self.status_timer.start(5000)
    
    def clear_temporary_status(self):
        """Clear temporary status messages."""
        if self.app_service.get_connection_state() == ConnectionState.CONNECTED:
            self.status_bar.showMessage("Connected - Ready for operations")
        else:
            self.status_bar.showMessage("Ready - Connect to rover to begin")
    
    def show_settings(self):
        """Show settings dialog (placeholder)."""
        QMessageBox.information(self, "Settings", "Settings dialog not yet implemented.")
    
    def show_about(self):
        """Show about dialog."""
        about_text = """
        ESP32 Rover Control Station v1.0
        
        A desktop application for controlling ESP32-based autonomous rovers.
        
        Features:
        • Interactive map with waypoint management
        • Real-time telemetry display
        • TCP communication with rover
        • Navigation control and monitoring
        
        Built with Python and PyQt5
        Compatible with ESP32 rover firmware
        """
        QMessageBox.about(self, "About ESP32 Rover Control Station", about_text.strip())
    
    # No custom resize handler needed - control panel is now resizable via splitter
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Abort mission if active
        if self.current_mission_progress and self.current_mission_progress.is_active:
            self.mission_planner.abort_mission("Application closing")
        
        # Disconnect from rover if connected
        if self.app_service.get_connection_state() == ConnectionState.CONNECTED:
            self.app_service.disconnect_from_rover()
        
        # Accept the close event
        event.accept()
    
    # Mission planner event handlers
    def on_mission_plan_requested(self):
        """Handle mission planning request."""
        waypoints = self.app_service.get_waypoints()
        if len(waypoints) < 2:
            QMessageBox.warning(self, "Mission Planning", "At least 2 waypoints required for mission planning.")
            return
        
        # Get mission settings from setup interface (prioritize new interface)
        if hasattr(self, 'setup_optimize_checkbox'):
            optimize_order = self.setup_optimize_checkbox.isChecked()
            rover_speed = self.setup_speed_spinner.value()
            cte_threshold = self.setup_cte_spinner.value()
        elif hasattr(self, 'optimize_route_checkbox'):
            # Fallback to legacy interface
            optimize_order = self.optimize_route_checkbox.isChecked()
            rover_speed = self.mission_speed_spinner.value()
            cte_threshold = self.cte_threshold_spinner.value()
        else:
            # Default values
            optimize_order = True
            rover_speed = 1.0
            cte_threshold = 0.1
        
        # Get current rover position if available
        current_position = None
        if self.app_service.get_connection_state() == ConnectionState.CONNECTED:
            telemetry = self.app_service.get_current_telemetry()
            if telemetry and telemetry.has_valid_position():
                current_position = (telemetry.latitude, telemetry.longitude)
        
        # Plan mission
        success = self.mission_planner.plan_mission(
            waypoints=waypoints,
            start_position=current_position,
            optimize_order=optimize_order,
            rover_speed=rover_speed,
            cte_threshold=cte_threshold
        )
        
        if not success:
            QMessageBox.critical(self, "Mission Planning", "Failed to plan mission. Check logs for details.")
    
    def on_mission_start_requested(self):
        """Handle mission start request."""
        if not self.current_mission:
            QMessageBox.warning(self, "Mission Start", "No mission plan available. Plan a mission first.")
            return
        
        if self.app_service.get_connection_state() != ConnectionState.CONNECTED:
            QMessageBox.warning(self, "Mission Start", "Must be connected to rover to start mission.")
            return
        
        # Get current rover position; if unavailable, fall back to first mission waypoint
        telemetry = self.app_service.get_current_telemetry()
        if telemetry and telemetry.has_valid_position():
            current_position = (telemetry.latitude, telemetry.longitude)
        else:
            # Fallback for simulator/initial start: use first waypoint as starting position
            if self.current_mission and self.current_mission.waypoints:
                wp0 = self.current_mission.waypoints[0]
                current_position = (wp0.latitude, wp0.longitude)
            else:
                QMessageBox.warning(self, "Mission Start", "No valid position or waypoints available to start.")
                return
        
        # Start mission
        success = self.mission_planner.start_mission(current_position)
        if not success:
            QMessageBox.critical(self, "Mission Start", "Failed to start mission. Check logs for details.")
    
    def on_mission_pause_requested(self):
        """Handle mission pause request."""
        self.mission_planner.pause_mission()
    
    def on_mission_abort_requested(self):
        """Handle mission abort request."""
        reply = QMessageBox.question(self, "Abort Mission", 
                                   "Are you sure you want to abort the current mission?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.mission_planner.abort_mission("User requested abort")
    
    def on_mission_clear_requested(self):
        """Handle mission clear request."""
        self.current_mission = None
        self.current_mission_progress = None
        self._reset_mission_interface()
        self.map_widget.clear_mission_visualization()
        self.app_service.clear_waypoints() # Also clear waypoints from app state
        
        # Update UI state
        self._adapt_ui_for_mission_state("idle")
        # Clear mission plan summary
        self.clear_mission_plan_summary()
    
    def on_waypoint_optimization_toggled(self, enabled: bool):
        """Handle waypoint optimization toggle."""
        # This is handled in mission planning, no immediate action needed
        pass
    
    def on_mission_speed_changed(self, speed: float):
        """Handle mission speed change."""
        # Update current mission if active
        if self.current_mission_progress and self.current_mission_progress.is_active:
            # Could send speed update to rover here
            pass
    
    def on_mission_plan_ready(self, mission_plan):
        """Handle mission plan ready event."""
        self.current_mission = mission_plan
        
        # Update mission statistics display (legacy interface)
        if hasattr(self, 'mission_stats_display'):
            stats = mission_plan.get_mission_summary()
            stats_text = f"""Mission Plan Ready:
• {stats['waypoints']} waypoints
• {stats['total_distance_m']:.0f}m total distance
• {stats['estimated_duration_min']:.1f} min estimated time
• {stats['average_speed_mps']:.1f} m/s average speed
• Optimization: {stats['optimization']}"""
            
            self.mission_stats_display.setText(stats_text)
        
        # Enable mission execution controls
        if hasattr(self, 'control_start_btn'):
            self.control_start_btn.setEnabled(True)
            self.control_clear_btn.setEnabled(True)
        if hasattr(self, 'start_mission_btn'):
            self.start_mission_btn.setEnabled(True)
            self.clear_mission_btn.setEnabled(True)
        
        # Update status header
        # Mission planned - status now shown in progress section
        
        # Update map visualization
        self.map_widget.display_mission_plan(mission_plan)
        self.map_widget.center_on_mission(mission_plan)
        
        # Adapt UI for mission planned state
        self._adapt_ui_for_mission_state("planned")
        
        # Update status
        stats = mission_plan.get_mission_summary()
        self.update_status_message(f"Mission planned: {stats['waypoints']} waypoints, {stats['total_distance_m']:.0f}m")
        # Update persistent mission plan summary in setup section
        self.update_mission_plan_summary(mission_plan)
    
    def on_mission_started(self, mission_plan):
        """Handle mission started event."""
        # Update control buttons
        if hasattr(self, 'control_start_btn'):
            self.control_start_btn.setEnabled(False)
            self.control_pause_btn.setEnabled(True)
            self.control_abort_btn.setEnabled(True)
        if hasattr(self, 'start_mission_btn'):
            self.start_mission_btn.setEnabled(False)
            self.pause_mission_btn.setEnabled(True)
            self.abort_mission_btn.setEnabled(True)
        
        # Adapt UI for active mission
        self._adapt_ui_for_mission_state("active")
        
        self.update_status_message("Mission started - rover is now autonomous")
    
    def on_mission_progress_updated(self, progress):
        """Handle mission progress update."""
        self.current_mission_progress = progress
        
        # Update progress display (legacy interface)
        if hasattr(self, 'mission_progress_display'):
            stats = progress.get_progress_summary()
            progress_text = f"""Mission Active:
• Progress: {stats['completion_pct']:.1f}%
• Waypoint: {stats['current_waypoint']} of {stats['total_segments']}
• Distance to target: {stats['distance_to_target_m']:.1f}m
• Cross-track error: {stats['cross_track_error_m']:.1f}m
• Speed: {stats['current_speed_mps']:.1f} m/s
• Status: {stats['status']}"""
            
            self.mission_progress_display.setText(progress_text)
        
        # Update new progress section
        stats = progress.get_progress_summary()
        if hasattr(self, 'progress_main_display'):
            self.progress_main_display.setText(
                f"Mission {stats['completion_pct']:.1f}% complete\n"
                f"Waypoint {stats['current_waypoint']} of {stats['total_segments']}"
            )
        
        # Update metrics labels (both legacy and new)
        if hasattr(self, 'progress_eta_label'):
            self.progress_eta_label.setText(f"ETA: {stats['eta_min']:.1f}min")
        if hasattr(self, 'progress_completion_label'):
            self.progress_completion_label.setText(f"Progress: {stats['completion_pct']:.0f}%")
        if hasattr(self, 'progress_cte_label'):
            self.progress_cte_label.setText(f"CTE: {stats['cross_track_error_m']:.1f}m")
        
        if hasattr(self, 'eta_label'):
            self.eta_label.setText(f"ETA: {stats['eta_min']:.1f} min")
        if hasattr(self, 'completion_label'):
            self.completion_label.setText(f"Progress: {stats['completion_pct']:.1f}%")
        if hasattr(self, 'cte_label'):
            self.cte_label.setText(f"CTE: {stats['cross_track_error_m']:.1f}m")
        
        # Update button states based on mission status
        if progress.is_active:
            self.start_mission_btn.setText("Resume Mission")
            self.start_mission_btn.setEnabled(False)
            self.pause_mission_btn.setEnabled(True)
            self.abort_mission_btn.setEnabled(True)
        elif progress.mission_status == "paused":
            self.start_mission_btn.setText("Resume Mission")
            self.start_mission_btn.setEnabled(True)
            self.pause_mission_btn.setEnabled(False)
            self.abort_mission_btn.setEnabled(True)
        elif progress.is_completed:
            self._mission_completed()
        
        # Update map visualization
        if self.current_mission:
            self.map_widget.update_mission_progress(progress, self.current_mission)
            self.map_widget.show_cross_track_error(progress, self.current_mission)
            self.map_widget.update_mission_statistics(progress)
        
        # Update rover trail
        if hasattr(self.mission_planner, 'position_history'):
            self.map_widget.show_rover_trail(self.mission_planner.position_history)
    
    def on_mission_completed(self, analytics):
        """Handle mission completion."""
        # Show completion dialog
        stats = analytics.get_analytics_summary()
        completion_text = f"""Mission Completed Successfully!
        
Time: {stats['completion_time_min']:.1f} minutes
Efficiency: {stats['efficiency_rating']:.1f}%
Waypoints reached: {stats['waypoints_reached']}/{stats['total_waypoints']}
Max deviation: {stats['max_deviation_m']:.1f}m"""
        
        QMessageBox.information(self, "Mission Complete", completion_text)
        
        # Update status
        self.update_status_message("Mission completed successfully")
    
    def on_mission_aborted(self, reason):
        """Handle mission abort."""
        self.mission_control_panel.mission_aborted(reason)
        self.update_status_message(f"Mission aborted: {reason}")
    
    def on_waypoint_reached(self, waypoint_index):
        """Handle waypoint reached event."""
        self.update_status_message(f"Waypoint {waypoint_index + 1} reached")
    
    def on_path_deviation_detected(self, cross_track_error):
        """Handle path deviation detection."""
        if abs(cross_track_error) > 5.0:  # Significant deviation
            self.update_status_message(f"Path deviation detected: {cross_track_error:.1f}m")
    
    def _mission_completed(self):
        """Handle mission completion and reset interface."""
        if hasattr(self, 'mission_progress_display'):
            self.mission_progress_display.setText("Mission completed successfully!")
        if hasattr(self, 'progress_main_display'):
            self.progress_main_display.setText("Mission completed successfully!")
        
        # Reset button states
        if hasattr(self, 'control_start_btn'):
            self.control_start_btn.setText("▶️ START MISSION")
            self.control_start_btn.setEnabled(False)
            self.control_pause_btn.setEnabled(False)
            self.control_abort_btn.setEnabled(False)
            self.control_clear_btn.setEnabled(True)
        
        if hasattr(self, 'start_mission_btn'):
            self.start_mission_btn.setText("Start Mission")
            self.start_mission_btn.setEnabled(False)
            self.pause_mission_btn.setEnabled(False)
            self.abort_mission_btn.setEnabled(False)
            self.clear_mission_btn.setEnabled(True)
        
        # Update UI state
        self._adapt_ui_for_mission_state("completed")
        
        # Update status
        self.update_status_message("Mission completed successfully")
        # Clear mission plan summary on completion
        self.clear_mission_plan_summary()
    
    def _reset_mission_interface(self):
        """Reset mission interface to initial state."""
        # Reset displays (new interface)
        if hasattr(self, 'progress_main_display'):
            self.progress_main_display.setText("No active mission")
        
        # Reset metrics (new interface)
        if hasattr(self, 'progress_eta_label'):
            self.progress_eta_label.setText("ETA: --")
        if hasattr(self, 'progress_completion_label'):
            self.progress_completion_label.setText("Progress: 0%")
        if hasattr(self, 'progress_cte_label'):
            self.progress_cte_label.setText("CTE: 0.0m")
        
        # Reset button states (new interface)
        waypoint_count = len(self.app_service.get_waypoints())
        if hasattr(self, 'setup_plan_btn'):
            self.setup_plan_btn.setEnabled(waypoint_count >= 2)
        if hasattr(self, 'control_start_btn'):
            self.control_start_btn.setText("▶️ START MISSION")
            self.control_start_btn.setEnabled(False)
            self.control_pause_btn.setEnabled(False)
            self.control_abort_btn.setEnabled(False)
            self.control_clear_btn.setEnabled(False)
        
        # Reset displays
        
        # Reset metrics
        if hasattr(self, 'eta_label'):
            self.eta_label.setText("ETA: --")
        if hasattr(self, 'completion_label'):
            self.completion_label.setText("Progress: 0%")
        if hasattr(self, 'cte_label'):
            self.cte_label.setText("CTE: 0.0m")
        
        # Reset button states
        if hasattr(self, 'start_mission_btn'):
            self.start_mission_btn.setText("Start Mission")
            self.start_mission_btn.setEnabled(False)
        if hasattr(self, 'pause_mission_btn'):
            self.pause_mission_btn.setEnabled(False)
        if hasattr(self, 'abort_mission_btn'):
            self.abort_mission_btn.setEnabled(False)
        if hasattr(self, 'clear_mission_btn'):
            self.clear_mission_btn.setEnabled(False)

        # Clear mission plan summary in setup section
        self.clear_mission_plan_summary()

    # Mission plan summary helpers
    def _format_distance_m(self, meters: float) -> str:
        if meters is None:
            return "—"
        if meters >= 1000:
            return f"{meters/1000:.2f} km"
        return f"{meters:.0f} m"

    def _format_duration_s(self, seconds: float) -> str:
        if seconds is None:
            return "—"
        if seconds >= 3600:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            return f"{h}h {m}m"
        if seconds >= 60:
            return f"{seconds/60:.1f} min"
        return f"{seconds:.0f} s"

    def update_mission_plan_summary(self, mission_plan: MissionPlan):
        """Render persistent mission plan summary in mission setup section."""
        if not hasattr(self, 'mission_plan_summary_label'):
            return
        if not mission_plan:
            self.mission_plan_summary_label.setText("No mission plan")
            return
        summary = mission_plan.get_mission_summary()
        text = (
            f"Waypoints: {summary['waypoints']}\n"
            f"Total distance: {self._format_distance_m(summary['total_distance_m'])}\n"
            f"Estimated duration: {self._format_duration_s(summary['estimated_duration_sec'])}\n"
            f"Average speed: {summary['average_speed_mps']:.1f} m/s\n"
            f"Optimization: {summary['optimization']}\n"
            f"CTE threshold: {mission_plan.cte_threshold:.1f} m"
        )
        self.mission_plan_summary_label.setText(text)

    def clear_mission_plan_summary(self):
        if hasattr(self, 'mission_plan_summary_label'):
            self.mission_plan_summary_label.setText("No mission plan")

