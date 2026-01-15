"use strict";
/**
 * Vehicle State Store
 *
 * Maintains the current state of the rover.
 * Merges partial updates from telemetry into a complete state object.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.VehicleStore = void 0;
const types_js_1 = require("./types.js");
class VehicleStore {
    state;
    constructor() {
        this.state = (0, types_js_1.createInitialVehicleState)();
    }
    /**
     * Get current complete state
     */
    getState() {
        return { ...this.state };
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
    setConnected(connected) {
        this.state.connected = connected;
    }
    /**
     * Set waypoints
     */
    setWaypoints(waypoints) {
        this.state.waypoints = waypoints;
        this.state.mission.totalWaypoints = waypoints.length;
    }
    /**
     * Clear all waypoints
     */
    clearWaypoints() {
        this.state.waypoints = [];
        this.state.mission.totalWaypoints = 0;
        this.state.mission.currentWaypointIndex = 0;
    }
    /**
     * Reset to initial state
     */
    reset() {
        this.state = (0, types_js_1.createInitialVehicleState)();
    }
}
exports.VehicleStore = VehicleStore;
//# sourceMappingURL=vehicleStore.js.map