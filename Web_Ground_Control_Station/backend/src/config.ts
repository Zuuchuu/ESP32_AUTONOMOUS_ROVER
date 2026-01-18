/**
 * Backend Configuration
 * All environment variables and constants are defined here.
 */

export const config = {
    // Server port for Express/Socket.IO
    SERVER_PORT: parseInt(process.env.SERVER_PORT || '3001', 10),

    // ESP32 Rover TCP connection settings
    ROVER_HOST: process.env.ROVER_HOST || '192.168.1.100',
    ROVER_PORT: parseInt(process.env.ROVER_PORT || '8080', 10),

    // Telemetry broadcast rate (ms)
    TELEMETRY_BROADCAST_INTERVAL: 100, // 10Hz

    // Connection retry settings
    ROVER_RECONNECT_DELAY: 5000,

    // CORS origins (frontend URL)
    CORS_ORIGIN: process.env.CORS_ORIGIN || 'http://localhost:5173',
};
