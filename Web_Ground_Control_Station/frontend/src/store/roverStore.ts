/**
 * Vehicle State Store (Zustand)
 * 
 * OPTIMIZED: Uses granular update functions to minimize object reference changes.
 * Only updates specific slices when their data actually changes.
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

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

export interface SensorStatus {
    accel: boolean;
    gyro: boolean;
    mag: boolean;
    gps: boolean;
    tof: boolean;
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
    waypoints?: Waypoint[];
}

export type ControlMode = 'mission' | 'manual';

interface RoverStore {
    vehicleState: VehicleState;
    waypoints: Waypoint[];
    controlMode: ControlMode;
    isSocketConnected: boolean;

    // Optimized: Single action for full state update from socket
    setVehicleState: (state: VehicleState) => void;

    // UI actions
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

// Shallow equality check for objects
function shallowEqual<T extends object>(a: T, b: T): boolean {
    const keysA = Object.keys(a);
    const keysB = Object.keys(b);
    if (keysA.length !== keysB.length) return false;
    for (const key of keysA) {
        if ((a as Record<string, unknown>)[key] !== (b as Record<string, unknown>)[key]) return false;
    }
    return true;
}

export const useRoverStore = create<RoverStore>()(
    subscribeWithSelector((set, get) => ({
        vehicleState: initialVehicleState,
        waypoints: [],
        controlMode: 'mission',
        isSocketConnected: false,

        setVehicleState: (newState) => {
            const current = get().vehicleState;

            // Filter out waypoints from backend
            const { waypoints: _, ...stateWithoutWaypoints } = newState;

            // OPTIMIZATION: Only update slices that actually changed
            const updates: Partial<VehicleState> = {};

            if (!shallowEqual(current.attitude, stateWithoutWaypoints.attitude)) {
                updates.attitude = stateWithoutWaypoints.attitude;
            }
            if (!shallowEqual(current.gps, stateWithoutWaypoints.gps)) {
                updates.gps = stateWithoutWaypoints.gps;
            }
            if (!shallowEqual(current.system, stateWithoutWaypoints.system)) {
                updates.system = stateWithoutWaypoints.system;
            }
            if (!shallowEqual(current.sensorStatus, stateWithoutWaypoints.sensorStatus)) {
                updates.sensorStatus = stateWithoutWaypoints.sensorStatus;
            }
            if (!shallowEqual(current.mission, stateWithoutWaypoints.mission)) {
                updates.mission = stateWithoutWaypoints.mission;
            }
            if (!shallowEqual(current.tofData, stateWithoutWaypoints.tofData)) {
                updates.tofData = stateWithoutWaypoints.tofData;
            }
            if (current.connected !== stateWithoutWaypoints.connected) {
                updates.connected = stateWithoutWaypoints.connected;
            }
            if (current.lastHeartbeat !== stateWithoutWaypoints.lastHeartbeat) {
                updates.lastHeartbeat = stateWithoutWaypoints.lastHeartbeat;
            }

            // IMU has nested calibration object - check separately
            if (stateWithoutWaypoints.imu) {
                const imuChanged = !shallowEqual(current.imu, stateWithoutWaypoints.imu) ||
                    !shallowEqual(current.imu.calibration, stateWithoutWaypoints.imu.calibration);
                if (imuChanged) {
                    updates.imu = stateWithoutWaypoints.imu;
                }
            }

            // Only set if something actually changed
            if (Object.keys(updates).length > 0) {
                set({
                    vehicleState: {
                        ...current,
                        ...updates,
                    }
                });
            }
        },

        setControlMode: (mode) => set({ controlMode: mode }),

        setSocketConnected: (connected) => set({ isSocketConnected: connected }),

        addWaypoint: (waypoint) => set((state) => ({
            waypoints: [...state.waypoints, waypoint],
        })),

        clearWaypoints: () => set({ waypoints: [] }),

        setWaypoints: (waypoints) => set({ waypoints }),
    }))
);
