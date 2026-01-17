/**
 * Rover Connection Manager
 * 
 * Handles TCP connection to the ESP32 Rover.
 * Currently supports the existing JSON protocol.
 * TODO: Migrate to Mavlink binary protocol.
 */

import * as net from 'net';
import { EventEmitter } from 'events';
import { config } from './config.js';
import { VehicleState, createInitialVehicleState } from './types.js';

export interface RoverConnectionEvents {
    connected: () => void;
    disconnected: () => void;
    telemetry: (state: Partial<VehicleState>) => void;
    error: (error: Error) => void;
}

export class RoverConnection extends EventEmitter {
    private socket: net.Socket | null = null;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private buffer: string = '';
    private _isConnected: boolean = false;

    constructor(
        private host: string = config.ROVER_HOST,
        private port: number = config.ROVER_PORT
    ) {
        super();
    }

    get isConnected(): boolean {
        return this._isConnected;
    }

    /**
     * Attempt to connect to the rover
     */
    connect(): void {
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

        this.socket.on('data', (data: Buffer) => {
            this.handleData(data);
        });

        this.socket.on('close', () => {
            console.log('[RoverConnection] Connection closed');
            this._isConnected = false;
            this.emit('disconnected');
            this.scheduleReconnect();
        });

        this.socket.on('error', (err: Error) => {
            console.error('[RoverConnection] Socket error:', err.message);
            this.emit('error', err);
        });
    }

    /**
     * Disconnect from rover
     */
    disconnect(): void {
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
    sendCommand(command: object): boolean {
        if (!this.socket || !this._isConnected) {
            console.warn('[RoverConnection] Cannot send command: not connected');
            return false;
        }

        try {
            const json = JSON.stringify(command) + '\n';
            this.socket.write(json);
            console.log('[RoverConnection] Sent:', json.trim());
            return true;
        } catch (err) {
            console.error('[RoverConnection] Failed to send command:', err);
            return false;
        }
    }

    /**
     * Handle incoming data (JSON lines)
     */
    private handleData(data: Buffer): void {
        this.buffer += data.toString();

        // Process complete lines
        let newlineIndex: number;
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
    private parseTelemetry(json: string): void {
        try {
            const data = JSON.parse(json);

            // Map the ESP32 JSON format to our VehicleState
            const partialState: Partial<VehicleState> = {
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
        } catch (err) {
            console.warn('[RoverConnection] Failed to parse telemetry:', json.substring(0, 100));
        }
    }

    /**
     * Schedule reconnection attempt
     */
    private scheduleReconnect(): void {
        if (this.reconnectTimer) return;

        console.log(`[RoverConnection] Reconnecting in ${config.ROVER_RECONNECT_DELAY}ms...`);
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, config.ROVER_RECONNECT_DELAY);
    }
}
