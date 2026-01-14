#ifndef ENCODER_TASK_H
#define ENCODER_TASK_H

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include "core/SharedData.h"
#include "hardware/MotorController.h"

// ============================================================================
// CONSTANTS
// ============================================================================

#define ENCODER_UPDATE_RATE 50 // 20Hz

// ============================================================================
// ENCODER TASK CLASS
// ============================================================================

class EncoderTask {
private:
    bool isInitialized;
    unsigned long lastUpdateTime;

public:
    EncoderTask();
    ~EncoderTask();
    
    // Lifecycle methods
    bool initialize();
    void run();
    void stop();
    
    // Status
    bool isReady() const { return isInitialized; }
};

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

extern EncoderTask encoderTask;

// ============================================================================
// TASK FUNCTION
// ============================================================================

void encoderTaskFunction(void* parameter);

#endif // ENCODER_TASK_H
