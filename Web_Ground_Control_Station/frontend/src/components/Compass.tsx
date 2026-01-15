/**
 * Compass Component
 * 
 * Displays heading with a rotating compass rose.
 */

interface CompassProps {
    heading: number;
}

export function Compass({ heading }: CompassProps) {
    // Normalize heading to 0-360
    const normalizedHeading = ((heading % 360) + 360) % 360;

    // Cardinal directions
    const cardinals = [
        { label: 'N', angle: 0 },
        { label: 'NE', angle: 45, size: 'sm' },
        { label: 'E', angle: 90 },
        { label: 'SE', angle: 135, size: 'sm' },
        { label: 'S', angle: 180 },
        { label: 'SW', angle: 225, size: 'sm' },
        { label: 'W', angle: 270 },
        { label: 'NW', angle: 315, size: 'sm' },
    ];

    return (
        <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
                Heading
            </h3>

            <div className="flex items-center gap-4">
                {/* Compass Rose */}
                <div className="relative w-32 h-32">
                    {/* Outer ring */}
                    <div className="absolute inset-0 rounded-full border-4 border-gcs-border bg-gcs-dark">
                        {/* Rotating compass */}
                        <div
                            className="absolute inset-2 rounded-full transition-transform duration-200"
                            style={{ transform: `rotate(${-normalizedHeading}deg)` }}
                        >
                            {/* Cardinal markers */}
                            {cardinals.map(({ label, angle, size }) => (
                                <div
                                    key={label}
                                    className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
                                    style={{ transform: `rotate(${angle}deg) translateY(-44px)` }}
                                >
                                    <span
                                        className={`block font-bold ${size === 'sm' ? 'text-xs text-slate-500' : 'text-sm text-slate-300'
                                            } ${label === 'N' ? 'text-gcs-danger' : ''}`}
                                        style={{ transform: `rotate(${-angle + normalizedHeading}deg)` }}
                                    >
                                        {label}
                                    </span>
                                </div>
                            ))}

                            {/* Tick marks */}
                            {Array.from({ length: 36 }).map((_, i) => (
                                <div
                                    key={i}
                                    className="absolute left-1/2 top-0 -translate-x-1/2"
                                    style={{
                                        transform: `rotate(${i * 10}deg)`,
                                        transformOrigin: '50% 56px',
                                    }}
                                >
                                    <div
                                        className={`w-0.5 ${i % 9 === 0 ? 'h-3 bg-slate-400' : 'h-1.5 bg-slate-600'
                                            }`}
                                    />
                                </div>
                            ))}
                        </div>

                        {/* Center pointer (fixed) */}
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <div className="w-0 h-0 border-l-8 border-r-8 border-b-[16px] border-transparent border-b-gcs-danger -translate-y-6" />
                            <div className="absolute w-3 h-3 rounded-full bg-gcs-card border-2 border-gcs-border" />
                        </div>
                    </div>
                </div>

                {/* Heading value */}
                <div>
                    <div className="telemetry-label">Degrees</div>
                    <div className="telemetry-value text-2xl">{normalizedHeading.toFixed(0)}°</div>
                    <div className="text-sm text-slate-400 mt-1">
                        {getCardinalDirection(normalizedHeading)}
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
