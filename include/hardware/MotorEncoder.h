#ifndef MOTOR_ENCODER_H
#define MOTOR_ENCODER_H

#include <Arduino.h>

// ============================================================================
// MOTOR ENCODER CLASS
// ============================================================================

class MotorEncoder {
private:
    uint8_t pinA;
    uint8_t pinB;
    bool reverse;
    
    volatile long position;
    volatile unsigned long lastInterruptTime;
    float countsPerRev;
    
public:
    MotorEncoder(uint8_t pin_a, uint8_t pin_b, float counts_per_rev, bool reverse_dir = false);
    
    // Lifecycle methods
    void begin();
    void reset();
    
    // Data access
    long getPosition();
    float getRPM();
    
    // ISR handler (IRAM_ATTR for ESP32)
    void IRAM_ATTR handleInterrupt();
};

#endif // MOTOR_ENCODER_H
