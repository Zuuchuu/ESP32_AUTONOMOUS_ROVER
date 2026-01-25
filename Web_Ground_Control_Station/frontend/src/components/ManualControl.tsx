/**
 * Manual Control Component
 * 
 * Virtual D-pad and speed control for manual rover operation.
 * Supports multi-button input for curved movement (e.g., Forward + Right).
 */

import { useState, useCallback, useEffect, useRef } from 'react';

interface ManualControlProps {
    onMove: (direction: string, speed: number) => void;
    onEnable: () => void;
    onDisable: () => void;
}

// Valid base directions
type BaseDirection = 'forward' | 'backward' | 'left' | 'right';

export function ManualControl({ onMove, onEnable, onDisable }: ManualControlProps) {
    const [isEnabled, setIsEnabled] = useState(false);
    const [speed, setSpeed] = useState(50);
    // Track all currently pressed buttons
    const [activeButtons, setActiveButtons] = useState<Set<BaseDirection>>(new Set());
    const sendInterval = useRef<ReturnType<typeof setInterval> | null>(null);
    // Ref to track buttons synchronously (React state updates are async)
    const activeButtonsRef = useRef<Set<BaseDirection>>(new Set());

    // Compute combined direction from active buttons
    const computeDirection = useCallback((buttons: Set<BaseDirection>): string | null => {
        const hasForward = buttons.has('forward');
        const hasBackward = buttons.has('backward');
        const hasLeft = buttons.has('left');
        const hasRight = buttons.has('right');

        // Conflicting directions cancel out
        if (hasForward && hasBackward) return null; // Ignore vertical conflict
        if (hasLeft && hasRight) return null;       // Ignore horizontal conflict

        // Determine primary (forward/backward) and secondary (left/right)
        let primary: string | null = null;
        let secondary: string | null = null;

        if (hasForward) primary = 'forward';
        else if (hasBackward) primary = 'backward';

        if (hasLeft) secondary = 'left';
        else if (hasRight) secondary = 'right';

        // Combine directions
        if (primary && secondary) {
            return `${primary}_${secondary}`; // e.g., "forward_right"
        } else if (primary) {
            return primary;
        } else if (secondary) {
            return secondary;
        }

        return null; // No direction
    }, []);

    // Send movement command based on current button state
    const sendCurrentMovement = useCallback((buttons: Set<BaseDirection>) => {
        const direction = computeDirection(buttons);
        if (direction) {
            onMove(direction, speed);
        } else if (buttons.size === 0) {
            onMove('stop', 0);
        }
        // If conflicting (null but buttons present), maintain previous state
    }, [computeDirection, speed, onMove]);

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
            setActiveButtons(new Set());
            // Send explicit stop command
            onMove('stop', 0);
        } else {
            onEnable();
            setIsEnabled(true);
        }
    }, [isEnabled, onEnable, onDisable, onMove]);

    // Add a button press
    const pressButton = useCallback((direction: BaseDirection) => {
        if (!isEnabled) return;

        // Update ref synchronously
        activeButtonsRef.current = new Set(activeButtonsRef.current);
        activeButtonsRef.current.add(direction);

        // Update React state
        setActiveButtons(new Set(activeButtonsRef.current));
    }, [isEnabled]);

    // Remove a button press - CRITICAL: send stop immediately if last button released
    const releaseButton = useCallback((direction: BaseDirection) => {
        console.log('[ManualControl] releaseButton called:', direction, 'remaining:', activeButtonsRef.current.size - 1);

        // Update ref synchronously FIRST
        activeButtonsRef.current = new Set(activeButtonsRef.current);
        activeButtonsRef.current.delete(direction);

        // Clear interval immediately
        if (sendInterval.current) {
            clearInterval(sendInterval.current);
            sendInterval.current = null;
        }

        // If no buttons remain, send stop IMMEDIATELY (synchronously, before React update)
        if (activeButtonsRef.current.size === 0) {
            console.log('[ManualControl] Sending STOP');
            onMove('stop', 0);
        }

        // Update React state (this may be async/batched, but stop already sent)
        setActiveButtons(new Set(activeButtonsRef.current));
    }, [onMove]);

    // Effect: When activeButtons changes, update movement command
    useEffect(() => {
        if (!isEnabled) return;

        // Clear previous interval
        if (sendInterval.current) {
            clearInterval(sendInterval.current);
            sendInterval.current = null;
        }

        // Send immediately
        sendCurrentMovement(activeButtons);

        // If there are active buttons, continue sending at 20Hz (50ms)
        if (activeButtons.size > 0) {
            sendInterval.current = setInterval(() => {
                sendCurrentMovement(activeButtons);
            }, 50);
        }
    }, [activeButtons, isEnabled, sendCurrentMovement]);

    // Stop all movement
    const stopAll = useCallback(() => {
        if (sendInterval.current) {
            clearInterval(sendInterval.current);
            sendInterval.current = null;
        }
        setActiveButtons(new Set());
        onMove('stop', 0);
    }, [onMove]);

    // Keyboard controls - track multiple keys
    useEffect(() => {
        if (!isEnabled) return;

        const keyMap: Record<string, BaseDirection> = {
            'ArrowUp': 'forward',
            'KeyW': 'forward',
            'ArrowDown': 'backward',
            'KeyS': 'backward',
            'ArrowLeft': 'left',
            'KeyA': 'left',
            'ArrowRight': 'right',
            'KeyD': 'right',
        };

        const handleKeyDown = (e: KeyboardEvent) => {
            // Space to stop
            if (e.code === 'Space') {
                e.preventDefault();
                stopAll();
                return;
            }

            // CRITICAL: Ignore key repeat events (when holding key down)
            // Without this, pressButton is called repeatedly which can desync state
            if (e.repeat) return;

            const direction = keyMap[e.code];
            if (direction) {
                e.preventDefault();
                console.log('[Keyboard] KeyDown:', direction);
                pressButton(direction);
            }
        };

        const handleKeyUp = (e: KeyboardEvent) => {
            const direction = keyMap[e.code];
            if (direction) {
                console.log('[Keyboard] KeyUp:', direction);
                releaseButton(direction);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, [isEnabled, pressButton, releaseButton, stopAll]);

    // Cleanup intervals when disabled
    useEffect(() => {
        if (!isEnabled && sendInterval.current) {
            clearInterval(sendInterval.current);
            sendInterval.current = null;
            setActiveButtons(new Set());
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

    // Check if a direction is active (for highlighting)
    const isActive = (dir: BaseDirection) => activeButtons.has(dir);

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
                        active={isActive('forward')}
                        onStart={() => pressButton('forward')}
                        onStop={() => releaseButton('forward')}
                    />

                    {/* Left, Stop, Right */}
                    <div className="flex items-center gap-2">
                        <DirectionButton
                            direction="left"
                            label="◄"
                            active={isActive('left')}
                            onStart={() => pressButton('left')}
                            onStop={() => releaseButton('left')}
                        />
                        <button
                            onClick={stopAll}
                            className="w-16 h-16 rounded-lg bg-gcs-danger/20 border-2 border-gcs-danger
                         text-gcs-danger font-bold text-lg
                         hover:bg-gcs-danger/40 active:scale-95 transition-all"
                        >
                            STOP
                        </button>
                        <DirectionButton
                            direction="right"
                            label="►"
                            active={isActive('right')}
                            onStart={() => pressButton('right')}
                            onStop={() => releaseButton('right')}
                        />
                    </div>

                    {/* Backward */}
                    <DirectionButton
                        direction="backward"
                        label="▼"
                        active={isActive('backward')}
                        onStart={() => pressButton('backward')}
                        onStop={() => releaseButton('backward')}
                    />
                </div>

                {/* Keyboard hint */}
                <p className="text-xs text-slate-500 text-center mt-4">
                    Use WASD or Arrow keys • Hold multiple for curves • Space to stop
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
