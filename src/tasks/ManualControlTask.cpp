#include "tasks/ManualControlTask.h"
#include <Arduino.h>
#include <cstring>  // For strcmp, strncpy
#include "config/config.h"

// ============================================================================
// CONSTRUCTOR AND DESTRUCTOR
// ============================================================================

ManualControlTask::ManualControlTask() 
    : isManualModeActive(false), isMoving(false), currentSpeed(0),
      lastCommandTime(0), commandTimeout(10000), updateInterval(100) {
    currentDirection[0] = '\0';  // Initialize empty string
}

ManualControlTask::~ManualControlTask() {
    stopAllMovement();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool ManualControlTask::initialize() {
    Serial.println("[ManualControl] Initializing manual control system...");
    
    // Global Motor controller already initialized in main, but safe to call
    if (!motorController.initialize()) {
        Serial.println("[ManualControl] Error: Failed to initialize motor controller");
        return false;
    }
    
    // Reset manual control state
    isManualModeActive = false;
    isMoving = false;
    currentDirection[0] = '\0';  // Empty string
    currentSpeed = 0;
    lastCommandTime = 0;
    
    Serial.println("[ManualControl] Manual control system initialized successfully");
    return true;
}

// ============================================================================
// MAIN MANUAL CONTROL LOOP
// ============================================================================

void ManualControlTask::run() {
    while (true) {
        // Safety Check (TOF from SharedData)
        RoverState currentState;
        if (sharedData.getRoverState(currentState)) {
             float dist = currentState.frontObstacleDistance;
             bool obstacleDetected = (dist > 0 && dist < 5.0); // 5cm threshold
             
             if (obstacleDetected) {
                 if (isMoving && strcmp(currentDirection, "forward") == 0) {
                     Serial.println("[ManualControl] PROXIMITY ALERT! Stopping.");
                     stopAllMovement();
                 }
             }
        }

        // Check shared data for manual control commands
        bool manualActive, manualMoving;
        char manualDirection[12];
        int manualSpeed;
        
        if (sharedData.getManualControlState(manualActive, manualMoving, manualDirection, sizeof(manualDirection), manualSpeed)) {
            // Update local state
            isManualModeActive = manualActive;
            isMoving = manualMoving;
            strncpy(currentDirection, manualDirection, sizeof(currentDirection) - 1);
            currentDirection[sizeof(currentDirection) - 1] = '\0';
            currentSpeed = manualSpeed;
            
            // Execute manual commands
            if (manualActive && manualMoving) {
                // Check for command timeout
                if (millis() - lastCommandTime > commandTimeout) {
                    Serial.println("[ManualControl] Command timeout - stopping movement");
                    stopMovement();
                    // Update shared data
                    sharedData.setManualControlState(true, false, "", 0);
                } else {
                    // Update motor speeds
                    updateMotors();
                }
            } else if (manualActive && !manualMoving) {
                // Manual mode active but not moving
                stopMovement();
            }
        }
        
        // Update at specified interval
        vTaskDelay(pdMS_TO_TICKS(updateInterval));
    }
}

// ============================================================================
// MANUAL CONTROL METHODS
// ============================================================================

bool ManualControlTask::enableManualMode() {
    if (isManualModeActive) {
        Serial.println("[ManualControl] Manual mode already active");
        return true;
    }
    
    Serial.println("[ManualControl] Enabling manual control mode");
    isManualModeActive = true;
    isMoving = false;
    currentDirection[0] = '\0';  // Empty string
    currentSpeed = 0;
    
    // Stop any current movement
    stopAllMovement();
    
    Serial.println("[ManualControl] Manual control mode enabled");
    return true;
}

bool ManualControlTask::disableManualMode() {
    if (!isManualModeActive) {
        Serial.println("[ManualControl] Manual mode not active");
        return true;
    }
    
    Serial.println("[ManualControl] Disabling manual control mode");
    isManualModeActive = false;
    
    // Stop all movement
    stopAllMovement();
    
    Serial.println("[ManualControl] Manual control mode disabled");
    return true;
}

bool ManualControlTask::executeCommand(const char* direction, int speed) {
    if (!isManualModeActive) {
        Serial.println("[ManualControl] Error: Manual mode not active");
        return false;
    }
    
    if (!isCommandValid(direction, speed)) {
        Serial.printf("[ManualControl] Error: Invalid command - direction: %s, speed: %d\n", 
                     direction, speed);
        return false;
    }
    
    Serial.printf("[ManualControl] Executing command: %s at speed %d\n", 
                 direction, speed);
    
    // Process the command
    processManualCommand(direction, speed);
    
    return true;
}

bool ManualControlTask::stopAllMovement() {
    Serial.println("[ManualControl] Stopping all movement");
    stopMovement();
    return true;
}

// ============================================================================
// PRIVATE METHODS
// ============================================================================

void ManualControlTask::processManualCommand(const char* direction, int speed) {
    strncpy(currentDirection, direction, sizeof(currentDirection) - 1);
    currentDirection[sizeof(currentDirection) - 1] = '\0';
    currentSpeed = speed;
    isMoving = true;
    
    // Update command time for timeout
    lastCommandTime = millis();
    
    // Map direction to motor speeds
    int leftSpeed = 0;
    int rightSpeed = 0;
    
    if (strcmp(direction, "forward") == 0) {
        leftSpeed = speed;
        rightSpeed = speed;
    } else if (strcmp(direction, "backward") == 0) {
        leftSpeed = -speed;
        rightSpeed = -speed;
    } else if (strcmp(direction, "left") == 0) {
        leftSpeed = -speed;
        rightSpeed = speed;
    } else if (strcmp(direction, "right") == 0) {
        leftSpeed = speed;
        rightSpeed = -speed;
    } else if (strcmp(direction, "stop") == 0) {
        leftSpeed = 0;
        rightSpeed = 0;
        isMoving = false;
    }
    
    // Apply motor speeds
    motorController.setMotorSpeeds(leftSpeed, rightSpeed);
    
    Serial.printf("[ManualControl] Motors set - Left: %d, Right: %d\n", leftSpeed, rightSpeed);
}

void ManualControlTask::stopMovement() {
    if (!isMoving) return;
    
    Serial.println("[ManualControl] Stopping movement");
    motorController.stopMotors();
    isMoving = false;
    currentDirection[0] = '\0';
    currentSpeed = 0;
}

void ManualControlTask::updateMotors() {
    // This method is called periodically while moving
    // Currently just ensures motors maintain their current speeds
    // Could be extended for additional safety checks or motor monitoring
}

bool ManualControlTask::isCommandValid(const char* direction, int speed) {
    // Validate direction
    if (strcmp(direction, "forward") != 0 && strcmp(direction, "backward") != 0 && 
        strcmp(direction, "left") != 0 && strcmp(direction, "right") != 0 && 
        strcmp(direction, "stop") != 0) {
        return false;
    }
    
    // Validate speed (0-100 for percentage)
    if (speed < 0 || speed > 100) {
        return false;
    }
    
    return true;
}

void ManualControlTask::emergencyStop() {
    Serial.println("[ManualControl] EMERGENCY STOP ACTIVATED");
    motorController.emergencyStop();
    isMoving = false;
    currentDirection[0] = '\0';
    currentSpeed = 0;
}

void ManualControlTask::emergencyStopMotors() {
    emergencyStop();
}

// ============================================================================
// CONFIGURATION METHODS
// ============================================================================

void ManualControlTask::setCommandTimeout(unsigned long timeout) {
    commandTimeout = timeout;
    Serial.printf("[ManualControl] Command timeout set to %lu ms\n", timeout);
}

void ManualControlTask::setUpdateInterval(unsigned long interval) {
    updateInterval = interval;
    Serial.printf("[ManualControl] Update interval set to %lu ms\n", interval);
}

// ============================================================================
// FREE RTOS TASK FUNCTION
// ============================================================================

void manualControlTaskFunction(void* parameter) {
    ManualControlTask* manualControl = static_cast<ManualControlTask*>(parameter);
    
    if (manualControl) {
        manualControl->run();
    }
    
    vTaskDelete(NULL);
}
