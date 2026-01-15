/**
 * Sensor Status Bar Component
 * 
 * Displays connection status for individual sensors with iNAV-style icons.
 */

import { SensorStatus } from '../store/roverStore';

interface SensorStatusBarProps {
    sensorStatus: SensorStatus;
}

export function SensorStatusBar({ sensorStatus }: SensorStatusBarProps) {
    // For now, we'll assume IMU status applies to all three (Accel, Gyro, Mag)
    const accelConnected = sensorStatus.imu;
    const gyroConnected = sensorStatus.imu;
    const magConnected = sensorStatus.imu;

    return (
        <div className="flex items-center gap-3">
            {/* Accelerometer */}
            <SensorIcon
                connected={accelConnected}
                icon={<AccelIcon />}
            />

            {/* Gyroscope */}
            <SensorIcon
                connected={gyroConnected}
                icon={<GyroIcon />}
            />

            {/* Magnetometer */}
            <SensorIcon
                connected={magConnected}
                icon={<MagIcon />}
            />

            {/* GPS */}
            <SensorIcon
                connected={sensorStatus.gps}
                icon={<GPSIcon />}
            />

            {/* TOF (Sonar) */}
            <SensorIcon
                connected={sensorStatus.tof}
                icon={<SonarIcon />}
            />
        </div>
    );
}

interface SensorIconProps {
    connected: boolean;
    icon: React.ReactNode;
}

function SensorIcon({ connected, icon }: SensorIconProps) {
    return (
        <div className={`transition-opacity ${connected ? 'opacity-100' : 'opacity-30'}`}>
            <div className={connected ? 'text-gcs-success' : 'text-slate-600'}>
                {icon}
            </div>
        </div>
    );
}

// iNAV-style SVG Icons
function AccelIcon() {
    return (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {/* Accelerometer - 3-axis arrows */}
            <path d="M12 2v8m0 0l-3-3m3 3l3-3" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M2 12h8m0 0l-3-3m3 3l-3 3" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M14 12h8m0 0l-3-3m3 3l-3 3" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="12" cy="12" r="2" fill="currentColor" />
        </svg>
    );
}

function GyroIcon() {
    return (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {/* Gyroscope - rotating circle with axis */}
            <circle cx="12" cy="12" r="8" strokeLinecap="round" />
            <path d="M12 4v16M4 12h16" strokeLinecap="round" />
            <circle cx="12" cy="12" r="3" fill="currentColor" />
            <path d="M16 8l4-4M8 16l-4 4M16 16l4 4M8 8l-4-4" strokeLinecap="round" opacity="0.5" />
        </svg>
    );
}

function MagIcon() {
    return (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {/* Magnetometer - compass/magnet */}
            <path d="M12 2L8 6h8l-4-4z" fill="currentColor" strokeLinejoin="round" />
            <path d="M12 22l-4-4h8l-4 4z" fill="currentColor" strokeLinejoin="round" />
            <circle cx="12" cy="12" r="6" strokeLinecap="round" />
            <path d="M12 6v12" strokeLinecap="round" />
        </svg>
    );
}

function GPSIcon() {
    return (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {/* GPS - satellite signal */}
            <circle cx="12" cy="12" r="2" fill="currentColor" />
            <circle cx="12" cy="12" r="6" strokeLinecap="round" opacity="0.6" />
            <circle cx="12" cy="12" r="10" strokeLinecap="round" opacity="0.3" />
            <path d="M12 2v3m0 14v3M2 12h3m14 0h3" strokeLinecap="round" />
        </svg>
    );
}

function SonarIcon() {
    return (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {/* Sonar/TOF - ultrasonic waves */}
            <path d="M4 12h3" strokeLinecap="round" />
            <path d="M7 9c2-2 2-6 0-6M7 15c2 2 2 6 0 6" strokeLinecap="round" opacity="0.6" />
            <path d="M10 7c3-3 3-8 0-8M10 17c3 3 3 8 0 8" strokeLinecap="round" opacity="0.4" />
            <circle cx="16" cy="12" r="6" strokeLinecap="round" />
            <circle cx="16" cy="12" r="3" fill="currentColor" />
        </svg>
    );
}
