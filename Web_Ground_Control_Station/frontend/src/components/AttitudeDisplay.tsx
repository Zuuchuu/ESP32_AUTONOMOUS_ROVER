/**
 * Attitude Display Component
 * 
 * Combined display showing pitch/roll (artificial horizon) and heading (compass) side-by-side.
 * OPTIMIZED: Uses CSS custom properties and GPU-accelerated animations for smooth 60fps rendering.
 */

import { useMemo, useRef, useEffect, useState } from 'react';
import { useRoverStore } from '../store/roverStore';

// Pre-computed pitch ladder marks for performance (±60° with 10° increments)
const PITCH_MARKS = [-60, -50, -40, -30, -20, -10, 10, 20, 30, 40, 50, 60];

// Pre-computed cardinal directions
const CARDINALS = [
    { label: 'N', angle: 0, color: '#ef4444' },  // red
    { label: 'E', angle: 90, color: '#cbd5e1' }, // slate-300
    { label: 'S', angle: 180, color: '#cbd5e1' },
    { label: 'W', angle: 270, color: '#cbd5e1' },
] as const;

// Pre-computed tick marks (36 ticks, 10° apart)
const TICK_MARKS = Array.from({ length: 36 }, (_, i) => ({
    angle: i * 10,
    isMajor: i % 9 === 0,
}));

export function AttitudeDisplay() {
    // Select specific values to minimize re-renders
    const pitch = useRoverStore(state => state.vehicleState.attitude.pitch);
    const roll = useRoverStore(state => state.vehicleState.attitude.roll);
    const heading = useRoverStore(state => state.vehicleState.attitude.yaw);

    // Clamp pitch to reasonable display range
    const clampedPitch = Math.max(-60, Math.min(60, pitch));
    const pitchOffset = clampedPitch * 2;

    // Normalize heading (0-360)
    const normalizedHeading = ((heading % 360) + 360) % 360;

    // Track smooth compass rotation (prevent 360->0 spin)
    const previousHeadingRef = useRef(normalizedHeading);
    const accumulatedRotationRef = useRef(0);
    const [smoothHeading, setSmoothHeading] = useState(0);

    useEffect(() => {
        const prev = previousHeadingRef.current;
        const current = normalizedHeading;
        let delta = current - prev;

        // Detect 360°/0° boundary crossing
        if (delta > 180) {
            // Crossed from 0° to 360° (e.g., 1° -> 359°)
            delta -= 360;
        } else if (delta < -180) {
            // Crossed from 360° to 0° (e.g., 359° -> 1°)
            delta += 360;
        }

        // Accumulate rotation for smooth animation
        accumulatedRotationRef.current += delta;
        setSmoothHeading(-accumulatedRotationRef.current);

        previousHeadingRef.current = current;
    }, [normalizedHeading]);

    // Memoize cardinal direction text
    const cardinalText = useMemo(() => getCardinalDirection(normalizedHeading), [normalizedHeading]);

    return (
        <div className="glass-card p-3">
            <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
                Attitude
            </h3>

            <div className="grid grid-cols-2 gap-4">
                {/* Artificial Horizon - Pitch/Roll */}
                <div className="flex flex-col items-center">
                    <div
                        className="attitude-horizon"
                        style={{
                            '--roll': `${-roll}deg`,
                            '--pitch-offset': `${pitchOffset}px`,
                        } as React.CSSProperties}
                    >
                        {/* Sky gradient */}
                        <div className="attitude-sky" />

                        {/* Ground gradient */}
                        <div className="attitude-ground" />

                        {/* Horizon line */}
                        <div className="attitude-horizon-line" />

                        {/* Pitch ladder marks */}
                        <div className="attitude-ladder">
                            {PITCH_MARKS.map((deg) => (
                                <div
                                    key={deg}
                                    className="attitude-ladder-mark"
                                    style={{ '--deg-offset': `${deg * 0.67}px` } as React.CSSProperties}
                                >
                                    <div className="attitude-ladder-line" />
                                    <span className="attitude-ladder-text">{Math.abs(deg)}</span>
                                    <div className="attitude-ladder-line" />
                                </div>
                            ))}
                        </div>

                        {/* Center aircraft symbol (fixed - doesn't rotate) */}
                        <div className="attitude-aircraft">
                            <div className="attitude-aircraft-dot" />
                            <div className="attitude-aircraft-wings" />
                        </div>
                    </div>

                    {/* Pitch/Roll values */}
                    <div className="mt-2 text-center">
                        <div className="text-xs text-slate-400">
                            P: <span className="text-gcs-primary font-mono tabular-nums">{pitch.toFixed(1)}°</span>
                        </div>
                        <div className="text-xs text-slate-400">
                            R: <span className="text-gcs-primary font-mono tabular-nums">{roll.toFixed(1)}°</span>
                        </div>
                    </div>
                </div>

                {/* Compass - Heading */}
                <div className="flex flex-col items-center">
                    <div className="compass-container">
                        {/* Outer ring / bezel */}
                        <div className="compass-bezel">
                            {/* Rotating compass rose */}
                            <div
                                className="compass-rose-rotating"
                                style={{ '--heading': `${smoothHeading}deg` } as React.CSSProperties}
                            >
                                {/* Tick marks */}
                                {TICK_MARKS.map(({ angle, isMajor }) => (
                                    <div
                                        key={angle}
                                        className="compass-tick"
                                        style={{ '--tick-angle': `${angle}deg` } as React.CSSProperties}
                                    >
                                        <div className={isMajor ? 'compass-tick-major' : 'compass-tick-minor'} />
                                    </div>
                                ))}

                                {/* Cardinal markers */}
                                {CARDINALS.map(({ label, angle, color }) => (
                                    <div
                                        key={label}
                                        className="compass-cardinal"
                                        style={{
                                            '--cardinal-angle': `${angle}deg`,
                                            '--counter-rotate': `${-angle - smoothHeading}deg`,
                                            color,
                                        } as React.CSSProperties}
                                    >
                                        <span className="compass-cardinal-text">{label}</span>
                                    </div>
                                ))}
                            </div>

                            {/* Center pointer (fixed) */}
                            <div className="compass-center-pointer">
                                <div className="compass-pointer-triangle" />
                                <div className="compass-pointer-dot" />
                            </div>
                        </div>
                    </div>

                    {/* Heading value */}
                    <div className="mt-1.5 text-center">
                        <div className="text-base font-mono text-gcs-primary tabular-nums">
                            {normalizedHeading.toFixed(0)}°
                        </div>
                        <div className="text-[10px] text-slate-400">{cardinalText}</div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function getCardinalDirection(heading: number): string {
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
        'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    const index = Math.round(heading / 22.5) % 16;
    return directions[index];
}
