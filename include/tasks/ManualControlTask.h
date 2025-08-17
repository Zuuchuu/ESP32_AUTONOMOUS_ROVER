#ifndef MANUAL_CONTROL_TASK_H
#define MANUAL_CONTROL_TASK_H

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/semphr.h>
#include "core/SharedData.h"
#include "config/config.h"
#include "config/pins.h"
#include "hardware/MotorController.h"

// ============================================================================
// MANUAL CONTROL TASK CLASS
// ============================================================================

class ManualControlTask {
private:
    // Manual control state
    bool isManualModeActive;
    bool isMoving;
    String currentDirection;
    int currentSpeed;
    
    // Motor control
    MotorController motorController;
    
    // Timing and safety
    unsigned long lastCommandTime;
    unsigned long commandTimeout;
    unsigned long updateInterval;
    
    // Private methods
    void processManualCommand(const String& direction, int speed);
    void stopMovement();
    void updateMotors();
    bool isCommandValid(const String& direction, int speed);
    void emergencyStop();
    
public:
    // Constructor
    ManualControlTask();
    
    // Destructor
    ~ManualControlTask();
    
    // Initialize manual control system
    bool initialize();
    
    // Main manual control loop
    void run();
    
    // Control methods
    bool enableManualMode();
    bool disableManualMode();
    bool executeCommand(const String& direction, int speed);
    bool stopAllMovement();
    
    // Status methods
    bool isActive() const { return isManualModeActive; }
    bool isCurrentlyMoving() const { return isMoving; }
    String getCurrentDirection() const { return currentDirection; }
    int getCurrentSpeed() const { return currentSpeed; }
    
    // Configuration methods
    void setCommandTimeout(unsigned long timeout);
    void setUpdateInterval(unsigned long interval);
    
    // Safety methods
    void emergencyStopMotors();
};

// ============================================================================
// FREE RTOS TASK FUNCTION
// ============================================================================

void manualControlTaskFunction(void* parameter);

#endif // MANUAL_CONTROL_TASK_H
