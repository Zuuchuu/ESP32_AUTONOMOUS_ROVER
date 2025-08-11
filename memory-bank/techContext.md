# Tech Context: ESP32 Autonomous Rover & Control Station App

## Technologies Used
- **✅ ESP32 Development**: Arduino framework, FreeRTOS, C++17
- **✅ Hardware**: ESP32 30-pin DevKit, N20 DC motors, TB6612FNG motor driver, GY-87 10-DOF IMU, u-blox M10 GPS
- **✅ Communication**: WiFi (STA mode), TCP server on port 80, JSON protocol
- **✅ Sensors**: UART (GPS), I2C (IMU), PWM (Motors)
- **🎯 Desktop App**: Python 3.8+, PyQt5, PyQtWebEngine, Leaflet.js
- **✅ Development**: PlatformIO, taskmaster-ai, Cursor IDE

## Development Setup
- **✅ PlatformIO**: Successfully configured for ESP32 development
- **✅ Project Structure**: Modular architecture with include/ and src/ directories
- **✅ Hardware Abstraction**: MotorController and SensorManager classes implemented
- **✅ Task Management**: FreeRTOS tasks for WiFi, GPS, IMU, Navigation, Telemetry
- **✅ Build System**: Successful compilation with optimized memory usage

## Technical Constraints
- **✅ Memory**: ESP32 RAM optimized (14.1% usage)
- **✅ Flash**: ESP32 storage optimized (63.6% usage) 
- **✅ Real-time**: Navigation timing requirements met with FreeRTOS
- **🎯 Network**: WiFi reliability testing pending
- **✅ Thread Safety**: Mutex-protected shared data structures implemented

## Dependencies
- **✅ ESP32 Libraries**: 
  - ArduinoJson @ 7.4.2
  - TinyGPSPlus @ 1.1.0
  - Adafruit MPU6050 @ 2.2.6
  - Adafruit HMC5883 Unified @ 1.2.3
  - WiFi @ 2.0.0
  - Wire @ 2.0.0
  - Adafruit Unified Sensor @ 1.1.15
- **🎯 Python Libraries**: PyQt5, QWebEngineView, socket, json, threading
- **🎯 External**: Leaflet.js for map integration

## File Structure
```
ESP32_AUTONOMOUS_ROVER/
├── include/
│   ├── config/          # ✅ Configuration headers (pins, WiFi, system)
│   ├── core/            # ✅ Shared data structures with mutexes
│   ├── hardware/        # ✅ Hardware abstraction layer
│   └── tasks/           # ✅ Task headers (WiFi, GPS, IMU, Navigation, Telemetry)
├── src/
│   ├── core/            # ✅ SharedData implementation
│   ├── hardware/        # ✅ HAL implementations (MotorController, SensorManager)
│   ├── tasks/           # ✅ Task implementations
│   └── main.cpp         # ✅ Main entry point with FreeRTOS setup
├── CONTROL_STATION_APP/  # 🚀 Python desktop app
│   ├── core/, gui/, network/, mission/, utils/, assets/
│   ├── sim_rover.py     # 🚀 Local TCP simulator for testing
│   └── requirements.txt # PyQt5, PyQtWebEngine
├── memory-bank/         # ✅ Project documentation
├── .taskmaster/         # ✅ Task management configuration
└── platformio.ini       # ✅ Build configuration
```

## Build/Run Configuration
- **Platform**: Espressif 32 (6.12.0)
- **Board**: ESP32 DOIT DevKit V1
- **Framework**: Arduino
- **Toolchain**: xtensa-esp32-elf/8.4.0
- **Memory Usage**: RAM 14.1%, Flash 63.6%
- **Build Status**: ✅ ESP32 firmware builds; 🧪 Control app runs with Python 3.8+ (use `pip install -r CONTROL_STATION_APP/requirements.txt`)