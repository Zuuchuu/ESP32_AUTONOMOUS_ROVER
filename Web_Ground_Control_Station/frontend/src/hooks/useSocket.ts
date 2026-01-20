/**
 * Socket Hook (Simplified wrapper around socketService)
 * 
 * OPTIMIZED: Uses singleton socketService instead of managing connection in React.
 * This hook just provides a convenient interface for components.
 */

import { useEffect } from 'react';
import { useRoverStore } from '../store/roverStore';
import {
    initializeSocket,
    socketCommands,
    connectRover,
    disconnectRover,
} from '../services/socketService';

export function useSocket() {
    // Initialize socket on mount (idempotent - only runs once)
    useEffect(() => {
        initializeSocket();
        // No cleanup - socket persists for app lifetime
    }, []);

    // Get stable waypoints reference for upload
    const waypoints = useRoverStore((state) => state.waypoints);

    return {
        // Mission commands
        uploadMission: () => socketCommands.uploadMission(waypoints),
        startMission: socketCommands.startMission,
        pauseMission: socketCommands.pauseMission,
        resumeMission: socketCommands.resumeMission,
        abortMission: socketCommands.abortMission,
        clearMission: socketCommands.clearMission,

        // Manual control
        enableManualControl: socketCommands.enableManualControl,
        disableManualControl: socketCommands.disableManualControl,
        sendManualMove: socketCommands.sendManualMove,

        // Rover connection
        connectRover,
        disconnectRover,
    };
}
