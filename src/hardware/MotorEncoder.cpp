#include "hardware/MotorEncoder.h"

// ============================================================================
// STATIC ISR INFRASTRUCTURE
// ============================================================================

static MotorEncoder* encoder_instances[2] = {nullptr, nullptr};
static int instance_count = 0;

// Lookup table for 4x quadrature state transitions
// Index = (prevState << 2) | currState where state = (A << 1) | B
// Values: 0 = no change, 1 = forward, -1 = backward
// Invalid transitions (skipped states) treated as no change
static const int8_t QUADRATURE_LUT[16] = {
     0,  // 00 -> 00: no change
    -1,  // 00 -> 01: CCW
     1,  // 00 -> 10: CW
     0,  // 00 -> 11: invalid (skipped)
     1,  // 01 -> 00: CW
     0,  // 01 -> 01: no change
     0,  // 01 -> 10: invalid (skipped)
    -1,  // 01 -> 11: CCW
    -1,  // 10 -> 00: CCW
     0,  // 10 -> 01: invalid (skipped)
     0,  // 10 -> 10: no change
     1,  // 10 -> 11: CW
     0,  // 11 -> 00: invalid (skipped)
     1,  // 11 -> 01: CW
    -1,  // 11 -> 10: CCW
     0   // 11 -> 11: no change
};

// ISR trampolines - call both channels on any edge
void IRAM_ATTR encoderISR0() { 
    if (encoder_instances[0]) encoder_instances[0]->handleInterrupt(); 
}
void IRAM_ATTR encoderISR1() { 
    if (encoder_instances[1]) encoder_instances[1]->handleInterrupt(); 
}

// ============================================================================
// CONSTRUCTOR
// ============================================================================

MotorEncoder::MotorEncoder(uint8_t pin_a, uint8_t pin_b, float counts_per_rev, bool reverse_dir) :
    pinA(pin_a), pinB(pin_b), reverse(reverse_dir),
    position(0), lastState(0), countsPerRev(counts_per_rev),
    lastSpeedPosition(0), lastSpeedTime(0), currentSpeed(0.0f) {
}

// ============================================================================
// INITIALIZATION
// ============================================================================

void MotorEncoder::begin() {
    pinMode(pinA, INPUT_PULLUP);
    pinMode(pinB, INPUT_PULLUP);
    
    // Read initial state
    lastState = (digitalRead(pinA) << 1) | digitalRead(pinB);
    
    // Register instance and attach interrupts
    if (instance_count < 2) {
        encoder_instances[instance_count] = this;
        
        // Attach to BOTH channels with CHANGE mode for 4x resolution
        if (instance_count == 0) {
            attachInterrupt(digitalPinToInterrupt(pinA), encoderISR0, CHANGE);
            attachInterrupt(digitalPinToInterrupt(pinB), encoderISR0, CHANGE);
        } else {
            attachInterrupt(digitalPinToInterrupt(pinA), encoderISR1, CHANGE);
            attachInterrupt(digitalPinToInterrupt(pinB), encoderISR1, CHANGE);
        }
        
        instance_count++;
    }
    
    lastSpeedTime = micros();
}

// ============================================================================
// ISR HANDLER - 4x Quadrature Decoding
// ============================================================================

void IRAM_ATTR MotorEncoder::handleInterrupt() {
    uint8_t currState = (digitalRead(pinA) << 1) | digitalRead(pinB);
    
    if (currState == lastState) return;  // No actual change (debounce)
    
    uint8_t index = (lastState << 2) | currState;
    int8_t direction = QUADRATURE_LUT[index];
    
    if (reverse) direction = -direction;
    
    position += direction;
    lastState = currState;
}

// ============================================================================
// PUBLIC METHODS
// ============================================================================

void MotorEncoder::reset() {
    noInterrupts();
    position = 0;
    lastSpeedPosition = 0;
    currentSpeed = 0.0f;
    interrupts();
}

long MotorEncoder::getPosition() {
    noInterrupts();
    long pos = position;
    interrupts();
    return pos;
}

long MotorEncoder::getPositionDelta() {
    noInterrupts();
    long currentPos = position;
    long delta = currentPos - lastSpeedPosition;
    lastSpeedPosition = currentPos;
    interrupts();
    return delta;
}

float MotorEncoder::getSpeed() {
    unsigned long now = micros();
    
    noInterrupts();
    long currentPos = position;
    long delta = currentPos - lastSpeedPosition;
    unsigned long dt = now - lastSpeedTime;
    lastSpeedPosition = currentPos;
    lastSpeedTime = now;
    interrupts();
    
    if (dt == 0) return currentSpeed;  // Prevent division by zero
    
    // Calculate ticks per second
    currentSpeed = (float)delta * 1000000.0f / (float)dt;
    return currentSpeed;
}

float MotorEncoder::getRPM() {
    float ticksPerSecond = getSpeed();
    // RPM = (ticks/sec) / (ticks/rev) * 60
    return (ticksPerSecond / countsPerRev) * 60.0f;
}
