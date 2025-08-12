## Active Context - ESP32 Autonomous Rover & Control Station App

Last Updated: 2025-08-12

Source: [.cursorrules](mdc:.cursorrules)

### Overview
- **Embedded (ESP32, FreeRTOS)**: Modular tasks for WiFi, GPS, IMU, Navigation, Telemetry. Shared state via `core/SharedData` with mutexes. HAL provided by `hardware/MotorController` and `hardware/SensorManager`.
- **Desktop (Python, PyQt5 + PyQtWebEngine)**: Modules under `core/`, `gui/`, `network/`, `mission/`, `utils/`. Mission planning and progress UI centered in `gui/main_window.py`. Map in `assets/map.html`.
- **Comms**: JSON over TCP, default port 80. Control Station sends waypoints/commands; rover streams telemetry.

### Critical implementation paths
- **ESP32**
  - Entry: [`src/main.cpp`](mdc:src/main.cpp)
  - Tasks: headers in `include/tasks/*.h`, implementations in `src/tasks/*.cpp`
  - Shared data: [`include/core/SharedData.h`](mdc:include/core/SharedData.h), [`src/core/SharedData.cpp`](mdc:src/core/SharedData.cpp)
  - HAL: [`include/hardware/MotorController.h`](mdc:include/hardware/MotorController.h), [`include/hardware/SensorManager.h`](mdc:include/hardware/SensorManager.h)
- **Desktop app**
  - Bootstrap: [`CONTROL_STATION_APP/main.py`](mdc:CONTROL_STATION_APP/main.py)
  - Coordinator/UI: [`CONTROL_STATION_APP/gui/main_window.py`](mdc:CONTROL_STATION_APP/gui/main_window.py)
  - Services/Models: [`CONTROL_STATION_APP/core/services.py`](mdc:CONTROL_STATION_APP/core/services.py), [`CONTROL_STATION_APP/core/models.py`](mdc:CONTROL_STATION_APP/core/models.py)
  - Networking: [`CONTROL_STATION_APP/network/client.py`](mdc:CONTROL_STATION_APP/network/client.py), [`CONTROL_STATION_APP/network/telemetry.py`](mdc:CONTROL_STATION_APP/network/telemetry.py)
  - Mission logic: `CONTROL_STATION_APP/mission/*.py`
  - Map/UI assets: [`CONTROL_STATION_APP/assets/map.html`](mdc:CONTROL_STATION_APP/assets/map.html), styles in [`CONTROL_STATION_APP/gui/styles.py`](mdc:CONTROL_STATION_APP/gui/styles.py)

### Operational notes
- **Firmware build**: PlatformIO (board: esp32doit-devkit-v1). Typical: `pio run -t upload` (ensure correct port) or use VS Code PlatformIO tasks.
- **Desktop app deps**: Install via `pip install -r CONTROL_STATION_APP/requirements.txt`.
- **Run Control Station**: `python CONTROL_STATION_APP/main.py`.
- **Networking**: Default TCP port 80; allow through Windows firewall.

### Known mismatches / caveats
- **Outdated README pathing**: [`CONTROL_STATION_APP/README.md`](mdc:CONTROL_STATION_APP/README.md) shows older flat layout; actual structure is modular under `core/`, `gui/`, `network/`, `mission`, `utils`.
- **Simulator**: Docs reference `CONTROL_STATION_APP/sim_rover.py` which is currently not present.
- **Task Master**: Memory mentions a `.taskmaster/` folder; not present—ignore unless we adopt Task Master locally.

### Future helpful additions
- Add a lightweight TCP simulator (`sim_rover.py`) to mirror telemetry and mission commands for offline testing.
- Align README with the current app structure and mission workflow.

### Current focus
- Memory bank initialized from `.cursorrules`. Keep this file and `progress.md` updated after significant code/UI changes.

# Active Context: ESP32 Autonomous Rover & Control Station App

## Current Work Focus
- **✅ Completed**: ESP32 rover firmware implementation with successful compilation
- **✅ Completed**: ESP32 rover tasks marked as done (Tasks 1-5)
- **🚀 In Progress**: Control Station App testing and debugging
- **✅ Completed**: Core Python application structure and implementation
- **🎯 Next**: End-to-end testing with ESP32 and with local simulator (`CONTROL_STATION_APP/sim_rover.py`)

## Recent Changes
- **✅ Task Status Update**: Marked ESP32 rover tasks (1-5) as completed
- **✅ PRD Update**: Updated project requirements document with current status
- **✅ Control Station Structure**: Created complete CONTROL_STATION_APP directory
- **✅ Core Implementation**: Built all essential Python modules:
  - `main.py`: Application entry point and app wiring
  - `gui/main_window.py`, `gui/panels.py`, `gui/styles.py`: Complete GUI with modern PyQt5 interface and map widget
  - `network/client.py`, `network/telemetry.py`: Robust TCP client and threaded telemetry processor
  - `mission/*`: Planning, optimization, trajectory, visualization
  - `utils/config.py`, `utils/helpers.py`: Config manager and utilities
  - `assets/map.html`: Full Leaflet.js interactive map
  - `README.md` & `requirements.txt`: Complete documentation
  - `sim_rover.py`: Local TCP simulator for development/testing

## Control Station App Implementation Details
### GUI Architecture
- **Main Window**: Professional interface with splitter layout (70% map, 30% controls)
- **Map Panel**: Interactive Leaflet.js map with waypoint management and rover tracking
- **Control Panel**: Organized sections for connection, waypoints, rover control, and telemetry
- **Modern Styling**: CSS-styled PyQt5 components with hover effects and proper spacing

### Key Features Implemented
- **Connection Management**: IP/Port inputs, connect/disconnect, status monitoring
- **Waypoint System**: Click-to-add on map, manual entry, tables, clear all
- **Mission Workflow**: Plan mission, start/pause/abort, progress and metrics
- **Real-time Telemetry**: Position, heading, IMU data, temperature, WiFi strength
- **Map Controls**: Center on rover, fit all content, waypoint markers
- **Error Handling**: Input validation, connection error messages, user guidance

### Technical Implementation
- **Threading**: QThread for telemetry reception to keep GUI responsive
- **Communication**: JSON protocol over TCP with proper error handling
- **Map Integration**: JavaScript-Python interaction via QWebEngineView
- **Data Validation**: Comprehensive input validation for coordinates and IP addresses
- **Simulation**: Local simulator `sim_rover.py` emits line-delimited JSON telemetry and accepts mission commands
- **Memory Management**: Proper resource cleanup and connection management

## Next Steps
1. **Test with Simulator**: `python CONTROL_STATION_APP/sim_rover.py --host 127.0.0.1 --port 8080`; connect app to 127.0.0.1:8080
2. **Debug Issues**: Fix any import errors, UI issues, or functionality problems
3. **End-to-End Testing**: Connect to ESP32 rover and test full communication
4. **Integration Validation**: Verify mission send (`start_mission`), telemetry reception, progress updates
5. **Documentation Updates**: Add any discovered requirements or setup notes

## Active Decisions and Patterns
- **✅ Modular Architecture**: Clean separation between GUI, communication, and utilities
- **✅ Modern GUI**: PyQt5 with CSS styling for professional appearance
- **✅ Robust Communication**: Threaded TCP client with proper error handling
- **✅ Interactive Map**: Full-featured Leaflet.js with OpenStreetMap tiles
- **✅ JSON Protocol**: Consistent with ESP32 rover implementation
- **🎯 Testing Strategy**: Progressive testing from GUI to communication to integration

## Project Organization
```
ESP32_AUTONOMOUS_ROVER/
├── ✅ ESP32 Firmware (include/, src/, platformio.ini)
├── 🚀 CONTROL_STATION_APP/ (Complete Python implementation)
├── 📋 .taskmaster/ (Project management)
└── 📚 memory-bank/ (Documentation)
```

## Current Blocking Issues
- **None**: Core implementation complete, ready for testing phase