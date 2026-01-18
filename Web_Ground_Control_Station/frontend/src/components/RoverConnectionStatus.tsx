import { useRoverStore } from '../store/roverStore';

export function RoverConnectionStatus() {
    const connected = useRoverStore(state => state.vehicleState.connected);

    return (
        <div className={`flex items-center gap-2 text-sm ${connected ? 'text-gcs-success' : 'text-gcs-danger'}`}>
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-gcs-success animate-pulse' : 'bg-gcs-danger'}`} />
            {connected ? 'Rover Connected' : 'Rover Disconnected'}
        </div>
    );
}
