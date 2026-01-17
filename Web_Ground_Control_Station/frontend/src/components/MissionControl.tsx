/**
 * Mission Control Component
 * 
 * Displays mission status and waypoint list with dynamic control buttons.
 */

import { useRoverStore } from '../store/roverStore';

interface MissionControlProps {
    onUpload: () => void;
    onStart: () => void;
    onResume: () => void;
    onAbort: () => void;
    onClear: () => void;
}

export function MissionControl({
    onUpload,
    onStart,
    onResume,
    onAbort,
    onClear
}: MissionControlProps) {
    const { vehicleState, waypoints, clearWaypoints } = useRoverStore();
    const { mission } = vehicleState;

    const handleClear = () => {
        clearWaypoints();
        onClear();
    };

    // Determine mission state for dynamic buttons
    const hasWaypoints = waypoints.length > 0;
    const missionActive = mission.active;

    return (
        <div className="glass-card p-3">
            <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
                Mission Control
            </h3>

            {/* Mission Status */}
            <div className="mb-4 p-3 rounded-lg bg-gcs-dark border border-gcs-border">
                <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                        <span className="text-slate-400">Status:</span>
                        <span className={`ml-2 font-medium ${missionActive ? 'text-gcs-success' : 'text-slate-300'}`}>
                            {missionActive ? 'Active' : 'Idle'}
                        </span>
                    </div>
                    <div>
                        <span className="text-slate-400">Progress:</span>
                        <span className="ml-2 font-mono text-gcs-primary">
                            {mission.currentWaypointIndex + 1}/{mission.totalWaypoints || waypoints.length}
                        </span>
                    </div>
                    <div>
                        <span className="text-slate-400">Distance:</span>
                        <span className="ml-2 font-mono text-gcs-primary">
                            {mission.distanceToWaypoint.toFixed(1)}m
                        </span>
                    </div>
                    <div>
                        <span className="text-slate-400">Total:</span>
                        <span className="ml-2 font-mono text-gcs-primary">
                            {mission.totalDistance.toFixed(1)}m
                        </span>
                    </div>
                </div>
            </div>

            {/* Waypoint List */}
            <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">Waypoints</span>
                    <span className="text-xs text-slate-500">{waypoints.length}/10</span>
                </div>

                <div className="max-h-32 overflow-y-auto space-y-1 scrollbar-thin">
                    {waypoints.length === 0 ? (
                        <p className="text-sm text-slate-500 text-center py-2">
                            Click on map to add waypoints
                        </p>
                    ) : (
                        waypoints.map((wp, index) => (
                            <div
                                key={wp.id}
                                className={`flex items-center justify-between px-2 py-1 rounded text-sm
                  ${index === mission.currentWaypointIndex && missionActive
                                        ? 'bg-gcs-primary/20 border border-gcs-primary'
                                        : 'bg-gcs-dark'
                                    }
                  ${wp.reached ? 'opacity-50' : ''}`}
                            >
                                <span className="font-medium text-slate-300">
                                    WP {index + 1}
                                </span>
                                <span className="font-mono text-xs text-slate-400">
                                    {wp.lat.toFixed(5)}, {wp.lng.toFixed(5)}
                                </span>
                                {wp.reached && (
                                    <span className="text-gcs-success">✓</span>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Dynamic Control Buttons */}
            <div className="space-y-2">
                {/* State: No waypoints OR waypoints added but not uploaded */}
                {!missionActive && (
                    <>
                        <div className="grid grid-cols-2 gap-2">
                            <button
                                onClick={onUpload}
                                disabled={!hasWaypoints}
                                className="control-btn control-btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Upload Mission
                            </button>
                            <button
                                onClick={handleClear}
                                disabled={!hasWaypoints}
                                className="control-btn disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Clear
                            </button>
                        </div>

                        {/* Start button (shown after upload or if waypoints exist) */}
                        {hasWaypoints && (
                            <button
                                onClick={onStart}
                                className="w-full control-btn bg-gcs-success/20 border-gcs-success text-gcs-success
                           hover:bg-gcs-success/40"
                            >
                                Start Mission
                            </button>
                        )}
                    </>
                )}

                {/* State: Mission active */}
                {missionActive && (
                    <button
                        onClick={onAbort}
                        className="w-full control-btn control-btn-danger"
                    >
                        Stop Mission
                    </button>
                )}

                {/* State: Mission stopped/paused (not active but has waypoints) */}
                {!missionActive && hasWaypoints && mission.currentWaypointIndex > 0 && (
                    <div className="grid grid-cols-2 gap-2">
                        <button
                            onClick={onResume}
                            className="control-btn bg-gcs-warning/20 border-gcs-warning text-gcs-warning
                         hover:bg-gcs-warning/40"
                        >
                            Resume
                        </button>
                        <button
                            onClick={() => {
                                handleClear();
                                // Reset mission state
                            }}
                            className="control-btn"
                        >
                            New Mission
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
