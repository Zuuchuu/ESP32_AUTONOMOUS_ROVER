"use strict";
/**
 * Socket.IO Event Handlers
 *
 * Handles WebSocket connections from the frontend.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.setupSocketHandlers = setupSocketHandlers;
function setupSocketHandlers(io, vehicleStore, getRoverConnection) {
    io.on('connection', (socket) => {
        console.log(`[Socket] Client connected: ${socket.id}`);
        // Send current state immediately on connect
        socket.emit('state', vehicleStore.getState());
        // Handle mission upload
        socket.on('mission:upload', (waypoints) => {
            console.log(`[Socket] Mission upload: ${waypoints.length} waypoints`);
            vehicleStore.setWaypoints(waypoints);
            // Format waypoints for ESP32 - upload only, don't auto-start
            const command = {
                command: 'upload_mission',
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
            }
            else {
                socket.emit('mission:uploaded', { success: false, error: 'Rover not connected' });
            }
        });
        // Handle mission control commands
        socket.on('mission:start', () => {
            // Start mission uses resume_mission to begin navigation
            getRoverConnection().sendCommand({ command: 'resume_mission' });
        });
        socket.on('mission:pause', () => {
            getRoverConnection().sendCommand({ command: 'pause_mission' });
        });
        socket.on('mission:resume', () => {
            getRoverConnection().sendCommand({ command: 'resume_mission' });
        });
        socket.on('mission:abort', () => {
            // Temporary stop - use pause_mission
            getRoverConnection().sendCommand({ command: 'pause_mission' });
        });
        socket.on('mission:clear', () => {
            // Full cancel - abort on rover and clear waypoints
            getRoverConnection().sendCommand({ command: 'abort_mission' });
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
        socket.on('manual:move', (data) => {
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
//# sourceMappingURL=socketHandlers.js.map