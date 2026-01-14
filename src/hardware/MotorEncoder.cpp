#include "hardware/MotorEncoder.h"

// ============================================================================
// STATIC ISR INSTANCES
// ============================================================================

static MotorEncoder* encoder_instances[2] = {nullptr, nullptr};

void IRAM_ATTR isr0() { if(encoder_instances[0]) encoder_instances[0]->handleInterrupt(); }
void IRAM_ATTR isr1() { if(encoder_instances[1]) encoder_instances[1]->handleInterrupt(); }

static int instance_count = 0;

// ============================================================================
// CONSTRUCTOR
// ============================================================================

MotorEncoder::MotorEncoder(uint8_t pin_a, uint8_t pin_b, float counts_per_rev, bool reverse_dir) :
    pinA(pin_a), pinB(pin_b), reverse(reverse_dir),
    position(0), lastInterruptTime(0), countsPerRev(counts_per_rev) {
}

// ============================================================================
// INITIALIZATION
// ============================================================================

void MotorEncoder::begin() {
    pinMode(pinA, INPUT_PULLUP);
    pinMode(pinB, INPUT_PULLUP);
    
    // Register instance for ISR
    if (instance_count < 2) {
        encoder_instances[instance_count] = this;
        
        if (instance_count == 0) {
             attachInterrupt(digitalPinToInterrupt(pinA), isr0, RISING);
        } else if (instance_count == 1) {
             attachInterrupt(digitalPinToInterrupt(pinA), isr1, RISING);
        }
        
        instance_count++;
    }
}

// ============================================================================
// ISR HANDLER
// ============================================================================

void IRAM_ATTR MotorEncoder::handleInterrupt() {
    // Read state of B to determine direction
    int valB = digitalRead(pinB);
    int direction = (valB == LOW) ? 1 : -1;
    
    if (reverse) direction = -direction;
    
    position += direction;
    lastInterruptTime = micros();
}

// ============================================================================
// PUBLIC METHODS
// ============================================================================

void MotorEncoder::reset() {
    noInterrupts();
    position = 0;
    interrupts();
}

long MotorEncoder::getPosition() {
    long pos;
    noInterrupts();
    pos = position;
    interrupts();
    return pos;
}

float MotorEncoder::getRPM() {
    return 0.0f; // Placeholder for future implementation
}
