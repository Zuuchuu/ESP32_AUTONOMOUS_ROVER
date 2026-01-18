/**
 * Attitude Display Component
 * 
 * Combined display showing pitch/roll (artificial horizon) and heading (compass) side-by-side.
 */

import { useRoverStore } from '../store/roverStore';

export function AttitudeDisplay() {
    // Select specific values to minimize re-renders
    const pitch = useRoverStore(state => state.vehicleState.attitude.pitch);
    const roll = useRoverStore(state => state.vehicleState.attitude.roll);
    const heading = useRoverStore(state => state.vehicleState.attitude.yaw); // yaw is heading

    // Clamp pitch to reasonable display range
    const clampedPitch = Math.max(-60, Math.min(60, pitch));
    const pitchOffset = clampedPitch * 2;

    // Normalize heading
    const normalizedHeading = ((heading % 360) + 360) % 360;

    return (
        <div className="glass-card p-3">
            <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
                Attitude
            </h3>

            <div className="grid grid-cols-2 gap-4">
                {/* Artificial Horizon - Pitch/Roll */}
                <div className="flex flex-col items-center">
                    <div
                        className="w-20 h-20 rounded-full overflow-hidden border-3 border-gcs-border relative"
                        style={{ transform: `rotate(${-roll}deg)` }}
                    >
                        {/* Sky */}
                        <div
                            className="absolute inset-0 transition-transform duration-100"
                            style={{
                                background: 'linear-gradient(to bottom, #3b82f6 0%, #60a5fa 100%)',
                                transform: `translateY(${pitchOffset}px)`,
                            }}
                        />

                        {/* Ground */}
                        <div
                            className="absolute inset-0 transition-transform duration-100"
                            style={{
                                background: 'linear-gradient(to bottom, #78350f 0%, #451a03 100%)',
                                top: '50%',
                                transform: `translateY(${pitchOffset}px)`,
                            }}
                        />

                        {/* Pitch ladder marks */}
                        <div
                            className="absolute inset-0 transition-transform duration-100"
                            style={{ transform: `translateY(${pitchOffset}px)` }}
                        >
                            {/* Pitch marks at ±10°, ±20°, ±30° */}
                            {[-30, -20, -10, 10, 20, 30].map((deg) => {
                                // The original instruction had `(deg / clampedPitch) * pitchOffset` which is incorrect.
                                // The offset should be relative to the center of the display, not scaled by clampedPitch.
                                // A fixed scaling factor (e.g., 0.67px per degree) is more appropriate for a visual ladder.
                                return (
                                    <div
                                        key={deg}
                                        className="absolute left-1/2 -translate-x-1/2 flex items-center gap-1"
                                        style={{ top: `calc(50% - ${deg * 0.67}px)` }}
                                    >
                                        <div className="w-4 h-px bg-white/80" />
                                        <span className="text-[8px] text-white/80 font-mono">{Math.abs(deg)}</span>
                                        <div className="w-4 h-px bg-white/80" />
                                    </div>
                                );
                            })}
                        </div>

                        {/* Horizon line */}
                        <div
                            className="absolute left-0 right-0 h-0.5 bg-white"
                            style={{
                                top: '50%',
                                transform: `translateY(${pitchOffset}px)`,
                                boxShadow: '0 0 4px rgba(255,255,255,0.5)',
                            }}
                        />

                        {/* Center reference (fixed) */}
                        <div
                            className="absolute inset-0 flex items-center justify-center pointer-events-none"
                        >
                            <div className="w-2 h-2 rounded-full bg-yellow-400 border border-white shadow-lg" />
                            <div className="absolute w-10 h-px bg-yellow-400" />
                        </div>
                    </div>

                    {/* Pitch/Roll values */}
                    <div className="mt-2 text-center">
                        <div className="text-xs text-slate-400">P: <span className="text-gcs-primary font-mono">{pitch.toFixed(1)}°</span></div>
                        <div className="text-xs text-slate-400">R: <span className="text-gcs-primary font-mono">{roll.toFixed(1)}°</span></div>
                    </div>
                </div>


                {/* Compass - Heading */}
                <div className="flex flex-col items-center">
                    <div className="relative w-20 h-20">
                        {/* Outer ring */}
                        <div className="absolute inset-0 rounded-full border-2 border-gcs-border bg-gcs-dark">
                            {/* Rotating compass */}
                            <div
                                className="absolute inset-1 rounded-full transition-transform duration-200"
                                style={{ transform: `rotate(${-normalizedHeading}deg)` }}
                            >
                                {/* Cardinal markers */}
                                {[
                                    { label: 'N', angle: 0, color: 'text-gcs-danger' },
                                    { label: 'E', angle: 90, color: 'text-slate-300' },
                                    { label: 'S', angle: 180, color: 'text-slate-300' },
                                    { label: 'W', angle: 270, color: 'text-slate-300' },
                                ].map(({ label, angle, color }) => (
                                    <div
                                        key={label}
                                        className="absolute"
                                        style={{
                                            left: '50%',
                                            top: '50%',
                                            transform: `translate(-50%, -50%) rotate(${angle}deg) translateY(-32px) rotate(${-angle + normalizedHeading}deg)`
                                        }}
                                    >
                                        <span className={`block text-[10px] font-bold ${color}`}>
                                            {label}
                                        </span>
                                    </div>
                                ))}

                                {/* Tick marks */}
                                {Array.from({ length: 36 }).map((_, i) => (
                                    <div
                                        key={i}
                                        className="absolute left-1/2 top-1/2"
                                        style={{
                                            transform: `translate(-50%, -50%) rotate(${i * 10}deg) translateY(-36px)`,
                                        }}
                                    >
                                        <div
                                            className={`w-0.5 ${i % 9 === 0 ? 'h-2 bg-slate-400' : 'h-1 bg-slate-600'
                                                }`}
                                        />
                                    </div>
                                ))}
                            </div>

                            {/* Center pointer (fixed) */}
                            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                <div className="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[8px] border-transparent border-b-gcs-danger"
                                    style={{ transform: 'translateY(-3px)' }} />
                                <div className="absolute w-1.5 h-1.5 rounded-full bg-gcs-card border border-gcs-border" />
                            </div>
                        </div>
                    </div>

                    {/* Heading value */}
                    <div className="mt-1.5 text-center">
                        <div className="text-base font-mono text-gcs-primary">{normalizedHeading.toFixed(0)}°</div>
                        <div className="text-[10px] text-slate-400">{getCardinalDirection(normalizedHeading)}</div>
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
