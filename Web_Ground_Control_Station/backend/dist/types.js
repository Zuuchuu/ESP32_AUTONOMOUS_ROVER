"use strict";
/**
 * Vehicle State Types
 * Mirrors the telemetry structure from the ESP32 firmware.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createInitialVehicleState = createInitialVehicleState;
/**
 * Create default/initial vehicle state
 */
function createInitialVehicleState() {
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
//# sourceMappingURL=types.js.map