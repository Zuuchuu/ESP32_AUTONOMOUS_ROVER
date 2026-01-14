#ifndef NAVIGATION_TASK_H
#define NAVIGATION_TASK_H

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/semphr.h>
#include "core/SharedData.h"
#include "config/config.h"
#include "config/pins.h"
#include "hardware/MotorController.h"

// ============================================================================
// NAVIGATION TASK CLASS
// ============================================================================

class NavigationTask {
private:
    // PID Control variables
    float pidSetpoint;
    float pidInput;
    float pidOutput;
    float pidError;
    float pidLastError;
    float pidIntegral;
    float pidDerivative;
    
    // Navigation state
    bool isNavigating;
    int currentWaypointIndex;
    double targetLatitude;
    double targetLongitude;
    double targetBearing;
    double crossTrackError;
    
    // Motor control
    int leftMotorSpeed;
    int rightMotorSpeed;
    int baseSpeed;
    
    // Timing
    unsigned long lastUpdateTime;
    unsigned long navigationUpdateInterval;
    
    // Private methods
    void processNavigation();
    void calculatePID();
    void calculateCrossTrackError();
    void updateMotorSpeeds();
    void stopMotors();
    void setMotorSpeed(int leftSpeed, int rightSpeed);
    bool isWaypointReached();
    void moveToNextWaypoint();
    void printNavigationInfo();
    
public:
    // Constructor
    NavigationTask();
    
    // Destructor
    ~NavigationTask();
    
    // Initialize navigation system
    bool initialize();
    
    // Main navigation loop
    void run();
    
    // Control methods
    bool startNavigation();
    bool stopNavigation();
    bool pauseNavigation();
    bool resumeNavigation();
    
    // Status methods
    bool isActive();
    int getCurrentWaypointIndex();
    double getTargetBearing();
    double getCrossTrackError();
    void getMotorSpeeds(int& left, int& right);
    
    // Configuration methods
    void setBaseSpeed(int speed);
    void setPIDGains(float kp, float ki, float kd);
    void setWaypointThreshold(double threshold);
};

// ============================================================================
// FREE RTOS TASK FUNCTION
// ============================================================================

void navigationTaskFunction(void* parameter);

#endif // NAVIGATION_TASK_H
