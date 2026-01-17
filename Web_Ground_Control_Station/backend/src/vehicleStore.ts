/**
 * Vehicle State Store
 * 
 * Maintains the current state of the rover.
 * Merges partial updates from telemetry into a complete state object.
 */

import { VehicleState, createInitialVehicleState, Waypoint } from './types.js';

export class VehicleStore {
    private state: VehicleState;

    constructor() {
        this.state = createInitialVehicleState();
    }

    /**
     * Get current complete state
     */
    getState(): VehicleState {
        return { ...this.state };
    }

    /**
     * Update state with partial data
     */
    update(partial: Partial<VehicleState>): void {
        // Deep merge for nested objects
        if (partial.attitude) {
            this.state.attitude = { ...this.state.attitude, ...partial.attitude };
        }
        if (partial.gps) {
            this.state.gps = { ...this.state.gps, ...partial.gps };
        }
        if (partial.imu) {
            this.state.imu = { ...this.state.imu, ...partial.imu };
        }
        if (partial.system) {
            this.state.system = { ...this.state.system, ...partial.system };
        }
        if (partial.mission) {
            this.state.mission = { ...this.state.mission, ...partial.mission };
        }
        if (partial.waypoints !== undefined) {
            this.state.waypoints = partial.waypoints;
        }
        if (partial.sensorStatus) {
            this.state.sensorStatus = { ...this.state.sensorStatus, ...partial.sensorStatus };
        }
        if (partial.tofData) {
            this.state.tofData = { ...this.state.tofData, ...partial.tofData };
        }

        // Top-level fields
        if (partial.connected !== undefined) {
            this.state.connected = partial.connected;
        }
        if (partial.lastHeartbeat !== undefined) {
            this.state.lastHeartbeat = partial.lastHeartbeat;
        }
    }

    /**
     * Set connection status
     */
    setConnected(connected: boolean): void {
        this.state.connected = connected;
    }

    /**
     * Set waypoints
     */
    setWaypoints(waypoints: Waypoint[]): void {
        this.state.waypoints = waypoints;
        this.state.mission.totalWaypoints = waypoints.length;
    }

    /**
     * Clear all waypoints
     */
    clearWaypoints(): void {
        this.state.waypoints = [];
        this.state.mission.totalWaypoints = 0;
        this.state.mission.currentWaypointIndex = 0;
    }

    /**
     * Reset to initial state
     */
    reset(): void {
        this.state = createInitialVehicleState();
    }
}
