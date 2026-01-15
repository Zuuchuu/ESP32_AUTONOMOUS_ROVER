/**
 * Attitude Indicator Component
 * 
 * Displays pitch and roll in an artificial horizon style.
 */

interface AttitudeIndicatorProps {
    pitch: number;
    roll: number;
}

export function AttitudeIndicator({ pitch, roll }: AttitudeIndicatorProps) {
    // Clamp pitch to reasonable display range (-60 to 60 degrees)
    const clampedPitch = Math.max(-60, Math.min(60, pitch));

    // Convert pitch to vertical offset (pixels per degree)
    const pitchOffset = clampedPitch * 2;

    return (
        <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
                Attitude
            </h3>

            <div className="flex items-center gap-4">
                {/* Artificial Horizon */}
                <div
                    className="w-32 h-32 rounded-full overflow-hidden border-4 border-gcs-border relative"
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
                        style={{ transform: `rotate(${roll}deg)` }}
                    >
                        <div className="w-3 h-3 rounded-full bg-yellow-400 border-2 border-white shadow-lg" />
                        <div className="absolute w-16 h-0.5 bg-yellow-400" />
                    </div>

                    {/* Pitch ladder marks */}
                    {[-30, -20, -10, 10, 20, 30].map((mark) => (
                        <div
                            key={mark}
                            className="absolute left-1/2 -translate-x-1/2 flex items-center gap-1"
                            style={{
                                top: `${50 - mark * 2 + pitchOffset}%`,
                                opacity: 0.7,
                            }}
                        >
                            <div className="w-4 h-0.5 bg-white" />
                            <span className="text-[8px] text-white">{Math.abs(mark)}</span>
                            <div className="w-4 h-0.5 bg-white" />
                        </div>
                    ))}
                </div>

                {/* Values */}
                <div className="space-y-3">
                    <div>
                        <div className="telemetry-label">Roll</div>
                        <div className="telemetry-value">{roll.toFixed(1)}°</div>
                    </div>
                    <div>
                        <div className="telemetry-label">Pitch</div>
                        <div className="telemetry-value">{pitch.toFixed(1)}°</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
