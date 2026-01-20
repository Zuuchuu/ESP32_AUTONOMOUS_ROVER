"use strict";
/**
 * Rover Connection Manager
 *
 * Handles TCP connection to the ESP32 Rover.
 * Currently supports the existing JSON protocol.
 * TODO: Migrate to Mavlink binary protocol.
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.RoverConnection = void 0;
const net = __importStar(require("net"));
const events_1 = require("events");
const config_js_1 = require("./config.js");
class RoverConnection extends events_1.EventEmitter {
    host;
    port;
    socket = null;
    reconnectTimer = null;
    buffer = '';
    _isConnected = false;
    constructor(host = config_js_1.config.ROVER_HOST, port = config_js_1.config.ROVER_PORT) {
        super();
        this.host = host;
        this.port = port;
    }
    get isConnected() {
        return this._isConnected;
    }
    /**
     * Attempt to connect to the rover
     */
    connect() {
        if (this.socket) {
            this.disconnect();
        }
        console.log(`[RoverConnection] Connecting to ${this.host}:${this.port}...`);
        this.socket = new net.Socket();
        this.socket.connect(this.port, this.host, () => {
            console.log('[RoverConnection] Connected to rover');
            this._isConnected = true;
            this.emit('connected');
        });
        this.socket.on('data', (data) => {
            this.handleData(data);
        });
        this.socket.on('close', () => {
            console.log('[RoverConnection] Connection closed');
            this._isConnected = false;
            this.emit('disconnected');
            this.scheduleReconnect();
        });
        this.socket.on('error', (err) => {
            console.error('[RoverConnection] Socket error:', err.message);
            this.emit('error', err);
        });
    }
    /**
     * Disconnect from rover
     */
    disconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.socket) {
            this.socket.destroy();
            this.socket = null;
        }
        this._isConnected = false;
    }
    /**
     * Send a command to the rover (JSON format for now)
     */
    sendCommand(command) {
        if (!this.socket || !this._isConnected) {
            console.warn('[RoverConnection] Cannot send command: not connected');
            return false;
        }
        try {
            const json = JSON.stringify(command) + '\n';
            this.socket.write(json);
            console.log('[RoverConnection] Sent:', json.trim());
            return true;
        }
        catch (err) {
            console.error('[RoverConnection] Failed to send command:', err);
            return false;
        }
    }
    /**
     * Handle incoming data (JSON lines)
     */
    handleData(data) {
        this.buffer += data.toString();
        // Process complete lines
        let newlineIndex;
        while ((newlineIndex = this.buffer.indexOf('\n')) !== -1) {
            const line = this.buffer.slice(0, newlineIndex).trim();
            this.buffer = this.buffer.slice(newlineIndex + 1);
            if (line.length > 0) {
                this.parseTelemetry(line);
            }
        }
    }
    /**
     * Parse JSON telemetry from rover
     */
    parseTelemetry(json) {
        try {
            const data = JSON.parse(json);
            // Map the ESP32 JSON format to our VehicleState
            const partialState = {
                connected: true,
                lastHeartbeat: Date.now(),
            };
            // GPS
            if (data.lat !== undefined && data.lon !== undefined) {
                partialState.gps = {
                    latitude: data.lat,
                    longitude: data.lon,
                    altitude: data.altitude || 0,
                    satellites: data.satellites || 0,
                    hdop: data.hdop || 99,
                    fix: data.lat !== 0 || data.lon !== 0,
                };
            }
            // Attitude
            if (data.heading !== undefined || data.imu_data) {
                const imuData = data.imu_data || {};
                partialState.attitude = {
                    roll: imuData.roll || 0,
                    pitch: imuData.pitch || 0,
                    yaw: data.heading || 0,
                };
                // Full IMU data
                if (data.imu_data) {
                    partialState.imu = {
                        roll: imuData.roll || 0,
                        pitch: imuData.pitch || 0,
                        quaternion: imuData.quaternion || [1, 0, 0, 0],
                        accel: imuData.accel || [0, 0, 0],
                        gyro: imuData.gyro || [0, 0, 0],
                        mag: imuData.mag || [0, 0, 0],
                        linearAccel: imuData.linear_accel || [0, 0, 0],
                        gravity: imuData.gravity || [0, 0, 9.8],
                        calibration: {
                            system: imuData.calibration?.sys ?? 0,
                            gyroscope: imuData.calibration?.gyro ?? 0,
                            accelerometer: imuData.calibration?.accel ?? 0,
                            magnetometer: imuData.calibration?.mag ?? 0,
                        },
                        temperature: imuData.temperature || data.temperature || 0,
                    };
                }
            }
            // System status
            if (data.wifi_strength !== undefined) {
                partialState.system = {
                    batteryVoltage: data.battery || 0,
                    wifiStrength: data.wifi_strength,
                    mode: data.mode || 'IDLE',
                    armed: data.armed || false,
                    uptime: data.timestamp || 0,
                };
            }
            // Sensor status
            if (data.sensors) {
                partialState.sensorStatus = {
                    accel: data.sensors.accel ?? false,
                    gyro: data.sensors.gyro ?? false,
                    mag: data.sensors.mag ?? false,
                    gps: data.sensors.gps ?? false,
                    tof: data.sensors.tof ?? false,
                };
            }
            // TOF data
            if (data.tof_data) {
                partialState.tofData = {
                    distance: data.tof_data.distance || 0,
                    status: data.tof_data.status || false,
                };
            }
            this.emit('telemetry', partialState);
        }
        catch (err) {
            console.warn('[RoverConnection] Failed to parse telemetry:', json.substring(0, 100));
        }
    }
    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        if (this.reconnectTimer)
            return;
        console.log(`[RoverConnection] Reconnecting in ${config_js_1.config.ROVER_RECONNECT_DELAY}ms...`);
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, config_js_1.config.ROVER_RECONNECT_DELAY);
    }
}
exports.RoverConnection = RoverConnection;
//# sourceMappingURL=roverConnection.js.map