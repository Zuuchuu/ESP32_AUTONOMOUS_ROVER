"use strict";
/**
 * ESP32 Rover Ground Control Station - Backend
 *
 * Main entry point for the Node.js server.
 * - Express for HTTP API
 * - Socket.IO for real-time WebSocket communication
 * - TCP client for rover connection
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const http_1 = require("http");
const socket_io_1 = require("socket.io");
const config_js_1 = require("./config.js");
const roverConnection_js_1 = require("./roverConnection.js");
const vehicleStore_js_1 = require("./vehicleStore.js");
const socketHandlers_js_1 = require("./socketHandlers.js");
// Initialize Express app
const app = (0, express_1.default)();
app.use((0, cors_1.default)({ origin: config_js_1.config.CORS_ORIGIN }));
app.use(express_1.default.json());
// Create HTTP server
const httpServer = (0, http_1.createServer)(app);
// Initialize Socket.IO
const io = new socket_io_1.Server(httpServer, {
    cors: {
        origin: config_js_1.config.CORS_ORIGIN,
        methods: ['GET', 'POST'],
    },
});
// Initialize vehicle state store
const vehicleStore = new vehicleStore_js_1.VehicleStore();
// Initialize rover connection
const roverConnection = new roverConnection_js_1.RoverConnection(config_js_1.config.ROVER_HOST, config_js_1.config.ROVER_PORT);
// Setup Socket.IO event handlers
(0, socketHandlers_js_1.setupSocketHandlers)(io, vehicleStore, roverConnection);
// Rover connection event handlers
roverConnection.on('connected', () => {
    vehicleStore.setConnected(true);
    io.emit('connection:status', { connected: true });
});
roverConnection.on('disconnected', () => {
    vehicleStore.setConnected(false);
    io.emit('connection:status', { connected: false });
});
roverConnection.on('telemetry', (partialState) => {
    vehicleStore.update(partialState);
});
roverConnection.on('error', (error) => {
    console.error('[Main] Rover connection error:', error.message);
});
// Broadcast state to all connected clients at regular interval
let lastBroadcast = 0;
setInterval(() => {
    const now = Date.now();
    if (now - lastBroadcast >= config_js_1.config.TELEMETRY_BROADCAST_INTERVAL) {
        io.emit('state', vehicleStore.getState());
        lastBroadcast = now;
    }
}, config_js_1.config.TELEMETRY_BROADCAST_INTERVAL);
// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        roverConnected: roverConnection.isConnected,
        uptime: process.uptime(),
    });
});
// Get current state endpoint (for debugging)
app.get('/state', (req, res) => {
    res.json(vehicleStore.getState());
});
// Manual rover connection control
app.post('/rover/connect', (req, res) => {
    const { host, port } = req.body;
    // Could implement dynamic host/port here
    roverConnection.connect();
    res.json({ message: 'Connection initiated' });
});
app.post('/rover/disconnect', (req, res) => {
    roverConnection.disconnect();
    res.json({ message: 'Disconnected' });
});
// Start the server
httpServer.listen(config_js_1.config.SERVER_PORT, () => {
    console.log('='.repeat(60));
    console.log(`  ESP32 Rover GCS Backend`);
    console.log('='.repeat(60));
    console.log(`  HTTP Server:    http://localhost:${config_js_1.config.SERVER_PORT}`);
    console.log(`  Socket.IO:      ws://localhost:${config_js_1.config.SERVER_PORT}`);
    console.log(`  Rover Target:   ${config_js_1.config.ROVER_HOST}:${config_js_1.config.ROVER_PORT}`);
    console.log('='.repeat(60));
    // Attempt initial connection to rover
    console.log('[Main] Attempting to connect to rover...');
    roverConnection.connect();
});
// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n[Main] Shutting down...');
    roverConnection.disconnect();
    httpServer.close(() => {
        console.log('[Main] Server closed');
        process.exit(0);
    });
});
//# sourceMappingURL=index.js.map