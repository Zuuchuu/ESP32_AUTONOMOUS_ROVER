#ifndef MANUAL_CONTROL_TASK_H
#define MANUAL_CONTROL_TASK_H

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/semphr.h>
#include <freertos/queue.h>
#include "core/SharedData.h"
#include "config/config.h"
#include "config/pins.h"
#include "hardware/MotorController.h"

// ============================================================================
// MANUAL COMMAND STRUCTURE - For queue-based communication
// ============================================================================

struct ManualCommand {
    char direction[20];   // "forward", "backward", "left", "right", "stop", "forward_right", etc.
    int speed;            // 0-100 percentage
    bool enableManual;    // true = enable manual mode, false = disable
    bool isControlCmd;    // true = enable/disable command, false = move command
};

// Command queue depth - small buffer for real-time responsiveness
#define MANUAL_CMD_QUEUE_SIZE 4

// ============================================================================
// MANUAL CONTROL TASK CLASS
// ============================================================================

class ManualControlTask {
private:
    // Command queue for low-latency communication
    QueueHandle_t commandQueue;
    
    // Manual control state
    bool isManualModeActive;
    bool isMoving;
    char currentDirection[20];  // "forward", "backward", "left", "right", "stop", "forward_right", etc.
    int currentSpeed;
    
    // Timing and safety - reduced timeout for better responsiveness
    unsigned long lastCommandTime;
    unsigned long commandTimeout;   // Now 150ms (was 500ms)
    unsigned long updateInterval;   // Now 20ms (was 100ms)
    
    // Private methods
    void processManualCommand(const char* direction, int speed);
    void stopMovement();
    void updateMotors();
    bool isCommandValid(const char* direction, int speed);
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
    bool executeCommand(const char* direction, int speed);
    bool stopAllMovement();
    
    // Status methods
    bool isActive() const { return isManualModeActive; }
    bool isCurrentlyMoving() const { return isMoving; }
    const char* getCurrentDirection() const { return currentDirection; }
    int getCurrentSpeed() const { return currentSpeed; }
    
    // Configuration methods
    void setCommandTimeout(unsigned long timeout);
    void setUpdateInterval(unsigned long interval);
    
    // Queue access for external command senders (e.g., WiFiTask)
    QueueHandle_t getCommandQueue() const { return commandQueue; }
    
    // Safety methods
    void emergencyStopMotors();
};

// ============================================================================
// GLOBAL INSTANCE - Extern declaration for access from WiFiTask
// ============================================================================

extern ManualControlTask manualControlTask;

// ============================================================================
// FREE RTOS TASK FUNCTION
// ============================================================================

void manualControlTaskFunction(void* parameter);

#endif // MANUAL_CONTROL_TASK_H
