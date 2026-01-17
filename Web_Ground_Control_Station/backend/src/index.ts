/**
 * ESP32 Rover Ground Control Station - Backend
 * 
 * Main entry point for the Node.js server.
 * - Express for HTTP API
 * - Socket.IO for real-time WebSocket communication
 * - TCP client for rover connection
 */

import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import { Server } from 'socket.io';

import { config } from './config.js';
import { RoverConnection } from './roverConnection.js';
import { VehicleStore } from './vehicleStore.js';
import { setupSocketHandlers } from './socketHandlers.js';

// Initialize Express app
const app = express();
app.use(cors({ origin: config.CORS_ORIGIN }));
app.use(express.json());

// Create HTTP server
const httpServer = createServer(app);

// Initialize Socket.IO
const io = new Server(httpServer, {
    cors: {
        origin: config.CORS_ORIGIN,
        methods: ['GET', 'POST'],
    },
});

// Initialize vehicle state store
const vehicleStore = new VehicleStore();

// Initialize rover connection (let allows dynamic reconnection)
let roverConnection = new RoverConnection(config.ROVER_HOST, config.ROVER_PORT);

// Setup Socket.IO event handlers
setupSocketHandlers(io, vehicleStore, () => roverConnection);

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
    if (now - lastBroadcast >= config.TELEMETRY_BROADCAST_INTERVAL) {
        io.emit('state', vehicleStore.getState());
        lastBroadcast = now;
    }
}, config.TELEMETRY_BROADCAST_INTERVAL);

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

    // Validate inputs
    if (!host || !port) {
        return res.status(400).json({
            success: false,
            message: 'Host and port are required'
        });
    }

    // Disconnect old connection
    roverConnection.disconnect();

    // Create new connection
    roverConnection = new RoverConnection(host, parseInt(port, 10));

    // Set up event handlers for new connection
    roverConnection.on('connected', () => {
        vehicleStore.setConnected(true);
        io.emit('connection:status', { connected: true });
        console.log('[Main] Rover connected successfully');
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

    // Attempt connection
    roverConnection.connect();

    res.json({
        success: true,
        message: `Connecting to ${host}:${port}...`
    });
});

app.post('/rover/disconnect', (req, res) => {
    roverConnection.disconnect();
    res.json({ message: 'Disconnected' });
});

// Start the server
httpServer.listen(config.SERVER_PORT, () => {
    console.log('='.repeat(60));
    console.log(`  ESP32 Rover GCS Backend`);
    console.log('='.repeat(60));
    console.log(`  HTTP Server:    http://localhost:${config.SERVER_PORT}`);
    console.log(`  Socket.IO:      ws://localhost:${config.SERVER_PORT}`);
    console.log(`  Rover Target:   ${config.ROVER_HOST}:${config.ROVER_PORT}`);
    console.log('='.repeat(60));

    // Connection will be initiated manually via UI
    console.log('[Main] Waiting for manual connection request from UI...');
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
