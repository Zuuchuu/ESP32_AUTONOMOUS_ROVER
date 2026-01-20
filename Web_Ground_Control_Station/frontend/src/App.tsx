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
    ConnectionControl,
    RoverConnectionStatus,
    LastHeartbeatDisplay,
} from './components';

function App() {
    // Only subscribe to controlMode for layout decisions
    const { controlMode, setControlMode } = useRoverStore();

    const {
        uploadMission,
        startMission,
        resumeMission,
        abortMission,
        clearMission,
        enableManualControl,
        disableManualControl,
        sendManualMove,
        connectRover,
        disconnectRover,
    } = useSocket();

    // Handle mode changes
    useEffect(() => {
        if (controlMode === 'manual') {
            enableManualControl();
        } else {
            disableManualControl();
        }
    }, [controlMode, enableManualControl, disableManualControl]);

    return (
        <div className="min-h-screen bg-gcs-darker relative">
            {/* Header - no blur for performance */}
            <header className="absolute top-0 left-0 right-0 z-50 bg-gcs-dark/95 border-b border-gcs-border px-4 py-3">
                <div className="grid grid-cols-3 items-center gap-4">
                    {/* Left: Title and Rover Status */}
                    <div className="flex items-center gap-4">
                        <h1 className="text-xl font-bold text-white">
                            🚀 ESP32 Rover GCS
                        </h1>

                        <RoverConnectionStatus />

                        <ConnectionControl
                            onConnect={connectRover}
                            onDisconnect={disconnectRover}
                        />
                    </div>

                    {/* Center: Sensor Status Bar */}
                    <div className="flex justify-center">
                        <SensorStatusBar />
                    </div>

                    {/* Right: Mode Toggle */}
                    <div className="flex justify-end">
                        <ModeToggle mode={controlMode} onModeChange={setControlMode} />
                    </div>
                </div>
            </header>

            {/* Full-screen Map */}
            <div className="fixed inset-0 pt-24 pb-10 px-4">
                <div className="w-full h-full rounded-2xl overflow-hidden relative">
                    {/* MapView now handles its own subscriptions */}
                    <MapView allowWaypointPlacement={controlMode === 'mission'} />

                    {/* Left Sidebar - Telemetry (inside map) */}
                    <div className="absolute left-4 top-12 bottom-4 w-64 z-[1000] overflow-y-auto space-y-3 scrollbar-thin pointer-events-auto">
                        <AttitudeDisplay />
                        <GPSStatus />
                        <IMUCalibration />
                        <SystemStatus />
                    </div>

                    {/* Right Sidebar - Controls (inside map) */}
                    <div className="absolute right-4 top-16 bottom-4 w-64 z-[1000] overflow-y-auto scrollbar-thin pointer-events-auto">
                        {controlMode === 'mission' ? (
                            <MissionControl
                                onUpload={uploadMission}
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

            {/* Footer - no blur for performance */}
            <footer className="absolute bottom-0 left-0 right-0 z-50 bg-gcs-dark/95 border-t border-gcs-border px-4 py-2">
                <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>ESP32 Autonomous Rover Ground Control Station v1.1</span>
                    <LastHeartbeatDisplay />
                </div>
            </footer>
        </div>
    );
}

export default App;
