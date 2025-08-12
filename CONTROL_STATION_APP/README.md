# ESP32 Rover Control Station (Modular)

Windows desktop application for controlling and monitoring an ESP32-based autonomous rover. Built with Python 3.8+ and PyQt5, featuring an interactive map interface and real-time telemetry display.

## Features

- **Interactive Map**: Click-to-add waypoints using Leaflet.js and OpenStreetMap
- **Real-time Telemetry**: Live position tracking, IMU data, temperature, and WiFi status
- **Rover Control**: Start/stop navigation, speed adjustment (0-100%)
- **Waypoint Management**: Up to 10 waypoints with manual entry and map selection
- **TCP Communication**: JSON-based protocol for reliable rover communication
- **Error Handling**: Comprehensive validation and user-friendly error messages

## Requirements

- **Operating System**: Windows 7/8/10/11
- **Python**: 3.8 or later
- **Internet Connection**: Required for map tiles (OpenStreetMap)
- **ESP32 Rover**: Must be running compatible firmware with TCP server on port 80

## Installation

1. **Install Python** (if not already installed):
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure Python is added to your PATH during installation

2. **Install dependencies**:
   ```bash
   cd CONTROL_STATION_APP
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python --version  # Should show Python 3.8+
   python -c "import PyQt5; print('PyQt5 installed successfully')"
   ```

## Quick Start

1. **Power on your ESP32 rover** and note its IP address from the Serial monitor

2. **Launch the application**:
   ```bash
   python main.py
   ```

3. **Connect to rover**:
   - Enter the rover's IP address in the connection field
   - Click "Connect" button
   - Wait for "Status: Connected" confirmation

4. **Plan a mission**:
   - Click on the map to add waypoints (up to 10)
   - Or manually enter coordinates in the Lat/Lng fields
   - Click "Send Waypoints to Rover"

5. **Start navigation**:
   - Adjust speed using the slider (0-100%)
   - Click "Start Navigation"
   - Monitor real-time telemetry and rover position on map
   - Use "Stop Navigation" when needed

## User Interface

### Left Panel: Interactive Map
- **Waypoint Selection**: Click anywhere on the map to add waypoints
- **Rover Tracking**: Red marker shows rover's current position and heading
- **Map Controls**: 
  - "Center on Rover": Centers map view on rover location
  - "Fit All": Adjusts zoom to show all waypoints and rover

### Right Panel: Control Interface

#### Connection Section
- **IP Address Input**: Enter rover's IP address (e.g., 192.168.1.100)
- **Connect/Disconnect**: Establish or terminate TCP connection
- **Status Display**: Shows current connection status

#### Waypoint Management
- **Waypoint Table**: Lists all waypoints with coordinates
- **Manual Entry**: Add waypoints by entering latitude/longitude
- **Clear All**: Remove all waypoints from map and rover
- **Send to Rover**: Transmit waypoint list to rover

#### Rover Control
- **Start/Stop Navigation**: Control autonomous navigation
- **Speed Slider**: Adjust rover speed (0-100%)
- **Real-time Speed**: Current speed setting display

#### Telemetry Display
- **Position**: Current GPS coordinates (latitude, longitude)
- **Heading**: Compass heading in degrees (0-360°)
- **IMU Data**: Acceleration, gyroscope, and magnetometer readings
- **System Info**: Temperature and WiFi signal strength

## Communication Protocol

The application communicates with the ESP32 rover using TCP sockets on port 80 with JSON messages:

### Commands Sent to Rover
```json
# Send waypoints
{"waypoints": [{"lat": 37.7749, "lon": -122.4194}, ...]}

# Start navigation
{"command": "start"}

# Stop navigation  
{"command": "stop"}

# Set speed (0-100%)
{"command": "set_speed", "speed": 75}
```

### Telemetry Received from Rover
```json
{
  "lat": 37.774929,
  "lon": -122.419416,
  "heading": 45.5,
  "imu_data": {
    "accel": [0.1, 0.2, 9.8],
    "gyro": [0.01, -0.02, 0.0],
    "mag": [23.4, -12.1, 45.7]
  },
  "temperature": 24.5,
  "wifi_strength": -45
}
```

## Troubleshooting

### Connection Issues
- **"Connection timeout"**: Check rover IP address and ensure rover is powered on
- **"Connection refused"**: Verify rover's TCP server is running on port 80
- **"Invalid IP address"**: Ensure IP format is correct (e.g., 192.168.1.100)

### Map Issues
- **Map doesn't load**: Check internet connection for OpenStreetMap tiles
- **Waypoints not appearing**: Wait for map to fully load before clicking
- **JavaScript errors**: Refresh by restarting the application

### Rover Communication
- **No telemetry data**: Check rover firmware is sending JSON telemetry
- **Waypoints not received**: Verify JSON format matches rover expectations
- **Commands ignored**: Ensure rover is processing TCP commands correctly

### Network Configuration
- **Cross-network access**: Use tools like ngrok for external network access
- **Firewall issues**: Ensure Windows Firewall allows Python/PyQt5 network access
- **Router settings**: Check that router allows communication between devices

## File Structure (current)

```
CONTROL_STATION_APP/
├── main.py                     # Application entry point
├── core/
│   ├── models.py               # Data models and application state
│   └── services.py             # ApplicationService (business logic)
├── gui/
│   ├── main_window.py          # Main window and workflow sections
│   ├── panels.py               # Map widget and modular panels
│   └── styles.py               # Styling/theming
├── mission/
│   ├── planner.py              # Mission planning and progress
│   ├── algorithms.py           # Path planning/optimizer helpers
│   ├── path_optimizer.py       # Path smoothing and constraints
│   ├── trajectory.py           # Trajectory utilities
│   └── visualizer.py           # JS generation for map overlays
├── network/
│   ├── client.py               # TCP client and command API
│   └── telemetry.py            # Telemetry background processor
├── utils/
│   ├── config.py               # JSON configuration manager
│   └── helpers.py              # Math/GPS utilities
├── assets/
│   └── map.html                # Leaflet map
├── config.json                 # App configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This documentation
```

## Development Notes

- **Threading**: Telemetry reception runs in a separate QThread to keep GUI responsive
- **Error Handling**: Comprehensive validation for all user inputs and network operations
- **Cross-platform**: While designed for Windows, should work on Linux/macOS with minor modifications
- **Extensibility**: Modular design allows easy addition of new features

## Future Enhancements

- Offline map support for areas without internet connectivity
- Mission save/load functionality for repeated routes
- Multi-rover support for fleet management
- Enhanced telemetry visualization with graphs and charts
- Advanced path planning with obstacle avoidance
- Integration with weather data and GPS accuracy indicators

## Support

For issues related to:
- **ESP32 firmware**: See project-level `ESP32_Rover.md`
- **Hardware setup**: Check wiring and component specifications
- **Application bugs**: Review error messages and check Python/PyQt5 versions
- **Network configuration**: Ensure Windows Firewall allows Python; rover TCP on port 80

## License

This project is part of the ESP32 Autonomous Rover system. See main project documentation for licensing information.
