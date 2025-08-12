# Project Brief: ESP32 Autonomous Rover & Control Station App

## Overview
This project aims to develop an autonomous robot rover based on the ESP32 30-pin DevKit, controlled via a Windows desktop application over WiFi. The system is designed for engineers and hobbyists with experience in embedded systems, robotics, and Python development.

## Core Requirements
- **Rover Hardware**: ESP32, N20 DC motors, TB6612FNG motor driver, GY-87 IMU, u-blox M10 GPS.
- **Rover Software**: Arduino framework with FreeRTOS, modular task-based architecture with Hardware Abstraction Layer, PID navigation, WiFi TCP server for communication.
- **Control Station App**: Python 3.8+ with PyQt5, interactive map (Leaflet.js), TCP client for sending waypoints/commands and receiving telemetry.

## Goals
- Enable waypoint-based autonomous navigation with real-time telemetry feedback.
- Provide a robust, user-friendly desktop interface for mission planning and manual control.
- Ensure modular, scalable, and maintainable codebases for both embedded and desktop components.

## Scope
- Hardware integration and configuration for all sensors and actuators.
- Real-time, thread-safe data sharing and task management on the ESP32.
- Desktop app with GUI for map-based waypoint selection, manual entry, rover control, and telemetry display.
- Communication protocol using JSON over TCP sockets.
- Documentation for setup, usage, and troubleshooting.

## Current Status
- **ESP32 Implementation**: Complete with modular architecture, Hardware Abstraction Layer, and all core tasks (WiFi, GPS, IMU, Navigation, Telemetry)
- **Architecture**: Successfully restructured with .h/.cpp separation, PlatformIO conventions, and clear separation of concerns
- **Desktop App**: Core implementation complete; testing/debugging pending
- **Integration**: Ready for end-to-end testing (use `CONTROL_STATION_APP/sim_rover.py` locally or connect to ESP32)
