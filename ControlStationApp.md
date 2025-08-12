# Control Station Application for ESP32 Rover

## Introduction
This guide provides a comprehensive development instruction for creating a Windows desktop application to control an ESP32-based autonomous rover as describe in `ESP32_Rover.md` guide over WiFi. The application features a graphical user interface (GUI) with an embedded interactive map using Leaflet.js on the left for selecting up to 10 waypoints and a control panel on the right for manual waypoint entry, connection management, rover control (start/stop, speed adjustment), and real-time telemetry display. The telemetry includes the rover’s position (latitude, longitude), heading, GY-87 sensor data (acceleration, gyroscope, magnetometer, temperature), and WiFi connectivity status. Tailored for users with expertise in embedded systems and robotics, this guide assumes familiarity with Python programming and networking concepts, providing actionable steps for implementation.

The application is built using Python 3.8 or later with the PyQt5 framework, leveraging QWebEngineView for map integration and TCP sockets for communication with the rover. The GUI is divided into a left panel with the interactive map and a right panel with controls for connection, waypoint management, rover control, and status display. The rover, running FreeRTOS tasks as described in prior discussions, handles incoming waypoints and commands, sending telemetry data for real-time monitoring. This instruction ensures a modular, scalable, and robust implementation, addressing industry best practices for robotics control interfaces.

## Requirements

### Software Requirements
- **Platform**: Windows
- **Programming Language**: Python 3.8
- **Libraries**:
  - **PyQt5**: For GUI development and web view integration ([PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/))
  - **requests**: Optional, for potential future enhancements like offline map tile fetching
- **Development Environment**: Any Python-compatible IDE, such as PyCharm ([PyCharm](https://www.jetbrains.com/pycharm/)) or Visual Studio Code ([VS Code](https://code.visualstudio.com/))
- **Internet Access**: Required for loading OpenStreetMap tiles via Leaflet.js. Offline maps are possible but require additional setup ([Leaflet Offline](https://github.com/leaflet-extras/leaflet-providers))

### Hardware Assumptions
- The ESP32 rover runs a TCP server on port 80 and connects to an existing WiFi network, as specified in prior discussions.
- The rover sends telemetry data in JSON format, including:
  - Latitude and longitude (from u-blox M10 GPS)
  - Heading (from GY-87 IMU magnetometer)
  - IMU data: acceleration, gyroscope, magnetometer (from GY-87)
  - Temperature (from GY-87)
  - WiFi signal strength (in dBm or percentage)
- The desktop computer and rover are on accessible networks, with the rover’s IP address provided by the user. Cross-network communication may require tools like ngrok ([ngrok](https://ngrok.com/)) if the computer and rover are on different networks.

## Setup Instructions
1. **Install Python**: Download and install Python 3.8 or later from [python.org](https://www.python.org/downloads/). Verify installation with `python --version`.
2. **Install PyQt5**: Run `pip install PyQt5` in a terminal or command prompt to install the GUI framework.
3. **Prepare the Map File**: Create an HTML file (`map.html`) with Leaflet.js to display the interactive map, as shown in the code snippets below.
4. **Set Up Project Directory**: Organize the ControlStationApp folder inside ESP32_AUTONOMOUS_ROVER project as follows:
   ```
   ControlStationApp/
   ├── main.py
   ├── main_window.py
   ├── communication.py
   ├── utils.py
   ├── map.html
   ```
5. **Test Connectivity**: Ensure the rover’s TCP server is running and accessible by pinging its IP address (e.g., `ping 192.168.1.100`) or using a tool like `telnet` to verify port 80 connectivity.

## Code Structure
The application is modular to ensure maintainability and scalability, with separate files for distinct functionalities.

| File              | Purpose                                                                 |
|-------------------|-------------------------------------------------------------------------|
| `main.py`         | Entry point; initializes the PyQt5 application and launches the main window. |
| `main_window.py`  | Defines the GUI layout, widgets, and interactions for waypoint management, rover control, and telemetry display. |
| `communication.py`| Handles TCP socket communication for sending waypoints and commands and receiving telemetry. |
| `utils.py`        | Contains utility functions, such as angle normalization for future enhancements. |
| `map.html`        | HTML file with Leaflet.js for the embedded interactive map.              |

## Implementation Details

### GUI Layout
The GUI is designed for intuitive control and clear visualization:
- **Left Panel**: A `QWebEngineView` widget displays an interactive map using Leaflet.js with OpenStreetMap tiles. Users can click on the map to add up to 10 waypoints, which are marked with pins. The rover’s current position is shown with a distinct marker (e.g., a red icon).
- **Right Panel**:
  - **Connection Section**: An input field (`QLineEdit`) for the rover’s IP address and a “Connect” button to establish a TCP connection.
  - **Waypoint Management**: A table (`QTableWidget`) displays the waypoint list (latitude, longitude). Input fields allow manual entry of coordinates, with buttons to add, remove, or clear waypoints.
  - **Rover Control**: Includes “Start” and “Stop” buttons to control navigation and a speed slider (`QSlider`) with a label to adjust and display the rover’s speed (0-100%).
  - **Rover Status**: Labels display real-time telemetry, including position, heading, IMU data (acceleration, gyroscope, magnetometer), temperature, and WiFi strength.

### Map Integration
The map, embedded via `QWebEngineView`, supports:
- **Waypoint Selection**: Clicking on the map adds a marker and stores coordinates in a JavaScript array, limited to 10 waypoints.
- **Rover Position Display**: A unique marker shows the rover’s current position, updated via telemetry data.
- **JavaScript Interaction**: Python code uses `runJavaScript` to add waypoints, retrieve the waypoint list, clear waypoints, and update the rover’s position, ensuring seamless integration ([Leaflet.js Documentation](https://leafletjs.com/)).

### Communication Protocol
- **Connection**: The app acts as a TCP client, connecting to the rover’s TCP server on port 80 using the user-provided IP address.
- **Sending Data**:
  - **Waypoints**: `{"waypoints": [{"lat": float, "lon": float}, ...]}`
  - **Start Command**: `{"command": "start"}`
  - **Stop Command**: `{"command": "stop"}`
  - **Set Speed**: `{"command": "set_speed", "speed": int}` (speed in percentage, 0-100)
- **Receiving Telemetry**: The rover sends periodic updates (e.g., every second) in JSON format:
  ```json
  {
    "lat": float,
    "lon": float,
    "heading": float,
    "imu_data": {
      "accel": [float, float, float],
      "gyro": [float, float, float],
      "mag": [float, float, float]
    },
    "temperature": float,
    "wifi_strength": int
  }
  ```
- **Connectivity Status**: The app displays “Connected” or “Disconnected” based on the socket status, updated when the connection is established or lost.

### Threading
A `QThread` handles telemetry reception to ensure the GUI remains responsive. The thread reads data from the TCP socket and emits a `pyqtSignal` with parsed telemetry, which the main thread uses to update the map and status labels ([PyQt Threading Tutorial](https://www.pythonguis.com/tutorials/multithreading-pyqt-applications-qthread/)).

### Error Handling
- **Connection Failures**: Display a `QMessageBox` if the TCP connection fails (e.g., invalid IP or rover offline).
- **Invalid Inputs**: Validate manual waypoint entries (latitude: -90 to 90, longitude: -180 to 180) and show an error for invalid values.
- **Map Loading**: Wait for the `QWebEngineView` `loadFinished` signal before executing JavaScript to ensure the map is ready.
- **Network Issues**: Handle socket errors by notifying the user and attempting to reconnect if appropriate ([Python Socket Programming](https://docs.python.org/3/library/socket.html)).

## Example Code Snippets

### map.html
This file sets up the Leaflet.js map, handling click events to add waypoints and providing functions for Python interaction.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Rover Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        #map { height: 100vh; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([51.505, -0.09], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        var waypoints = [];
        var markers = [];
        var roverMarker = null;

        map.on('click', function(e) {
            if (waypoints.length < 10) {
                var marker = L.marker(e.latlng).addTo(map);
                markers.push(marker);
                waypoints.push(e.latlng);
            }
        });

        function getWaypoints() {
            return waypoints.map(function(wp) { return {lat: wp.lat, lng: wp.lng}; });
        }

        function clearWaypoints() {
            markers.forEach(function(m) { map.removeLayer(m); });
            markers = [];
            waypoints = [];
        }

        function addWaypoint(lat, lng) {
            if (waypoints.length < 10) {
                var latlng = L.latLng(lat, lng);
                var marker = L.marker(latlng).addTo(map);
                markers.push(marker);
                waypoints.push(latlng);
            }
        }

        function setRoverPosition(lat, lng) {
            if (roverMarker) {
                roverMarker.setLatLng([lat, lng]);
            } else {
                roverMarker = L.marker([lat, lng], {
                    icon: L.icon({iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png', iconSize: [25, 41]})
                }).addTo(map);
            }
        }
    </script>
</body>
</html>
```

### main.py
Initializes the PyQt5 application and launches the main window.

```python
import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
```

### main_window.py
Defines the GUI layout and interactions, including waypoint management, rover control, and telemetry display.

```python
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, QTableWidget, QMessageBox, QSlider
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt
from communication import TelemetryThread
import socket
import json

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rover Control Station")
        self.setGeometry(100, 100, 1200, 800)
        self.sock = None
        self.telemetry_thread = None

        # Left panel: Map
        self.map_view = QWebEngineView()
        self.map_view.load(QUrl.fromLocalFile("path/to/map.html"))
        self.map_view.loadFinished.connect(self.on_map_loaded)

        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # Connection section
        self.ip_input = QLineEdit("192.168.1.100")  # Default IP for testing
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_rover)
        self.connection_status = QLabel("Connection: Disconnected")
        right_layout.addWidget(QLabel("Rover IP:"))
        right_layout.addWidget(self.ip_input)
        right_layout.addWidget(self.connect_button)
        right_layout.addWidget(self.connection_status)

        # Waypoint list
        self.waypoint_table = QTableWidget(0, 2)
        self.waypoint_table.setHorizontalHeaderLabels(["Latitude", "Longitude"])
        right_layout.addWidget(QLabel("Waypoints:"))
        right_layout.addWidget(self.waypoint_table)

        # Manual input
        self.lat_input = QLineEdit()
        self.lon_input = QLineEdit()
        self.add_button = QPushButton("Add Waypoint")
        self.add_button.clicked.connect(self.add_manual_waypoint)
        self.clear_button = QPushButton("Clear Waypoints")
        self.clear_button.clicked.connect(self.clear_waypoints)
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Lat:"))
        manual_layout.addWidget(self.lat_input)
        manual_layout.addWidget(QLabel("Lon:"))
        manual_layout.addWidget(self.lon_input)
        manual_layout.addWidget(self.add_button)
        manual_layout.addWidget(self.clear_button)
        right_layout.addLayout(manual_layout)

        # Send waypoints button
        self.send_button = QPushButton("Send Waypoints")
        self.send_button.clicked.connect(self.send_waypoints)
        right_layout.addWidget(self.send_button)

        # Rover control section
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_rover)
        right_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_rover)
        right_layout.addWidget(self.stop_button)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 100)
        self.speed_slider.setValue(50)
        self.speed_slider.valueChanged.connect(self.set_speed)
        right_layout.addWidget(QLabel("Speed:"))
        right_layout.addWidget(self.speed_slider)

        self.speed_label = QLabel("Speed: 50%")
        right_layout.addWidget(self.speed_label)

        # Rover status
        self.status_label = QLabel("Rover Position: N/A\nHeading: N/A\nAcceleration: N/A\nGyroscope: N/A\nMagnetometer: N/A\nTemperature: N/A\nWiFi Strength: N/A")
        right_layout.addWidget(self.status_label)

        right_panel.setLayout(right_layout)

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.map_view, 2)
        main_layout.addWidget(right_panel, 1)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def on_map_loaded(self, ok):
        if not ok:
            QMessageBox.critical(self, "Error", "Failed to load map")
        else:
            self.update_waypoint_table()

    def connect_to_rover(self):
        try:
            ip = self.ip_input.text()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, 80))
            self.connect_button.setText("Connected")
            self.connect_button.setEnabled(False)
            self.connection_status.setText("Connection: Connected")
            self.telemetry_thread = TelemetryThread(self.sock)
            self.telemetry_thread.telemetry_received.connect(self.on_telemetry_received)
            self.telemetry_thread.disconnected.connect(self.on_disconnected)
            self.telemetry_thread.start()
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {e}")
            self.sock = None
            self.connection_status.setText("Connection: Disconnected")

    def on_disconnected(self):
        self.connection_status.setText("Connection: Disconnected")
        self.connect_button.setText("Connect")
        self.connect_button.setEnabled(True)
        self.sock = None
        if self.telemetry_thread:
            self.telemetry_thread.terminate()

    def add_manual_waypoint(self):
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                self.map_view.page().runJavaScript(f"addWaypoint({lat}, {lon})")
                self.update_waypoint_table()
                self.lat_input.clear()
                self.lon_input.clear()
            else:
                QMessageBox.warning(self, "Invalid Input", "Latitude must be -90 to 90, Longitude -180 to 180")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for latitude and longitude")

    def clear_waypoints(self):
        self.map_view.page().runJavaScript("clearWaypoints()")
        self.update_waypoint_table()

    def send_waypoints(self):
        if not self.sock:
            QMessageBox.warning(self, "Connection Error", "Not connected to rover")
            return
        self.map_view.page().runJavaScript("getWaypoints()", self.handle_waypoints)

    def handle_waypoints(self, waypoints):
        try:
            data = {"waypoints": waypoints}
            self.sock.sendall(json.dumps(data).encode())
            QMessageBox.information(self, "Success", "Waypoints sent to rover")
        except Exception as e:
            QMessageBox.critical(self, "Send Error", f"Failed to send waypoints: {e}")

    def start_rover(self):
        if self.sock:
            self.send_command("start")
        else:
            QMessageBox.warning(self, "Connection Error", "Not connected to rover")

    def stop_rover(self):
        if self.sock:
            self.send_command("stop")
        else:
            QMessageBox.warning(self, "Connection Error", "Not connected to rover")

    def set_speed(self, value):
        if self.sock:
            self.send_command("set_speed", speed=value)
        self.speed_label.setText(f"Speed: {value}%")

    def send_command(self, command, **kwargs):
        data = {"command": command}
        data.update(kwargs)
        try:
            self.sock.sendall(json.dumps(data).encode())
        except Exception as e:
            QMessageBox.critical(self, "Send Error", f"Failed to send command: {e}")

    def on_telemetry_received(self, telemetry):
        try:
            lat = telemetry['lat']
            lon = telemetry['lon']
            heading = telemetry['heading']
            accel = telemetry['imu_data']['accel']
            gyro = telemetry['imu_data']['gyro']
            mag = telemetry['imu_data']['mag']
            temp = telemetry['temperature']
            wifi = telemetry['wifi_strength']
            self.map_view.page().runJavaScript(f"setRoverPosition({lat}, {lon})")
            status_text = f"Rover Position: {lat:.6f}, {lon:.6f}\n"
            status_text += f"Heading: {heading:.1f}°\n"
            status_text += f"Acceleration: {accel[0]:.2f}, {accel[1]:.2f}, {accel[2]:.2f}\n"
            status_text += f"Gyroscope: {gyro[0]:.2f}, {gyro[1]:.2f}, {gyro[2]:.2f}\n"
            status_text += f"Magnetometer: {mag[0]:.2f}, {mag[1]:.2f}, {mag[2]:.2f}\n"
            status_text += f"Temperature: {temp:.1f}°C\n"
            status_text += f"WiFi Strength: {wifi} dBm"
            self.status_label.setText(status_text)
        except KeyError as e:
            self.status_label.setText(f"Invalid telemetry data: missing {e}")

    def update_waypoint_table(self):
        self.map_view.page().runJavaScript("getWaypoints()", self.populate_waypoint_table)

    def populate_waypoint_table(self, waypoints):
        self.waypoint_table.setRowCount(len(waypoints))
        for i, wp in enumerate(waypoints):
            self.waypoint_table.setItem(i, 0, QTableWidgetItem(f"{wp['lat']:.6f}"))
            self.waypoint_table.setItem(i, 1, QTableWidgetItem(f"{wp['lng']:.6f}"))

    def closeEvent(self, event):
        if self.sock:
            self.sock.close()
        if self.telemetry_thread:
            self.telemetry_thread.terminate()
        event.accept()
```

### communication.py
Manages TCP communication, including a thread for receiving telemetry.

```python
import socket
import json
from PyQt5.QtCore import QThread, pyqtSignal

class TelemetryThread(QThread):
    telemetry_received = pyqtSignal(dict)
    disconnected = pyqtSignal()

    def __init__(self, sock):
        super().__init__()
        self.sock = sock

    def run(self):
        while True:
            try:
                data = self.sock.recv(1024)
                if not data:
                    self.disconnected.emit()
                    break
                telemetry = json.loads(data.decode())
                self.telemetry_received.emit(telemetry)
            except Exception as e:
                print(f"Error receiving telemetry: {e}")
                self.disconnected.emit()
                break
```

### utils.py
Contains utility functions for potential future enhancements.

```python
def normalize_angle(angle):
    angle = angle % 360
    if angle > 180:
        angle -= 360
    elif angle <= -180:
        angle += 360
    return angle
```

## Development Guidelines
1. **GUI Framework**: PyQt5 is chosen for its robust support for web views and Windows compatibility, ensuring a responsive and feature-rich interface ([PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)).
2. **Map Integration**: Leaflet.js with OpenStreetMap provides a lightweight, API-key-free solution for interactive maps, ideal for waypoint selection and rover tracking ([Leaflet.js Documentation](https://leafletjs.com/)).
3. **Communication**: Configure the rover’s TCP server to accept connections on port 80 and send telemetry as specified. Test connectivity using tools like `telnet` or `netcat` ([Python Socket Programming](https://docs.python.org/3/library/socket.html)).
4. **Threading**: Use `QThread` for telemetry reception to maintain GUI responsiveness, connecting signals to slots for thread-safe updates ([PyQt Threading Tutorial](https://www.pythonguis.com/tutorials/multithreading-pyqt-applications-qthread/)).
5. **Error Handling**: Implement robust validation for waypoint inputs and network operations, displaying user-friendly error messages via `QMessageBox`.
6. **Waypoint Limit**: Enforce a maximum of 10 waypoints in both the map’s JavaScript and GUI table to align with rover constraints.
7. **Deployment**: Bundle the application using PyInstaller, including `map.html` and any assets like custom marker icons ([PyInstaller](https://pyinstaller.org/)).

## Testing and Calibration
- **Map Testing**: Verify that clicking on the map adds waypoints (up to 10) and that manual entries appear correctly. Test JavaScript interactions by logging coordinates to the console.
- **Communication Testing**: Connect to the rover using a known IP address, send test waypoints, start/stop commands, and speed settings, and verify telemetry updates in the status label and map.
- **Error Handling**: Simulate connection failures (e.g., wrong IP), invalid waypoint inputs, and network disruptions to ensure clear error messages.
- **Performance**: Ensure the GUI remains responsive during telemetry updates, adjusting the thread’s polling rate (e.g., 1-second intervals) if necessary.
- **Telemetry Validation**: Confirm that the rover sends correctly formatted JSON telemetry, including all specified fields, and that the app displays them accurately.

## Potential Challenges
- **Network Reliability**: Cross-network communication (e.g., different WiFi networks) may require tools like ngrok for external access ([ngrok](https://ngrok.com/)). Test connectivity in various network conditions to ensure stability.
- **Map Loading**: Ensure `map.html` loads correctly and that internet access is available for map tiles. Consider offline tiles for robust operation ([Leaflet Offline](https://github.com/leaflet-extras/