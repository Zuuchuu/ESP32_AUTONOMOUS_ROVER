/**
 * Socket.IO Event Handlers
 *
 * Handles WebSocket connections from the frontend.
 */
import { Server } from 'socket.io';
import { VehicleStore } from './vehicleStore.js';
import { RoverConnection } from './roverConnection.js';
export declare function setupSocketHandlers(io: Server, vehicleStore: VehicleStore, getRoverConnection: () => RoverConnection): void;
//# sourceMappingURL=socketHandlers.d.ts.map