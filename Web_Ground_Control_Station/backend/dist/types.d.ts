/**
 * Vehicle State Types
 * Mirrors the telemetry structure from the ESP32 firmware.
 */
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
    waypoints: Waypoint[];
    sensorStatus: SensorStatus;
    tofData: TOFData;
}
/**
 * Create default/initial vehicle state
 */
export declare function createInitialVehicleState(): VehicleState;
//# sourceMappingURL=types.d.ts.map