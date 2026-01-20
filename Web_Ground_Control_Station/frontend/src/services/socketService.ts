/**
 * Socket Service (Singleton)
 * 
 * OPTIMIZED: Socket connection is managed as a singleton module.
 * - Avoids closure issues with React hooks
 * - Uses getState() for stable store access
 * - Single connection instance for the entire app
 */

import { io, Socket } from 'socket.io-client';
import { useRoverStore } from '../store/roverStore';

const SOCKET_URL = import.meta.env.PROD
    ? window.location.origin
    : 'http://localhost:3001';

// Singleton socket instance
let socket: Socket | null = null;
let isInitialized = false;

/**
 * Initialize socket connection (call once on app startup)
 */
export function initializeSocket(): void {
    if (isInitialized) return;

    socket = io(SOCKET_URL, {
        transports: ['websocket'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: Infinity,
    });

    socket.on('connect', () => {
        console.log('[Socket] Connected to backend');
        // Use getState() to avoid closure issues
        useRoverStore.getState().setSocketConnected(true);
    });

    socket.on('disconnect', () => {
        console.log('[Socket] Disconnected from backend');
        useRoverStore.getState().setSocketConnected(false);
    });

    socket.on('state', (state) => {
        // Direct call to store action via getState()
        useRoverStore.getState().setVehicleState(state);
    });

    socket.on('connection:status', (data: { connected: boolean }) => {
        console.log('[Socket] Rover connection status:', data.connected);
    });

    isInitialized = true;
}

/**
 * Get the socket instance (for emitting events)
 */
export function getSocket(): Socket | null {
    return socket;
}

/**
 * Disconnect and cleanup
 */
export function disconnectSocket(): void {
    if (socket) {
        socket.disconnect();
        socket = null;
        isInitialized = false;
    }
}

// Socket command helpers
export const socketCommands = {
    uploadMission: (waypoints: unknown[]) => {
        socket?.emit('mission:upload', waypoints);
    },
    startMission: () => {
        socket?.emit('mission:start');
    },
    pauseMission: () => {
        socket?.emit('mission:pause');
    },
    resumeMission: () => {
        socket?.emit('mission:resume');
    },
    abortMission: () => {
        socket?.emit('mission:abort');
    },
    clearMission: () => {
        socket?.emit('mission:clear');
    },
    enableManualControl: () => {
        socket?.emit('manual:enable');
    },
    disableManualControl: () => {
        socket?.emit('manual:disable');
    },
    sendManualMove: (direction: string, speed: number) => {
        socket?.emit('manual:move', { direction, speed });
    },
};

// HTTP API helpers
export async function connectRover(host: string, port: number) {
    try {
        const response = await fetch(`${SOCKET_URL}/rover/connect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, port }),
        });
        return await response.json();
    } catch (error) {
        console.error('[Socket] Connect error:', error);
        return { success: false, message: 'Failed to connect' };
    }
}

export async function disconnectRover() {
    try {
        const response = await fetch(`${SOCKET_URL}/rover/disconnect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        return await response.json();
    } catch (error) {
        console.error('[Socket] Disconnect error:', error);
        return { success: false, message: 'Failed to disconnect' };
    }
}
