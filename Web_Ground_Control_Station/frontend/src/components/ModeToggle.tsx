/**
 * Mode Toggle Component
 * 
 * Switches between Mission and Manual control modes.
 */

import { ControlMode } from '../store/roverStore';

interface ModeToggleProps {
    mode: ControlMode;
    onModeChange: (mode: ControlMode) => void;
}

export function ModeToggle({ mode, onModeChange }: ModeToggleProps) {
    return (
        <div className="mode-toggle">
            <button
                onClick={() => onModeChange('mission')}
                className={`mode-toggle-option ${mode === 'mission' ? 'active' : ''}`}
            >
                🎯 Mission
            </button>
            <button
                onClick={() => onModeChange('manual')}
                className={`mode-toggle-option ${mode === 'manual' ? 'active' : ''}`}
            >
                🎮 Manual
            </button>
        </div>
    );
}
