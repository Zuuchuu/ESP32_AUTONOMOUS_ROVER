/**
 * Vehicle State Store (Zustand)
 * 
 * Global state management for rover telemetry.
 */

import { create } from 'zustand';

// Types matching backend
export interface AttitudeData {
    roll: number;
    pitch: number;
    yaw: number;
}

export interface GPSData {
    latitude: number;
    longitude: number;
    altitude: number;
    satellites: number;
    hdop: number;
    fix: boolean;
}

export interface IMUCalibration {
    system: number;
    gyroscope: number;
    accelerometer: number;
    magnetometer: number;
}

export interface IMUData {
    roll: number;
    pitch: number;
    quaternion: [number, number, number, number];
    accel: [number, number, number];
    gyro: [number, number, number];
    mag: [number, number, number];
    linearAccel: [number, number, number];
    gravity: [number, number, number];
    calibration: IMUCalibration;
    temperature: number;
}

export interface SystemStatus {
    batteryVoltage: number;
    wifiStrength: number;
    mode: 'MANUAL' | 'AUTO' | 'IDLE';
    armed: boolean;
    uptime: number;
}

// Sensor connection status
export interface SensorStatus {
    accel: boolean;  // Accelerometer
    gyro: boolean;   // Gyroscope
    mag: boolean;    // Magnetometer
    gps: boolean;    // GPS
    tof: boolean;    // Time-of-Flight
}

export interface TOFData {
    distance: number;
    status: boolean;
}

export interface Waypoint {
    id: number;
    lat: number;
    lng: number;
    altitude?: number;
    reached?: boolean;
}

export interface MissionStatus {
    active: boolean;
    currentWaypointIndex: number;
    totalWaypoints: number;
    distanceToWaypoint: number;
    totalDistance: number;
    estimatedTimeRemaining: number;
}

export interface VehicleState {
    connected: boolean;
    lastHeartbeat: number;
    attitude: AttitudeData;
    gps: GPSData;
    imu: IMUData;
    system: SystemStatus;
    mission: MissionStatus;
    sensorStatus: SensorStatus;
    tofData: TOFData;
    waypoints?: Waypoint[]; // Optional - backend sends but we filter it out
}

export type ControlMode = 'mission' | 'manual';

interface RoverStore {
    // Vehicle state from backend
    vehicleState: VehicleState;

    // Waypoints managed separately to prevent backend overwrites
    waypoints: Waypoint[];

    // UI state
    controlMode: ControlMode;
    isSocketConnected: boolean;

    // Actions
    setVehicleState: (state: VehicleState) => void;
    setControlMode: (mode: ControlMode) => void;
    setSocketConnected: (connected: boolean) => void;
    addWaypoint: (waypoint: Waypoint) => void;
    clearWaypoints: () => void;
    setWaypoints: (waypoints: Waypoint[]) => void;
}

const initialVehicleState: VehicleState = {
    connected: false,
    lastHeartbeat: 0,
    attitude: { roll: 0, pitch: 0, yaw: 0 },
    gps: {
        latitude: 0,
        longitude: 0,
        altitude: 0,
        satellites: 0,
        hdop: 99,
        fix: false,
    },
    imu: {
        roll: 0,
        pitch: 0,
        quaternion: [1, 0, 0, 0],
        accel: [0, 0, 0],
        gyro: [0, 0, 0],
        mag: [0, 0, 0],
        linearAccel: [0, 0, 0],
        gravity: [0, 0, 9.8],
        calibration: { system: 0, gyroscope: 0, accelerometer: 0, magnetometer: 0 },
        temperature: 0,
    },
    system: {
        batteryVoltage: 0,
        wifiStrength: 0,
        mode: 'IDLE',
        armed: false,
        uptime: 0,
    },
    mission: {
        active: false,
        currentWaypointIndex: 0,
        totalWaypoints: 0,
        distanceToWaypoint: 0,
        totalDistance: 0,
        estimatedTimeRemaining: 0,
    },
    sensorStatus: {
        accel: false,
        gyro: false,
        mag: false,
        gps: false,
        tof: false,
    },
    tofData: {
        distance: 0,
        status: false,
    },
};

export const useRoverStore = create<RoverStore>((set) => ({
    vehicleState: initialVehicleState,
    waypoints: [],
    controlMode: 'mission',
    isSocketConnected: false,

    setVehicleState: (state) => {
        // Filter out waypoints from backend to prevent overwrites
        const { waypoints: _, ...stateWithoutWaypoints } = state;
        set({ vehicleState: stateWithoutWaypoints });
    },

    setControlMode: (mode) => set({ controlMode: mode }),

    setSocketConnected: (connected) => set({ isSocketConnected: connected }),

    addWaypoint: (waypoint) => set((state) => ({
        waypoints: [...state.waypoints, waypoint],
    })),

    clearWaypoints: () => set({ waypoints: [] }),

    setWaypoints: (waypoints) => set({ waypoints }),
}));
