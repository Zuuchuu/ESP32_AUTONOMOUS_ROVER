/**
 * Vehicle State Store
 *
 * Maintains the current state of the rover.
 * Merges partial updates from telemetry into a complete state object.
 */
import { VehicleState, Waypoint } from './types.js';
export declare class VehicleStore {
    private state;
    constructor();
    /**
     * Get current complete state
     */
    getState(): VehicleState;
    /**
     * Update state with partial data
     */
    update(partial: Partial<VehicleState>): void;
    /**
     * Set connection status
     */
    setConnected(connected: boolean): void;
    /**
     * Set waypoints
     */
    setWaypoints(waypoints: Waypoint[]): void;
    /**
     * Clear all waypoints
     */
    clearWaypoints(): void;
    /**
     * Reset to initial state
     */
    reset(): void;
}
//# sourceMappingURL=vehicleStore.d.ts.map