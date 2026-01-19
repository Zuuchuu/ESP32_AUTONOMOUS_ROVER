# Web Ground Control Station (Web GCS)

A professional, mission-critical interface for the ESP32 Autonomous Rover. Built with modern web technologies to provide real-time telemetry, mission planning, and manual control capabilities from any browser.

![React](https://img.shields.io/badge/Frontend-React%20v18-blue)
![Node](https://img.shields.io/badge/Backend-Node.js%20v18-green)
![Socket.IO](https://img.shields.io/badge/Comms-Socket.IO-black)
![Tailwind](https://img.shields.io/badge/Style-TailwindCSS-06b6d4)

---

## 🏗️ Architecture

The Web GCS acts as the bridge between the user and the autonomous rover. It consists of a high-performance Node.js backend handling TCP communication and a responsive React frontend for visualization.

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
│             (WiFiTask @ Port 80)                         │
└──────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🖥️ Instrument Cluster
- **Artificial Horizon**: Real-time visual representation of Pitch and Roll.
- **Digital Compass**: Heading indicator with cardinal directions.
- **Status Indicators**:
    - **GPS**: Fix status, HDOP, Satellite count.
    - **IMU**: Calibration confidence scores (System, Gyro, Accel, Mag).
    - **System**: WiFi RSSI, Battery Voltage, Uptime.

### 🗺️ Mission Control
- **Interactive Map**: Click-to-place waypoints on a global map.
- **Workflow**:
    1. **Plan**: Add waypoints graphically.
    2. **Upload**: Send mission to rover (validates connection).
    3. **Start**: Trigger autonomous navigation.
    4. **Monitor**: Watch progress (Current WP / Total WP, ETA).
- **Dynamic Controls**: Smart buttons that change based on state (Start -> Stop -> Resume).

### 🎮 Manual Control
- **Keyboard Drive**: Use `W`, `A`, `S`, `D` for directional control.
- **Safety**:
    - **Dead Man's Switch**: Rovers stops if key is released.
    - **Emergency Stop**: Spacebar sends immediate HALT command.
- **Speed Limiter**: Adjustable power output (0-100%) via slider.

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: v18 or higher
- **npm**: v9 or higher
- **Network**: Computer must be on the same WiFi network as the ESP32 Rover.

### 1. Backend Setup
The backend handles the persistent TCP connection to the rover.

```bash
cd backend
npm install

# Start development server
# Default connects to Rover at 192.168.1.100 (configurable)
npm run dev
```

**Configuration:**
Edit `backend/src/config.ts` or use Environment Variables:
```bash
ROVER_HOST="192.168.4.1" ROVER_PORT=80 npm run dev
```

### 2. Frontend Setup
The frontend provides the user interface.

```bash
cd frontend
npm install

# Start development server (Vite)
npm run dev
```
Open your browser to `http://localhost:5173`.

---

## 🔌 API Reference (Internal)

Communication between Frontend and Backend uses Socket.IO.

### Client -> Server Events

| Event | Payload | Description |
|-------|---------|-------------|
| `mission:upload` | `[{lat, lng}]` | Sends waypoint list to backend for formatting. |
| `mission:start` | `null` | Commands rover to begin mission. |
| `mission:pause` | `null` | Pauses current mission. |
| `mission:abort` | `null` | Stops mission and clears state. |
| `manual:enable` | `null` | Switches rover to MANUAL mode. |
| `manual:move` | `{direction, speed}` | Sends movement command (`forward`, `left`, etc). |

### Server -> Client Events

| Event | Payload | Description |
|-------|---------|-------------|
| `state` | `VehicleState` | Broadcasts full vehicle telemetry (~20Hz). |
| `mission:uploaded` | `{success, count}` | Confirmation of upload status. |

### Data Structures

**VehicleState Object**:
```typescript
interface VehicleState {
  connected: boolean;      // TCP connection status
  attitude: {
    roll: number;
    pitch: number;
    yaw: number;
  };
  mission: {
    active: boolean;
    currentWaypointIndex: number;
    distanceToWaypoint: number;
  };
  imu: {
    calibration: { system: number, ... }; // 0-3 confidence
  };
  // ... other telemetry
}
```

---

## 🛠️ Development

- **State Management**: `frontend/src/store/roverStore.ts` uses **Zustand** for centralized state.
- **Styling**: **TailwindCSS** with custom glass-morphism classes in `index.css`.
- **Map**: **React-Leaflet** for map rendering.

---

*Part of the ESP32 Autonomous Rover Project*
