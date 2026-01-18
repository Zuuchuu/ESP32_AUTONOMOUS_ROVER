/**
 * Sensor Status Bar Component
 * 
 * Displays connection status for individual sensors with icon-based indicators.
 */

import { useRoverStore } from '../store/roverStore';

export function SensorStatusBar() {
    const sensorStatus = useRoverStore(state => state.vehicleState.sensorStatus);

    return (
        <div className="flex items-center gap-3">
            <SensorIndicator
                name="Accel"
                state={sensorStatus.accel ? 'on' : 'off'}
                iconBase="sensor_acc"
            />
            <SensorIndicator
                name="Gyro"
                state={sensorStatus.gyro ? 'on' : 'off'}
                iconBase="sensor_gyro"
            />
            <SensorIndicator
                name="Mag"
                state={sensorStatus.mag ? 'on' : 'off'}
                iconBase="sensor_mag"
            />
            <SensorIndicator
                name="GPS"
                state={sensorStatus.gps ? 'on' : 'off'}
                iconBase="sensor_sat"
            />
            <SensorIndicator
                name="TOF"
                state={sensorStatus.tof ? 'on' : 'off'}
                iconBase="sensor_tof"
            />
        </div>
    );
}

interface SensorIndicatorProps {
    name: string;
    state: 'on' | 'off' | 'error';
    iconBase: string;
}

function SensorIndicator({ name, state, iconBase }: SensorIndicatorProps) {
    const iconPath = `/icon/${iconBase}_${state}.png`;

    return (
        <div className="flex flex-col items-center gap-1 px-2 py-1.5 rounded border border-gcs-border bg-gcs-card/50">
            <img
                src={iconPath}
                alt={`${name} ${state}`}
                className="w-8 h-8 object-contain"
            />
            <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wide">
                {name}
            </span>
        </div>
    );
}
