# System Patterns: ESP32 Autonomous Rover & Control Station App

## System Architecture
- **Rover (ESP32)**: ✅ **Complete** - Modular, task-based design using FreeRTOS with Hardware Abstraction Layer (HAL). Each major function (WiFi, GPS, IMU, Navigation, Telemetry) runs in its own task, sharing data via mutex-protected structures. Hardware control abstracted through MotorController and SensorManager classes.
- **Control Station App**: 🚀 **Implemented (Testing Phase)** - Modular Python application using PyQt5 for GUI and QWebEngineView for map integration. Networking via `network/client.py` and threaded telemetry in `network/telemetry.py`. Interactive map in `assets/map.html` with Leaflet.js.

## Key Technical Decisions
- **✅ FreeRTOS on ESP32**: Successfully implemented real-time, concurrent operation
- **✅ Hardware Abstraction Layer**: MotorController and SensorManager classes fully implemented
- **✅ Modular Architecture**: Clear separation with .h/.cpp files in include/src/ structure
- **✅ TCP Sockets & JSON**: Protocol implemented and ready for testing
- **🎯 Leaflet.js Map**: Integrated via QWebEngineView (`gui/panels.py` → `MapWidget`)
- **✅ Threading**: QThread-based telemetry receiver implemented (`network/telemetry.py`)
- **✅ Mutexes**: Successfully implemented on ESP32 for shared data protection

## Component Relationships
- **✅ ESP32 Internal**: All tasks communicate via SharedData with mutex protection
- **✅ HAL Layer**: Tasks use MotorController and SensorManager for hardware access
- **🎯 Rover <-> App**: TCP socket connection implemented (`network/client.py`); simulator available (`sim_rover.py`)
- **🎯 App <-> Map**: JavaScript/Python interaction via QWebEngineView implemented (`MapWidget` bridging and polling)
- **✅ Task Communication**: Producer-consumer pattern between sensor tasks and navigation

## Design Patterns Implemented
- **✅ Hardware Abstraction Pattern**: Clean separation between task logic and hardware specifics
- **✅ Singleton Pattern**: SharedData instance for global state management
- **✅ Producer-Consumer**: Sensor tasks produce data, navigation consumes it
- **✅ Configuration Pattern**: Centralized config files for pins and system parameters
- **✅ Task-Based Concurrency**: FreeRTOS tasks with proper synchronization
- **🎯 MVC Pattern**: Planned for desktop app (Model-View-Controller)

## Code Quality Patterns
- **✅ RAII**: Proper resource management in C++ classes
- **✅ Const Correctness**: Appropriate use of const in method signatures
- **✅ Memory Management**: Stack-based allocation, minimal dynamic allocation
- **✅ Error Handling**: Comprehensive error checking and logging
- **✅ Documentation**: Clear code structure and commenting

## Integration Patterns
- **✅ Compilation Success**: All modules integrate successfully
- **✅ Memory Efficiency**: Optimized for ESP32 constraints
- **✅ Library Integration**: Successfully integrated third-party libraries
- **✅ Build System**: PlatformIO configuration optimized
- **🎯 Network Integration**: Ready for TCP communication testing