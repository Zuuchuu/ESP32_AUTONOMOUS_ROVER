/**
 * Socket.IO Event Handlers
 * 
 * Handles WebSocket connections from the frontend.
 */

import { Server, Socket } from 'socket.io';
import { VehicleStore } from './vehicleStore.js';
import { RoverConnection } from './roverConnection.js';
import { Waypoint } from './types.js';

export function setupSocketHandlers(
    io: Server,
    vehicleStore: VehicleStore,
    getRoverConnection: () => RoverConnection
): void {
    io.on('connection', (socket: Socket) => {
        console.log(`[Socket] Client connected: ${socket.id}`);

        // Send current state immediately on connect
        socket.emit('state', vehicleStore.getState());

        // Handle mission upload
        socket.on('mission:upload', (waypoints: Waypoint[]) => {
            console.log(`[Socket] Mission upload: ${waypoints.length} waypoints`);

            vehicleStore.setWaypoints(waypoints);

            // Format waypoints for ESP32
            const command = {
                command: 'start_mission',
                mission_id: `mission_${Date.now()}`,
                waypoints: waypoints.map(wp => ({
                    lat: wp.lat,
                    lng: wp.lng,
                })),
                parameters: {
                    speed_mps: 1.0,
                    cte_threshold_m: 2.0,
                    mission_timeout_s: 3600,
                },
            };

            if (getRoverConnection().sendCommand(command)) {
                socket.emit('mission:uploaded', { success: true, count: waypoints.length });
            } else {
                socket.emit('mission:uploaded', { success: false, error: 'Rover not connected' });
            }
        });

        // Handle mission control commands
        socket.on('mission:start', () => {
            getRoverConnection().sendCommand({ command: 'start' });
        });

        socket.on('mission:pause', () => {
            getRoverConnection().sendCommand({ command: 'pause_mission' });
        });

        socket.on('mission:resume', () => {
            getRoverConnection().sendCommand({ command: 'resume_mission' });
        });

        socket.on('mission:abort', () => {
            getRoverConnection().sendCommand({ command: 'abort_mission' });
        });

        socket.on('mission:clear', () => {
            vehicleStore.clearWaypoints();
            socket.emit('state', vehicleStore.getState());
        });

        // Handle manual control
        socket.on('manual:enable', () => {
            console.log('[Socket] Manual control enabled');
            getRoverConnection().sendCommand({ command: 'enable_manual' });
        });

        socket.on('manual:disable', () => {
            console.log('[Socket] Manual control disabled');
            getRoverConnection().sendCommand({ command: 'disable_manual' });
        });

        socket.on('manual:move', (data: { direction: string; speed: number }) => {
            getRoverConnection().sendCommand({
                command: 'manual_move',
                direction: data.direction,
                speed: data.speed,
            });
        });

        // Handle disconnect
        socket.on('disconnect', () => {
            console.log(`[Socket] Client disconnected: ${socket.id}`);
        });
    });
}
