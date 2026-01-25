#ifndef MOTOR_ENCODER_H
#define MOTOR_ENCODER_H

#include <Arduino.h>

// ============================================================================
// MOTOR ENCODER CLASS - 4x Quadrature Decoding
// ============================================================================

class MotorEncoder {
private:
    uint8_t pinA;
    uint8_t pinB;
    bool reverse;
    
    volatile long position;           // Absolute position (preserved for odometry)
    volatile uint8_t lastState;       // For 4x quadrature state machine
    float countsPerRev;               // CPR for this specific motor
    
    // For getPositionDelta() calculation
    long lastSpeedPosition;
    
public:
    MotorEncoder(uint8_t pin_a, uint8_t pin_b, float counts_per_rev, bool reverse_dir = false);
    
    // Lifecycle methods
    void begin();
    void reset();                     // For odometry calibration only
    
    // Data access
    long getPosition();               // Absolute position (for odometry)
    long getPositionDelta();          // Delta since last call (for PID)
    
    // ISR handler (IRAM_ATTR for ESP32)
    void IRAM_ATTR handleInterrupt();
};

#endif // MOTOR_ENCODER_H
