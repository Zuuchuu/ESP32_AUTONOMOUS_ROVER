/**
 * Vehicle State Store
 *
 * Maintains the current state of the rover.
 * Merges partial updates from telemetry into a complete state object.
 *
 * OPTIMIZED: Uses dirty flag to prevent unnecessary broadcasts.
 */
import { VehicleState, Waypoint } from './types.js';
export declare class VehicleStore {
    private state;
    private _isDirty;
    private _cachedState;
    constructor();
    /**
     * Check if state has changed since last broadcast
     */
    get isDirty(): boolean;
    /**
     * Get current complete state (returns cached if not dirty)
     */
    getState(): VehicleState;
    /**
     * Clear dirty flag after broadcast
     */
    clearDirty(): void;
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