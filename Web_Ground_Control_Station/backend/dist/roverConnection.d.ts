/**
 * Rover Connection Manager
 *
 * Handles TCP connection to the ESP32 Rover.
 * Currently supports the existing JSON protocol.
 * TODO: Migrate to Mavlink binary protocol.
 */
import { EventEmitter } from 'events';
import { VehicleState } from './types.js';
export interface RoverConnectionEvents {
    connected: () => void;
    disconnected: () => void;
    telemetry: (state: Partial<VehicleState>) => void;
    error: (error: Error) => void;
}
export declare class RoverConnection extends EventEmitter {
    private host;
    private port;
    private socket;
    private reconnectTimer;
    private buffer;
    private _isConnected;
    constructor(host?: string, port?: number);
    get isConnected(): boolean;
    /**
     * Attempt to connect to the rover
     */
    connect(): void;
    /**
     * Disconnect from rover
     */
    disconnect(): void;
    /**
     * Send a command to the rover (JSON format for now)
     */
    sendCommand(command: object): boolean;
    /**
     * Handle incoming data (JSON lines)
     */
    private handleData;
    /**
     * Parse JSON telemetry from rover
     */
    private parseTelemetry;
    /**
     * Schedule reconnection attempt
     */
    private scheduleReconnect;
}
//# sourceMappingURL=roverConnection.d.ts.map