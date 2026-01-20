"use strict";
/**
 * Vehicle State Store
 *
 * Maintains the current state of the rover.
 * Merges partial updates from telemetry into a complete state object.
 *
 * OPTIMIZED: Uses dirty flag to prevent unnecessary broadcasts.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.VehicleStore = void 0;
const types_js_1 = require("./types.js");
class VehicleStore {
    state;
    _isDirty = false;
    _cachedState = null;
    constructor() {
        this.state = (0, types_js_1.createInitialVehicleState)();
    }
    /**
     * Check if state has changed since last broadcast
     */
    get isDirty() {
        return this._isDirty;
    }
    /**
     * Get current complete state (returns cached if not dirty)
     */
    getState() {
        if (!this._isDirty && this._cachedState) {
            return this._cachedState;
        }
        // Only create new object when state has changed
        this._cachedState = { ...this.state };
        return this._cachedState;
    }
    /**
     * Clear dirty flag after broadcast
     */
    clearDirty() {
        this._isDirty = false;
    }
    /**
     * Update state with partial data
     */
    update(partial) {
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
        // Mark as dirty after any update
        this._isDirty = true;
    }
    /**
     * Set connection status
     */
    setConnected(connected) {
        this.state.connected = connected;
        this._isDirty = true;
    }
    /**
     * Set waypoints
     */
    setWaypoints(waypoints) {
        this.state.waypoints = waypoints;
        this.state.mission.totalWaypoints = waypoints.length;
        this._isDirty = true;
    }
    /**
     * Clear all waypoints
     */
    clearWaypoints() {
        this.state.waypoints = [];
        this.state.mission.totalWaypoints = 0;
        this.state.mission.currentWaypointIndex = 0;
        this._isDirty = true;
    }
    /**
     * Reset to initial state
     */
    reset() {
        this.state = (0, types_js_1.createInitialVehicleState)();
        this._cachedState = null;
        this._isDirty = true;
    }
}
exports.VehicleStore = VehicleStore;
//# sourceMappingURL=vehicleStore.js.map