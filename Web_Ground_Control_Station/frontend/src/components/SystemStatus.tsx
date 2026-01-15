/**
 * System Status Component
 * 
 * Displays battery, WiFi, mode, and connection status.
 */

import { SystemStatus as SystemStatusType } from '../store/roverStore';

interface SystemStatusProps {
    system: SystemStatusType;
    connected: boolean;
    socketConnected: boolean;
}

export function SystemStatus({ system, connected, socketConnected }: SystemStatusProps) {
    return (
        <div className="glass-card p-3">
            <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
                System Status
            </h3>

            <div className="space-y-3">
                {/* Connection Status */}
                <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">Backend</span>
                    <div className={`flex items-center gap-2 ${socketConnected ? 'text-gcs-success' : 'text-gcs-danger'}`}>
                        <div className={`w-2 h-2 rounded-full ${socketConnected ? 'bg-gcs-success' : 'bg-gcs-danger'}`} />
                        <span className="text-sm font-medium">{socketConnected ? 'Connected' : 'Disconnected'}</span>
                    </div>
                </div>

                <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">Rover</span>
                    <div className={`flex items-center gap-2 ${connected ? 'text-gcs-success' : 'text-gcs-danger'}`}>
                        <div className={`w-2 h-2 rounded-full ${connected ? 'bg-gcs-success' : 'bg-gcs-danger'}`} />
                        <span className="text-sm font-medium">{connected ? 'Connected' : 'Disconnected'}</span>
                    </div>
                </div>

                {/* WiFi Signal */}
                <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">WiFi Signal</span>
                    <div className="flex items-center gap-2">
                        <WifiIcon strength={system.wifiStrength} />
                        <span className="text-sm font-mono text-gcs-primary">
                            {system.wifiStrength} dBm
                        </span>
                    </div>
                </div>

                {/* Mode */}
                <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">Mode</span>
                    <span className={`px-2 py-1 rounded text-xs font-bold ${getModeColor(system.mode)}`}>
                        {system.mode}
                    </span>
                </div>

                {/* Uptime */}
                <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">Uptime</span>
                    <span className="text-sm font-mono text-slate-300">
                        {formatUptime(system.uptime)}
                    </span>
                </div>
            </div>
        </div>
    );
}

function WifiIcon({ strength }: { strength: number }) {
    // WiFi bars based on dBm
    let bars = 0;
    if (strength > -50) bars = 4;
    else if (strength > -60) bars = 3;
    else if (strength > -70) bars = 2;
    else if (strength > -80) bars = 1;

    return (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
            {[0, 1, 2, 3].map((i) => (
                <path
                    key={i}
                    d={getWifiArcPath(i)}
                    stroke={i < bars ? '#0ea5e9' : '#334155'}
                    strokeWidth="2"
                    strokeLinecap="round"
                />
            ))}
        </svg>
    );
}

function getWifiArcPath(index: number): string {
    const paths = [
        'M12 18h.01', // Dot
        'M8.5 14.5a5 5 0 017 0', // Arc 1
        'M5 11a10 10 0 0114 0', // Arc 2
        'M1.5 7.5a15 15 0 0121 0', // Arc 3
    ];
    return paths[index];
}


function getModeColor(mode: string): string {
    switch (mode) {
        case 'MANUAL': return 'bg-gcs-warning text-black';
        case 'AUTO': return 'bg-gcs-success text-black';
        default: return 'bg-slate-600 text-white';
    }
}

function formatUptime(ms: number): string {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
        return `${hours}h ${minutes % 60}m`;
    }
    if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
}
