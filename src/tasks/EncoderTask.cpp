#include "tasks/EncoderTask.h"

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

// Global instance declared in main.cpp

// ============================================================================
// CONSTRUCTOR/DESTRUCTOR
// ============================================================================

EncoderTask::EncoderTask() : isInitialized(false), lastUpdateTime(0) {}

EncoderTask::~EncoderTask() {
    stop();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool EncoderTask::initialize() {
    Serial.println("[Encoder] Initializing...");
    // MotorController initializes hardware, we just read from it.
    // Ensure MotorController is initialized (usually in main setup)
    isInitialized = true;
    return true;
}

// ============================================================================
// MAIN RUN LOOP
// ============================================================================

void EncoderTask::run() {
    if (!isInitialized) return;
    
    // Get encoder counts from global motor controller
    long leftCount = motorController.getLeftEncoderCount();
    long rightCount = motorController.getRightEncoderCount();
    
    // Update SharedData
    RoverState state;
    if (sharedData.getRoverState(state)) {
        state.leftEncoderCount = leftCount;
        state.rightEncoderCount = rightCount;
        sharedData.setRoverState(state);
    }
    
    lastUpdateTime = millis();
}

// ============================================================================
// PUBLIC METHODS
// ============================================================================

void EncoderTask::stop() {
    isInitialized = false;
    Serial.println("[Encoder] Stopped");
}

// ============================================================================
// TASK FUNCTION
// ============================================================================

void encoderTaskFunction(void* parameter) {
    if (!encoderTask.initialize()) {
        Serial.println("[Encoder] Failed to initialize");
        vTaskDelete(NULL);
        return;
    }
    
    while(true) {
        encoderTask.run();
        vTaskDelay(pdMS_TO_TICKS(ENCODER_UPDATE_RATE)); // 20Hz
    }
}
