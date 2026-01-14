#include "tasks/TOFTask.h"

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

// Global instance declared in main.cpp

// ============================================================================
// CONSTRUCTOR/DESTRUCTOR
// ============================================================================

TOFTask::TOFTask() 
    : isInitialized(false), 
      lastDistance(8190),
      lastUpdateTime(0) {
}

TOFTask::~TOFTask() {
    stop();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool TOFTask::initialize() {
    Serial.println("[TOF] Initializing VL53L0X sensor...");
    
    if (!lox.begin()) {
        Serial.println("[TOF] ERROR: Failed to boot VL53L0X");
        return false;
    }
    
    isInitialized = true;
    Serial.println("[TOF] Initialization successful");
    return true;
}

// ============================================================================
// MAIN RUN LOOP
// ============================================================================

void TOFTask::run() {
    if (!isInitialized) return;
    
    // Read distance from sensor
    uint16_t distance = readDistance();
    
    // Update SharedData
    RoverState state;
    if (sharedData.getRoverState(state)) {
        state.frontObstacleDistance = (float)distance / 10.0f; // mm to cm
        sharedData.setRoverState(state);
    } // Else failed to get state, skip update
    
    lastUpdateTime = millis();
}

// ============================================================================
// INTERNAL HELPERS
// ============================================================================

uint16_t TOFTask::readDistance() {
    if (!isInitialized) return 8190;
    
    VL53L0X_RangingMeasurementData_t measure;
    lox.rangingTest(&measure, false);
    
    if (measure.RangeStatus != 4) {  // phase failures have incorrect data
        lastDistance = measure.RangeMilliMeter;
    } else {
        lastDistance = 8190; // Out of range
    }
    
    return lastDistance;
}

// ============================================================================
// PUBLIC METHODS
// ============================================================================

void TOFTask::stop() {
    isInitialized = false;
    Serial.println("[TOF] Task stopped");
}

// ============================================================================
// TASK FUNCTION
// ============================================================================

void tofTaskFunction(void* parameter) {
    Serial.println("[TOF] Task started");
    
    if (!tofTask.initialize()) {
        Serial.println("[TOF] ERROR: Failed to initialize task");
        vTaskDelete(NULL);
        return;
    }
    
    while(true) {
        tofTask.run();
        vTaskDelay(pdMS_TO_TICKS(TOF_UPDATE_RATE));
    }
}
