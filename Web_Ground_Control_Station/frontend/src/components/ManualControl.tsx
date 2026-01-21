/**
 * Manual Control Component
 * 
 * Virtual D-pad and speed control for manual rover operation.
 */

import { useState, useCallback, useEffect, useRef } from 'react';

interface ManualControlProps {
    onMove: (direction: string, speed: number) => void;
    onEnable: () => void;
    onDisable: () => void;
}

export function ManualControl({ onMove, onEnable, onDisable }: ManualControlProps) {
    const [isEnabled, setIsEnabled] = useState(false);
    const [speed, setSpeed] = useState(50);
    const [activeDirection, setActiveDirection] = useState<string | null>(null);
    const sendInterval = useRef<ReturnType<typeof setInterval> | null>(null);

    // Handle enabling/disabling
    const toggleEnabled = useCallback(() => {
        if (isEnabled) {
            // Clear any active intervals when disabling
            if (sendInterval.current) {
                clearInterval(sendInterval.current);
                sendInterval.current = null;
            }
            onDisable();
            setIsEnabled(false);
            setActiveDirection(null);
            // Send explicit stop command
            onMove('stop', 0);
        } else {
            onEnable();
            setIsEnabled(true);
        }
    }, [isEnabled, onEnable, onDisable, onMove]);

    // Send movement command
    const startMove = useCallback((direction: string) => {
        // Guard: Don't execute if disabled
        if (!isEnabled) return;

        // Clear any existing interval first
        if (sendInterval.current) {
            clearInterval(sendInterval.current);
            sendInterval.current = null;
        }

        setActiveDirection(direction);
        onMove(direction, speed);

        // Continue sending at 10Hz
        sendInterval.current = setInterval(() => {
            onMove(direction, speed);
        }, 100);
    }, [isEnabled, speed, onMove]);

    const stopMove = useCallback(() => {
        if (sendInterval.current) {
            clearInterval(sendInterval.current);
            sendInterval.current = null;
        }
        setActiveDirection(null);
        onMove('stop', 0);
    }, [onMove]);

    // Keyboard controls
    useEffect(() => {
        if (!isEnabled) return;

        const keyMap: Record<string, string> = {
            'ArrowUp': 'forward',
            'KeyW': 'forward',
            'ArrowDown': 'backward',
            'KeyS': 'backward',
            'ArrowLeft': 'left',
            'KeyA': 'left',
            'ArrowRight': 'right',
            'KeyD': 'right',
            'Space': 'stop',
        };

        const handleKeyDown = (e: KeyboardEvent) => {
            const direction = keyMap[e.code];
            if (direction && direction !== 'stop' && activeDirection !== direction) {
                e.preventDefault();
                startMove(direction);
            } else if (direction === 'stop') {
                e.preventDefault();
                stopMove();
            }
        };

        const handleKeyUp = (e: KeyboardEvent) => {
            const direction = keyMap[e.code];
            if (direction && direction !== 'stop' && activeDirection === direction) {
                stopMove();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, [isEnabled, activeDirection, startMove, stopMove]);

    // Cleanup intervals when disabled
    useEffect(() => {
        if (!isEnabled && sendInterval.current) {
            clearInterval(sendInterval.current);
            sendInterval.current = null;
            setActiveDirection(null);
        }
    }, [isEnabled]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (sendInterval.current) {
                clearInterval(sendInterval.current);
            }
        };
    }, []);

    return (
        <div className="glass-card p-3">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                    Manual Control
                </h3>
                <button
                    onClick={toggleEnabled}
                    className={`control-btn ${isEnabled ? 'control-btn-danger' : 'control-btn-primary'}`}
                >
                    {isEnabled ? 'Disable' : 'Enable'}
                </button>
            </div>

            <div className={`transition-opacity ${isEnabled ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
                {/* Speed slider */}
                <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-slate-400">Speed</span>
                        <span className="telemetry-value">{speed}%</span>
                    </div>
                    <input
                        type="range"
                        min={10}
                        max={100}
                        step={10}
                        value={speed}
                        onChange={(e) => setSpeed(parseInt(e.target.value))}
                        className="w-full h-2 bg-gcs-card rounded-lg appearance-none cursor-pointer
                       [&::-webkit-slider-thumb]:appearance-none
                       [&::-webkit-slider-thumb]:w-4
                       [&::-webkit-slider-thumb]:h-4
                       [&::-webkit-slider-thumb]:rounded-full
                       [&::-webkit-slider-thumb]:bg-gcs-primary
                       [&::-webkit-slider-thumb]:cursor-pointer"
                    />
                </div>

                {/* D-Pad */}
                <div className="flex flex-col items-center gap-2">
                    {/* Forward */}
                    <DirectionButton
                        direction="forward"
                        label="▲"
                        active={activeDirection === 'forward'}
                        onStart={() => startMove('forward')}
                        onStop={stopMove}
                    />

                    {/* Left, Stop, Right */}
                    <div className="flex items-center gap-2">
                        <DirectionButton
                            direction="left"
                            label="◄"
                            active={activeDirection === 'left'}
                            onStart={() => startMove('left')}
                            onStop={stopMove}
                        />
                        <button
                            onClick={stopMove}
                            className="w-16 h-16 rounded-lg bg-gcs-danger/20 border-2 border-gcs-danger
                         text-gcs-danger font-bold text-lg
                         hover:bg-gcs-danger/40 active:scale-95 transition-all"
                        >
                            STOP
                        </button>
                        <DirectionButton
                            direction="right"
                            label="►"
                            active={activeDirection === 'right'}
                            onStart={() => startMove('right')}
                            onStop={stopMove}
                        />
                    </div>

                    {/* Backward */}
                    <DirectionButton
                        direction="backward"
                        label="▼"
                        active={activeDirection === 'backward'}
                        onStart={() => startMove('backward')}
                        onStop={stopMove}
                    />
                </div>

                {/* Keyboard hint */}
                <p className="text-xs text-slate-500 text-center mt-4">
                    Use WASD or Arrow keys • Space to stop
                </p>
            </div>
        </div>
    );
}

interface DirectionButtonProps {
    direction: string;
    label: string;
    active: boolean;
    onStart: () => void;
    onStop: () => void;
}

function DirectionButton({ label, active, onStart, onStop }: DirectionButtonProps) {
    return (
        <button
            className={`w-16 h-16 rounded-lg border-2 font-bold text-2xl
                  transition-all select-none
                  ${active
                    ? 'bg-gcs-primary border-gcs-primary text-white scale-95'
                    : 'bg-gcs-card border-gcs-border text-slate-400 hover:border-gcs-primary hover:text-gcs-primary'
                }`}
            onMouseDown={onStart}
            onMouseUp={onStop}
            onMouseLeave={onStop}
            onTouchStart={(e) => { e.preventDefault(); onStart(); }}
            onTouchEnd={(e) => { e.preventDefault(); onStop(); }}
        >
            {label}
        </button>
    );
}
