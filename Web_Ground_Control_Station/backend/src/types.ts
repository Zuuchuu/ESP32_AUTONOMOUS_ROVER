/**
 * Vehicle State Types
 * Mirrors the telemetry structure from the ESP32 firmware.
 */

export interface AttitudeData {
    roll: number;
    pitch: number;
    yaw: number; // heading
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
    imu: boolean;
    gps: boolean;
    tof: boolean;
}

export interface TOFData {
    distance: number; // millimeters
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
    waypoints: Waypoint[];
    sensorStatus: SensorStatus;
    tofData: TOFData;
}

/**
 * Create default/initial vehicle state
 */
export function createInitialVehicleState(): VehicleState {
    return {
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
        waypoints: [],
        sensorStatus: {
            imu: false,
            gps: false,
            tof: false,
        },
        tofData: {
            distance: 0,
            status: false,
        },
    };
}
