# Product Context: ESP32 Autonomous Rover & Control Station App

## Why This Project Exists
This project addresses the need for a complete autonomous navigation solution that combines embedded robotics with modern desktop control interfaces. It serves engineers and hobbyists who want to experiment with autonomous vehicles without the complexity of industrial systems.

## Problems It Solves
- **Hardware Integration**: Provides a complete hardware-software solution for autonomous navigation
- **User Interface**: Offers an intuitive desktop application for mission planning and real-time control
- **Modularity**: Demonstrates scalable, maintainable architecture for embedded systems
- **Real-time Control**: Enables precise autonomous navigation with PID control and cross-track error correction

## How It Should Work
- **ESP32 Rover**: Connects to WiFi, receives waypoints via TCP, navigates autonomously using GPS/IMU data
- **Desktop App**: Provides map-based waypoint selection, real-time telemetry display, and manual control
- **Communication**: JSON protocol over TCP for reliable data exchange
- **Navigation**: PID-controlled differential steering with cross-track error correction

## User Experience Goals
- **Intuitive Control**: Click-to-add waypoints on interactive map
- **Real-time Feedback**: Live telemetry display with position, heading, and sensor data
- **Reliable Operation**: Robust error handling and connection management
- **Scalable Architecture**: Modular design for easy extension and maintenance

## Current Implementation Status
- **ESP32 Side**: Complete implementation with Hardware Abstraction Layer, all core tasks functional
- **Desktop App**: Core app modules implemented (`core`, `gui`, `network`, `mission`, `utils`, `assets/map.html`); testing/debugging in progress
- **Architecture**: Modular design with clear separation of concerns achieved
- **Integration**: Ready for end-to-end testing via ESP32 or the included simulator (`CONTROL_STATION_APP/sim_rover.py`)
