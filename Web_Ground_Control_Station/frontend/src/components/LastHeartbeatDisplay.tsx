import { useRoverStore } from '../store/roverStore';

export function LastHeartbeatDisplay() {
    const lastHeartbeat = useRoverStore(state => state.vehicleState.lastHeartbeat);

    return (
        <span>
            Last Update: {lastHeartbeat > 0
                ? new Date(lastHeartbeat).toLocaleTimeString()
                : 'Never'}
        </span>
    );
}
