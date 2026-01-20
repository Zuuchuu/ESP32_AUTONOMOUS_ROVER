/**
 * Mission Control Component
 * 
 * Displays mission status and waypoint list with dynamic control buttons.
 * 
 * State Machine:
 * - IDLE: No waypoints or waypoints added (shows Upload/Clear)
 * - UPLOADED: Mission uploaded to rover (shows Start + Upload/Clear)
 * - ACTIVE: Mission running (shows only STOP)
 * - PAUSED: Mission stopped (shows Resume/Cancel)
 */

import { useState, useEffect } from 'react';
import { useRoverStore } from '../store/roverStore';

// Mission UI states
type MissionUIState = 'IDLE' | 'UPLOADED' | 'ACTIVE' | 'PAUSED';

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

    // Local UI state to track mission flow
    const [uiState, setUIState] = useState<MissionUIState>('IDLE');

    const hasWaypoints = waypoints.length > 0;

    // Sync UI state with backend mission.active
    useEffect(() => {
        if (mission.active && uiState !== 'ACTIVE') {
            setUIState('ACTIVE');
        } else if (!mission.active && uiState === 'ACTIVE') {
            // Mission was stopped externally or completed
            setUIState('PAUSED');
        }
    }, [mission.active, uiState]);

    // Reset to IDLE when waypoints are cleared
    useEffect(() => {
        if (!hasWaypoints && uiState !== 'ACTIVE') {
            setUIState('IDLE');
        }
    }, [hasWaypoints, uiState]);

    // Handle Upload - transitions from IDLE to UPLOADED
    const handleUpload = () => {
        onUpload();
        setUIState('UPLOADED');
    };

    // Handle Start - transitions from UPLOADED to ACTIVE
    const handleStart = () => {
        onStart();
        setUIState('ACTIVE');
    };

    // Handle Stop - transitions from ACTIVE to PAUSED
    const handleStop = () => {
        onAbort();
        setUIState('PAUSED');
    };

    // Handle Resume - transitions from PAUSED back to ACTIVE
    const handleResume = () => {
        onResume();
        setUIState('ACTIVE');
    };

    // Handle Cancel - clears mission and returns to IDLE
    const handleCancel = () => {
        clearWaypoints();
        onClear();
        setUIState('IDLE');
    };

    // Handle Clear (in IDLE/UPLOADED state)
    const handleClear = () => {
        clearWaypoints();
        onClear();
        setUIState('IDLE');
    };

    // Get display status text
    const getStatusText = () => {
        switch (uiState) {
            case 'ACTIVE': return 'Active';
            case 'PAUSED': return 'Paused';
            case 'UPLOADED': return 'Ready';
            default: return 'Idle';
        }
    };

    const getStatusColor = () => {
        switch (uiState) {
            case 'ACTIVE': return 'text-gcs-success';
            case 'PAUSED': return 'text-gcs-warning';
            case 'UPLOADED': return 'text-gcs-primary';
            default: return 'text-slate-300';
        }
    };

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
                        <span className={`ml-2 font-medium ${getStatusColor()}`}>
                            {getStatusText()}
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
                  ${index === mission.currentWaypointIndex && uiState === 'ACTIVE'
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

            {/* Dynamic Control Buttons based on UI State */}
            <div className="space-y-2">
                {/* State: IDLE or UPLOADED - Show Upload/Clear buttons */}
                {(uiState === 'IDLE' || uiState === 'UPLOADED') && (
                    <div className="grid grid-cols-2 gap-2">
                        <button
                            onClick={handleUpload}
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
                )}

                {/* State: UPLOADED - Show Start button */}
                {uiState === 'UPLOADED' && hasWaypoints && (
                    <button
                        onClick={handleStart}
                        className="w-full control-btn bg-gcs-success/20 border-gcs-success text-gcs-success
                           hover:bg-gcs-success/40"
                    >
                        Start Mission
                    </button>
                )}

                {/* State: ACTIVE - Show only STOP button */}
                {uiState === 'ACTIVE' && (
                    <button
                        onClick={handleStop}
                        className="w-full control-btn control-btn-danger text-lg py-3 font-bold"
                    >
                        STOP
                    </button>
                )}

                {/* State: PAUSED - Show Resume and Cancel buttons */}
                {uiState === 'PAUSED' && (
                    <div className="grid grid-cols-2 gap-2">
                        <button
                            onClick={handleResume}
                            className="control-btn bg-gcs-success/20 border-gcs-success text-gcs-success
                         hover:bg-gcs-success/40"
                        >
                            Resume
                        </button>
                        <button
                            onClick={handleCancel}
                            className="control-btn control-btn-danger"
                        >
                            Cancel
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
