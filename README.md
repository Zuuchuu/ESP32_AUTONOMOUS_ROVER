# ESP32 Autonomous Rover

A sophisticated autonomous navigation system featuring ESP32 firmware with BNO055 IMU integration, and a modern **Web-Based Ground Control Station (GCS)** for mission planning and real-time telemetry.

![Project Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Platform](https://img.shields.io/badge/Platform-ESP32-blue)
![Web GCS](https://img.shields.io/badge/GCS-React%20%2B%20Node.js-blueviolet)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Hardware Setup](#-hardware-setup)
- [Software Components](#-software-components)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [Communication Protocol](#-communication-protocol)
- [Development](#-development)

---

## 🚀 Overview

The ESP32 Autonomous Rover is a production-ready robotics platform designed for precision navigation. It integrates advanced sensor fusion (BNO055 9-DOF IMU) with a robust FreeRTOS-based firmware and a professional web interface.

### Key Features
- **🌐 Web Ground Control Station**: Modern React/Node.js interface accessible from any browser.
- **🎯 Precision Navigation**: GPS waypoint navigation with Cross-Track Error (XTE) correction.
- **🧭 Advanced IMU Fusion**: BNO055 sensor fusion with NVS-backed automatic calibration storage.
- **🎮 Dual Control Mode**: Seamless switching between Autonomous Missions and Manual Control.
- **🖥️ OLED Status Display**: On-rover display for IP address, calibration status, and mission state.
- **📡 Real-Time Telemetry**: High-frequency JSON telemetry over TCP/WiFi.

---

## 🏗️ System Architecture

The system consists of three main layers: the ESP32 Firmware (Hardware Layer), the Node.js Backend (Communication Layer), and the React Frontend (User Interface Layer).

```
┌─────────────────────────────────────────────────────────────┐
│                 WEB GROUND CONTROL STATION                  │
│                                                             │
│  ┌──────────────────┐             ┌──────────────────────┐  │
│  │  React Frontend  │◄───────────►│   Node.js Backend    │  │
│  │     (Browser)    │  WebSocket  │ (Express/Socket.IO)  │  │
│  └──────────────────┘             └──────────┬───────────┘  │
└──────────────────────────────────────────────┼──────────────┘
                                               │ TCP / JSON
                                               │
┌──────────────────────────────────────────────▼───────────┐
│                      ESP32 ROVER                         │
│                                                          │
│  ┌──────────────┐      ┌────────────┐   ┌─────────────┐  │
│  │  WiFi Task   │◄────►│ SharedData │◄──│  IMU Task   │  │
│  └──────┬───────┘      └──────┬─────┘   └─────────────┘  │
│         │                     │                          │
│         │              ┌──────▼─────┐   ┌─────────────┐  │
│         ├─────────────►│ Telemetry  │   │ Display Task│  │
│         │              └───┬────────┘   └─────────────┘  │
│  ┌──────▼───────┐          │                             │
│  │  NAV / PID   │◄─────────┘                             │
│  └──────┬───────┘                                        │
│         │                                                │
│  ┌──────▼───────┐                                        │
│  │   MOTORS     │                                        │
│  └──────────────┘                                        │
└──────────────────────────────────────────────────────────┘
```

### ESP32 Firmware Tasks (FreeRTOS)
- **WiFi Task**: TCP Server (Port 80), handles command parsing.
- **Navigation Task**: Path planning, PID control, Waypoint logic.
- **IMU Task**: BNO055 sensor fusion, calibration management (NVS storage).
- **Telemetry Task**: Aggregates sensor data (1Hz) and sends to GCS.
- **Display Task**: Updates OLED with system health and status.
- **Encoder/TOF Tasks**: Odometry and obstacle detection.

---

## 🔧 Hardware Setup

### Core Components
| Component | Function | Interface |
|-----------|----------|-----------|
| **ESP32 DevKit** | Main Controller | N/A |
| **BNO055** | 9-DOF IMU (Absolute Orientation) | I2C (0x28) |
| **u-blox M10 GPS** | Positioning | UART |
| **SSD1306 OLED** | Status Display | I2C (0x3C) |
| **TB6612FNG** | Dual Motor Driver | PWM/GPIO |
| **N20 Motors** | Drive with Encoders | GPIO |

### Wiring Diagram
```
ESP32 Pins:
├── I2C Bus (SDA: 21, SCL: 22)
│   ├── BNO055 IMU
│   ├── SSD1306 OLED
│   └── VL53L0X TOF (Optional)
├── GPS (UART)
│   ├── TX → GPIO 16 (RX)
│   └── RX → GPIO 17 (TX)
├── Motors (TB6612FNG)
│   ├── Left: PWM=14, IN1=26, IN2=27
│   └── Right: PWM=32, IN1=25, IN2=33
└── Encoders
    ├── Left: A=18, B=19
    └── Right: A=5, B=4
```

---

## 💻 Software Components

### 1. ESP32 Firmware (`/src`)
The firmware is built with PlatformIO. It features a thread-safe `SharedData` struct for inter-task communication.
- **IMU Calibration**: Calibration data is automatically saved to Non-Volatile Storage (NVS) when the system detects full calibration (System=3, Gyro=3, Accel=3, Mag=3). It is reloaded on boot.
- **OLED Interface**: Cycles through info screens including WiFi IP, Mission State, and detailed IMU Calibration scores.

### 2. Web Ground Control Station (`/Web_Ground_Control_Station`)
A full-stack web application replacing the legacy Python interface.
- **Backend (`/backend`)**: Node.js + Express + Socket.IO. Acts as a bridge between the Browser and the Rover via TCP.
- **Frontend (`/frontend`)**: React + Vite + TailwindCSS. Renders the interactive map, instrument cluster, and control panels.

---

## 🚀 Quick Start

### 1. Flash Firmware
1. Open project in VS Code with PlatformIO extension.
2. Edit `include/config/wifi_config.h` with your WiFi credentials.
3. Build and Upload:
   ```bash
   pio run --target upload
   pio device monitor
   ```
4. Note the **IP Address** shown on the OLED Display or Serial Monitor.

### 2. Start Web GCS
**Backend:**
```bash
cd Web_Ground_Control_Station/backend
npm install
# Configure IP in src/config.ts or via ENV
ROVER_HOST=<ROVER_IP> npm run dev
```

**Frontend:**
```bash
cd Web_Ground_Control_Station/frontend
npm install
npm run dev
```
Access the GCS at `http://localhost:5173`.

---

## 📖 Usage Guide

### Mission Planning
1. Go to the **Mission** tab in the Web GCS.
2. Click on the map to place waypoints.
3. Click **"Upload Mission"** to send the plan to the rover.
4. Click **"Start"** to begin autonomous navigation.

### Manual Control
1. Switch to the **Manual** tab.
2. Toggle **"Enable Manual Control"** (this pauses any active mission).
3. Use **WASD** or the on-screen D-Pad to drive.
4. Adjust speed using the slider.

### IMU Calibration
For best navigation accuracy, the BNO055 must be calibrated:
1. **Gyro**: Keep rover still for 2-3 seconds.
2. **Magnetometer**: Move rover in a "Figure-8" pattern in the air.
3. **Accelerometer**: Rotate rover 45° around various axes.
4. Watch the **Calibration Status** on the Web GCS or OLED. Once 3/3 on all sensors, data is saved.

---

## 📡 Communication Protocol

The rover uses a JSON-based protocol over TCP (Port 80).

### Telemetry Object (Rover -> GCS)
```json
{
  "lat": 37.7749, 
  "lon": -122.4194,
  "heading": 180.5,
  "system_status": "operational",
  "imu_data": {
    "roll": 1.2,
    "pitch": -0.5,
    "quaternion": [0.99, 0.01, 0.0, 0.0],
    "calibration": {
      "sys": 3, "gyro": 3, "accel": 3, "mag": 3
    }
  },
  "wifi_strength": -45
}
```

### Commands (GCS -> Rover)
```json
// Start Mission
{"command": "start_mission", "waypoints": [...]}

// Manual Move
{"command": "manual_move", "direction": "forward", "speed": 75}
```

---

## 🛠️ Development

- **Firmware**: Modify `src/config/config.h` to tune PID values (`PID_KP`, `PID_KI`, `PID_KD`) and navigation thresholds.
- **Web App**: The frontend uses `zustand` for state management. `useSocket.ts` handles real-time data sync.

---

*Verified for Firmware v1.0 & Web GCS v1.0*