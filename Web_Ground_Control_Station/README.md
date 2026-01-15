# Web-Based Ground Control Station (GCS)

A modern, cross-platform Ground Control Station for the ESP32 Autonomous Rover.

## Features

- 🌐 **Web-Based**: Accessible from any modern browser (Chrome, Firefox, Safari)
- ⚡ **Real-Time**: Low-latency telemetry via WebSocket (Socket.IO)
- 🗺️ **Interactive Map**: Leaflet-based map with waypoint placement
- 🎮 **Dual Mode**: Mission mode and Manual control mode
- 📊 **Telemetry Dashboard**: Attitude indicator, compass, GPS status, system health

## Architecture

```
┌─────────────────┐     TCP      ┌─────────────────┐   WebSocket   ┌─────────────────┐
│   ESP32 Rover   │ ──────────── │  Node.js Backend│ ──────────────│  React Frontend │
│  (JSON/Mavlink) │              │  (Socket.IO)    │               │  (Browser)      │
└─────────────────┘              └─────────────────┘               └─────────────────┘
```

## Quick Start

### Prerequisites

- Node.js 18+ 
- npm 9+
- ESP32 Rover running and connected to the same network

### 1. Start the Backend

```bash
cd backend
npm install
npm run dev
```

The backend will start on `http://localhost:3001`.

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will start on `http://localhost:5173`.

### 3. Configure Rover Connection

Edit `backend/src/config.ts` to set your rover's IP address:

```typescript
ROVER_HOST: '192.168.1.100',  // Your rover's IP
ROVER_PORT: 8080,              // TCP port
```

Or use environment variables:
```bash
ROVER_HOST=192.168.1.100 ROVER_PORT=8080 npm run dev
```

## Project Structure

```
Web_Ground_Control_Station/
├── backend/                 # Node.js + TypeScript backend
│   ├── src/
│   │   ├── index.ts         # Main entry point
│   │   ├── config.ts        # Configuration
│   │   ├── types.ts         # TypeScript types
│   │   ├── roverConnection.ts  # TCP client for rover
│   │   ├── vehicleStore.ts  # In-memory state store
│   │   └── socketHandlers.ts   # WebSocket event handlers
│   ├── package.json
│   └── tsconfig.json
│
└── frontend/                # React + Vite + Tailwind frontend
    ├── src/
    │   ├── App.tsx          # Main application
    │   ├── components/      # UI components
    │   │   ├── AttitudeIndicator.tsx
    │   │   ├── Compass.tsx
    │   │   ├── GPSStatus.tsx
    │   │   ├── SystemStatus.tsx
    │   │   ├── MapView.tsx
    │   │   ├── ManualControl.tsx
    │   │   ├── MissionControl.tsx
    │   │   └── ModeToggle.tsx
    │   ├── hooks/
    │   │   └── useSocket.ts # Socket.IO client hook
    │   └── store/
    │       └── roverStore.ts # Zustand state store
    ├── package.json
    └── vite.config.ts
```

## Usage

### Mission Mode
1. Click on the map to add waypoints (up to 10)
2. Click "Upload Mission" to send waypoints to rover
3. Click "Start" to begin autonomous navigation
4. Monitor progress on the map and telemetry panels

### Manual Mode
1. Switch to "Manual" mode using the toggle
2. Click "Enable" to activate manual control
3. Use the D-pad or keyboard (WASD/Arrow keys) to control the rover
4. Adjust speed with the slider
5. Press Space or click STOP to stop immediately

## API Reference

### WebSocket Events (Frontend → Backend)

| Event | Payload | Description |
|-------|---------|-------------|
| `mission:upload` | `Waypoint[]` | Upload waypoints to rover |
| `mission:start` | - | Start mission |
| `mission:pause` | - | Pause mission |
| `mission:resume` | - | Resume mission |
| `mission:abort` | - | Abort mission |
| `mission:clear` | - | Clear waypoints |
| `manual:enable` | - | Enable manual mode |
| `manual:disable` | - | Disable manual mode |
| `manual:move` | `{direction, speed}` | Send movement command |

### WebSocket Events (Backend → Frontend)

| Event | Payload | Description |
|-------|---------|-------------|
| `state` | `VehicleState` | Full vehicle state (20Hz) |
| `connection:status` | `{connected: boolean}` | Rover connection status |

## Development

### Backend Development
```bash
cd backend
npm run dev   # Start with hot-reload
npm run build # Build for production
npm start     # Run production build
```

### Frontend Development
```bash
cd frontend
npm run dev     # Start dev server
npm run build   # Build for production
npm run preview # Preview production build
```

## Technology Stack

### Backend
- **Runtime**: Node.js 18+
- **Language**: TypeScript
- **Framework**: Express
- **WebSocket**: Socket.IO
- **Build Tool**: tsup/tsc

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Map**: React-Leaflet
- **WebSocket**: Socket.IO Client

## Future Improvements

- [ ] Mavlink protocol support (replacing JSON)
- [ ] Flight path history/track logging
- [ ] Video streaming integration
- [ ] Multiple rover support
- [ ] Mission file import/export
- [ ] 3D attitude visualization

## License

MIT
