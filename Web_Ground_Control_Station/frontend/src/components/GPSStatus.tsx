/**
 * GPS Status Component
 * 
 * Displays GPS coordinates, satellite count, and fix status.
 */

import { GPSData } from '../store/roverStore';

interface GPSStatusProps {
    gps: GPSData;
}

export function GPSStatus({ gps }: GPSStatusProps) {
    const hasValidPosition = gps.latitude !== 0 || gps.longitude !== 0;

    return (
        <div className="glass-card p-3">
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                    GPS Status
                </h3>
                <div className={`flex items-center gap-1.5 ${hasValidPosition ? 'text-gcs-success' : 'text-gcs-warning'}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${hasValidPosition ? 'bg-gcs-success' : 'bg-gcs-warning'}`} />
                    <span className="text-xs font-medium">{hasValidPosition ? 'Fix' : 'No Fix'}</span>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
                {/* Latitude */}
                <div>
                    <div className="text-slate-500 text-[10px] uppercase">Latitude</div>
                    <div className="font-mono text-gcs-primary">{gps.latitude.toFixed(6)}</div>
                </div>

                {/* Longitude */}
                <div>
                    <div className="text-slate-500 text-[10px] uppercase">Longitude</div>
                    <div className="font-mono text-gcs-primary">{gps.longitude.toFixed(6)}</div>
                </div>

                {/* Altitude */}
                <div>
                    <div className="text-slate-500 text-[10px] uppercase">Altitude</div>
                    <div className="font-mono text-slate-300">{gps.altitude.toFixed(1)} m</div>
                </div>

                {/* Satellites */}
                <div>
                    <div className="text-slate-500 text-[10px] uppercase">Satellites</div>
                    <div className="font-mono text-slate-300">{gps.satellites}</div>
                </div>
            </div>

            {/* HDOP */}
            <div className="mt-2 pt-2 border-t border-gcs-border">
                <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400">HDOP</span>
                    <div className="flex items-center gap-2">
                        <HDOPIndicator hdop={gps.hdop} />
                        <span className="text-xs font-mono text-slate-300">{gps.hdop.toFixed(1)}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

function HDOPIndicator({ hdop }: { hdop: number }) {
    const getColor = () => {
        if (hdop >= 90) return 'bg-slate-600';
        if (hdop < 1) return 'bg-gcs-success';
        if (hdop < 2) return 'bg-gcs-primary';
        if (hdop < 5) return 'bg-gcs-warning';
        return 'bg-gcs-danger';
    };

    return <div className={`w-2 h-2 rounded-full ${getColor()}`} />;
}
