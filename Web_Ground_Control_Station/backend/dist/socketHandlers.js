"use strict";
/**
 * Socket.IO Event Handlers
 *
 * Handles WebSocket connections from the frontend.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.setupSocketHandlers = setupSocketHandlers;
function setupSocketHandlers(io, vehicleStore, roverConnection) {
    io.on('connection', (socket) => {
        console.log(`[Socket] Client connected: ${socket.id}`);
        // Send current state immediately on connect
        socket.emit('state', vehicleStore.getState());
        // Handle mission upload
        socket.on('mission:upload', (waypoints) => {
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
            if (roverConnection.sendCommand(command)) {
                socket.emit('mission:uploaded', { success: true, count: waypoints.length });
            }
            else {
                socket.emit('mission:uploaded', { success: false, error: 'Rover not connected' });
            }
        });
        // Handle mission control commands
        socket.on('mission:start', () => {
            roverConnection.sendCommand({ command: 'start' });
        });
        socket.on('mission:pause', () => {
            roverConnection.sendCommand({ command: 'pause_mission' });
        });
        socket.on('mission:resume', () => {
            roverConnection.sendCommand({ command: 'resume_mission' });
        });
        socket.on('mission:abort', () => {
            roverConnection.sendCommand({ command: 'abort_mission' });
        });
        socket.on('mission:clear', () => {
            vehicleStore.clearWaypoints();
            socket.emit('state', vehicleStore.getState());
        });
        // Handle manual control
        socket.on('manual:enable', () => {
            console.log('[Socket] Manual control enabled');
            roverConnection.sendCommand({ command: 'enable_manual' });
        });
        socket.on('manual:disable', () => {
            console.log('[Socket] Manual control disabled');
            roverConnection.sendCommand({ command: 'disable_manual' });
        });
        socket.on('manual:move', (data) => {
            roverConnection.sendCommand({
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
//# sourceMappingURL=socketHandlers.js.map