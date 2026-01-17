/**
 * Socket.IO Client Hook
 * 
 * Manages WebSocket connection to backend and syncs state.
 */

import { useEffect, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { useRoverStore, VehicleState, Waypoint } from '../store/roverStore';

const SOCKET_URL = import.meta.env.PROD
    ? window.location.origin
    : 'http://localhost:3001';

export function useSocket() {
    const socketRef = useRef<Socket | null>(null);
    const { setVehicleState, setSocketConnected } = useRoverStore();

    useEffect(() => {
        // Create socket connection
        const socket = io(SOCKET_URL, {
            transports: ['websocket'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: Infinity,
        });

        socketRef.current = socket;

        socket.on('connect', () => {
            console.log('[Socket] Connected to backend');
            setSocketConnected(true);
        });

        socket.on('disconnect', () => {
            console.log('[Socket] Disconnected from backend');
            setSocketConnected(false);
        });

        socket.on('state', (state: VehicleState) => {
            setVehicleState(state);
        });

        socket.on('connection:status', (data: { connected: boolean }) => {
            console.log('[Socket] Rover connection status:', data.connected);
        });

        return () => {
            socket.disconnect();
        };
    }, [setVehicleState, setSocketConnected]);

    // Mission commands
    const uploadMission = useCallback((waypoints: Waypoint[]) => {
        socketRef.current?.emit('mission:upload', waypoints);
    }, []);

    const startMission = useCallback(() => {
        socketRef.current?.emit('mission:start');
    }, []);

    const pauseMission = useCallback(() => {
        socketRef.current?.emit('mission:pause');
    }, []);

    const resumeMission = useCallback(() => {
        socketRef.current?.emit('mission:resume');
    }, []);

    const abortMission = useCallback(() => {
        socketRef.current?.emit('mission:abort');
    }, []);

    const clearMission = useCallback(() => {
        socketRef.current?.emit('mission:clear');
    }, []);

    // Manual control commands
    const enableManualControl = useCallback(() => {
        socketRef.current?.emit('manual:enable');
    }, []);

    const disableManualControl = useCallback(() => {
        socketRef.current?.emit('manual:disable');
    }, []);

    const sendManualMove = useCallback((direction: string, speed: number) => {
        socketRef.current?.emit('manual:move', { direction, speed });
    }, []);

    // Rover connection control
    const connectRover = useCallback(async (host: string, port: number) => {
        try {
            const response = await fetch(`${SOCKET_URL}/rover/connect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host, port }),
            });
            const data = await response.json();
            console.log('[Socket] Connect response:', data);
            return data;
        } catch (error) {
            console.error('[Socket] Connect error:', error);
            return { success: false, message: 'Failed to connect' };
        }
    }, []);

    const disconnectRover = useCallback(async () => {
        try {
            const response = await fetch(`${SOCKET_URL}/rover/disconnect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            const data = await response.json();
            console.log('[Socket] Disconnect response:', data);
            return data;
        } catch (error) {
            console.error('[Socket] Disconnect error:', error);
            return { success: false, message: 'Failed to disconnect' };
        }
    }, []);

    return {
        uploadMission,
        startMission,
        pauseMission,
        resumeMission,
        abortMission,
        clearMission,
        enableManualControl,
        disableManualControl,
        sendManualMove,
        connectRover,
        disconnectRover,
    };
}
