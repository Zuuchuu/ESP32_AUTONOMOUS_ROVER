#include "hardware/MotorEncoder.h"

// ============================================================================
// STATIC ISR INFRASTRUCTURE
// ============================================================================

static MotorEncoder* encoder_instances[2] = {nullptr, nullptr};
static int instance_count = 0;

// Lookup table for 4x quadrature state transitions
// Index = (prevState << 2) | currState where state = (A << 1) | B
// Values: 0 = no change, 1 = forward, -1 = backward
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

// ISR trampolines
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
    lastSpeedPosition(0) {
}

// ============================================================================
// INITIALIZATION
// ============================================================================

void MotorEncoder::begin() {
    pinMode(pinA, INPUT_PULLUP);
    pinMode(pinB, INPUT_PULLUP);
    
    // Read initial state using fast GPIO read
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
    } else {
        Serial.println("[MotorEncoder] ERROR: Maximum 2 encoder instances exceeded!");
    }
}

// ============================================================================
// ISR HANDLER - OPTIMIZED 4x Quadrature Decoding
// ============================================================================

void IRAM_ATTR MotorEncoder::handleInterrupt() {
    // CRITICAL FIX: Use direct GPIO register read instead of digitalRead()
    // This reduces ISR execution time from ~2µs to ~0.3µs
    // Prevents missed edges during high-speed rotation
    
    #ifdef ESP32
        // Fast GPIO read for ESP32
        uint32_t gpioState = REG_READ(GPIO_IN_REG);
        uint8_t valA = (gpioState >> pinA) & 0x01;
        uint8_t valB = (gpioState >> pinB) & 0x01;
    #else
        // Fallback to digitalRead for other platforms
        uint8_t valA = digitalRead(pinA);
        uint8_t valB = digitalRead(pinB);
    #endif
    
    uint8_t currState = (valA << 1) | valB;
    
    if (currState == lastState) return;  // Debounce - no actual change
    
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
