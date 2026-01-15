/**
 * IMU Calibration Component
 * 
 * Displays BNO055 calibration status with visual indicators.
 */

import type { IMUCalibration } from '../store/roverStore';

interface IMUCalibrationProps {
    calibration: IMUCalibration;
}

export function IMUCalibration({ calibration }: IMUCalibrationProps) {
    return (
        <div className="glass-card p-3">
            <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
                IMU Calibration
            </h3>

            <div className="grid grid-cols-2 gap-3">
                <CalibrationIndicator label="System" level={calibration.system} />
                <CalibrationIndicator label="Accel" level={calibration.accelerometer} />
                <CalibrationIndicator label="Gyro" level={calibration.gyroscope} />
                <CalibrationIndicator label="Mag" level={calibration.magnetometer} />
            </div>
        </div>
    );
}

interface CalibrationIndicatorProps {
    label: string;
    level: number; // 0-3
}

function CalibrationIndicator({ label, level }: CalibrationIndicatorProps) {
    return (
        <div>
            <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-400">{label}</span>
                <span className="text-xs font-mono text-gcs-primary">{level}/3</span>
            </div>

            {/* Calibration level bars */}
            <div className="flex gap-1">
                {[0, 1, 2, 3].map((bar) => (
                    <div
                        key={bar}
                        className={`flex-1 h-2 rounded-sm transition-colors ${bar < level
                            ? level === 3
                                ? 'bg-gcs-success'
                                : level === 2
                                    ? 'bg-gcs-primary'
                                    : 'bg-gcs-warning'
                            : 'bg-slate-700'
                            }`}
                    />
                ))}
            </div>
        </div>
    );
}
