#ifndef TOF_TASK_H
#define TOF_TASK_H

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <Adafruit_VL53L0X.h>
#include "config/config.h"
#include "core/SharedData.h"

// ============================================================================
// CONSTANTS
// ============================================================================

#define OBSTACLE_DISTANCE_MM 50 // 5cm
#define TOF_UPDATE_RATE 50      // 20Hz

// ============================================================================
// TOF TASK CLASS
// ============================================================================

class TOFTask {
private:
    Adafruit_VL53L0X lox;
    bool isInitialized;
    uint16_t lastDistance;
    unsigned long lastUpdateTime;
    
    // Internal helper
    uint16_t readDistance();

public:
    TOFTask();
    ~TOFTask();
    
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

extern TOFTask tofTask;

// ============================================================================
// TASK FUNCTION
// ============================================================================

void tofTaskFunction(void* parameter);

#endif // TOF_TASK_H
