/**
 * ESP32 Rover Ground Control Station
 * 
 * Main application component with full-screen map and overlay sidebars.
 */

import { useEffect } from 'react';
import { useRoverStore } from './store/roverStore';
import { useSocket } from './hooks/useSocket';
import {
    AttitudeDisplay,
    GPSStatus,
    SystemStatus,
    IMUCalibration,
    SensorStatusBar,
    MapView,
    ManualControl,
    MissionControl,
    ModeToggle,
} from './components';

function App() {
    const {
        vehicleState,
        controlMode,
        isSocketConnected,
        setControlMode,
    } = useRoverStore();

    const {
        uploadMission,
        startMission,
        resumeMission,
        abortMission,
        clearMission,
        enableManualControl,
        disableManualControl,
        sendManualMove,
    } = useSocket();

    // Handle mode changes
    useEffect(() => {
        if (controlMode === 'manual') {
            enableManualControl();
        } else {
            disableManualControl();
        }
    }, [controlMode, enableManualControl, disableManualControl]);

    const handleUploadMission = () => {
        uploadMission(vehicleState.waypoints);
    };

    return (
        <div className="min-h-screen bg-gcs-darker relative">
            {/* Header */}
            <header className="absolute top-0 left-0 right-0 z-50 bg-gcs-dark/95 backdrop-blur-md border-b border-gcs-border px-4 py-3">
                <div className="grid grid-cols-3 items-center gap-4">
                    {/* Left: Title and Rover Status */}
                    <div className="flex items-center gap-4">
                        <h1 className="text-xl font-bold text-white">
                            🚀 ESP32 Rover GCS
                        </h1>
                        <div className={`flex items-center gap-2 text-sm ${vehicleState.connected ? 'text-gcs-success' : 'text-gcs-danger'
                            }`}>
                            <div className={`w-2 h-2 rounded-full ${vehicleState.connected ? 'bg-gcs-success animate-pulse' : 'bg-gcs-danger'
                                }`} />
                            {vehicleState.connected ? 'Rover Connected' : 'Rover Disconnected'}
                        </div>
                    </div>

                    {/* Center: Sensor Status Bar */}
                    <div className="flex justify-center">
                        <SensorStatusBar sensorStatus={vehicleState.sensorStatus} />
                    </div>

                    {/* Right: Mode Toggle */}
                    <div className="flex justify-end">
                        <ModeToggle mode={controlMode} onModeChange={setControlMode} />
                    </div>
                </div>
            </header>

            {/* Full-screen Map */}
            <div className="fixed inset-0 pt-20 pb-10 px-4">
                <div className="w-full h-full rounded-2xl overflow-hidden relative">
                    <MapView allowWaypointPlacement={controlMode === 'mission'} />

                    {/* Left Sidebar - Telemetry (inside map) */}
                    <div className="absolute left-4 top-12 bottom-4 w-64 z-40 overflow-y-auto space-y-3 scrollbar-thin">
                        <AttitudeDisplay
                            pitch={vehicleState.attitude.pitch}
                            roll={vehicleState.attitude.roll}
                            heading={vehicleState.attitude.yaw}
                        />
                        <GPSStatus gps={vehicleState.gps} />
                        <IMUCalibration calibration={vehicleState.imu.calibration} />
                        <SystemStatus
                            system={vehicleState.system}
                            connected={vehicleState.connected}
                            socketConnected={isSocketConnected}
                        />
                    </div>

                    {/* Right Sidebar - Controls (inside map) */}
                    <div className="absolute right-4 top-16 bottom-4 w-64 z-40 overflow-y-auto scrollbar-thin">
                        {controlMode === 'mission' ? (
                            <MissionControl
                                onUpload={handleUploadMission}
                                onStart={startMission}
                                onResume={resumeMission}
                                onAbort={abortMission}
                                onClear={clearMission}
                            />
                        ) : (
                            <ManualControl
                                onMove={sendManualMove}
                                onEnable={enableManualControl}
                                onDisable={disableManualControl}
                            />
                        )}
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer className="absolute bottom-0 left-0 right-0 z-50 bg-gcs-dark/95 backdrop-blur-md border-t border-gcs-border px-4 py-2">
                <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>ESP32 Autonomous Rover Ground Control Station v1.1</span>
                    <span>
                        Last Update: {vehicleState.lastHeartbeat > 0
                            ? new Date(vehicleState.lastHeartbeat).toLocaleTimeString()
                            : 'Never'}
                    </span>
                </div>
            </footer>
        </div>
    );
}

export default App;
