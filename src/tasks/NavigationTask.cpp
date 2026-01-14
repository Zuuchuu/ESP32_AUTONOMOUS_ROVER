#include "tasks/NavigationTask.h"
#include <Arduino.h>
#include <math.h>
#include "hardware/MotorController.h"
#include "config/config.h"

// ============================================================================
// CONSTRUCTOR AND DESTRUCTOR
// ============================================================================

NavigationTask::NavigationTask() 
    : pidSetpoint(0.0), pidInput(0.0), pidOutput(0.0), 
      pidError(0.0), pidLastError(0.0), pidIntegral(0.0), pidDerivative(0.0),
      isNavigating(false), currentWaypointIndex(0),
      targetLatitude(0.0), targetLongitude(0.0), targetBearing(0.0), crossTrackError(0.0),
      leftMotorSpeed(0), rightMotorSpeed(0), baseSpeed(BASE_SPEED),
      lastUpdateTime(0), navigationUpdateInterval(100) {
}

NavigationTask::~NavigationTask() {
    stopMotors();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool NavigationTask::initialize() {
    Serial.println("[Navigation] Initializing navigation system...");
    
    // Initialize motor controller
    if (!motorController.initialize()) {
        Serial.println("[Navigation] Error: Failed to initialize motor controller");
        return false;
    }
    
    // Reset navigation state
    isNavigating = false;
    currentWaypointIndex = 0;
    pidIntegral = 0.0;
    pidLastError = 0.0;
    
    Serial.println("[Navigation] Navigation system initialized successfully");
    return true;
}

// ============================================================================
// MAIN NAVIGATION LOOP
// ============================================================================

void NavigationTask::run() {
    unsigned long lastPIDUpdate = 0;
    const unsigned long pidInterval = 20; // 50Hz

    while (true) {
        // High frequency loop
        unsigned long now = millis();

        // 1. Safety Check (TOF from SharedData)
        RoverState currentState;
        if (sharedData.getRoverState(currentState)) {
             float dist = currentState.frontObstacleDistance;
             bool obstacleDetected = (dist > 0 && dist < 5.0); // 5cm threshold
             
             if (obstacleDetected) {
                if (isNavigating) {
                    Serial.println("[Navigation] OBSTACLE DETECTED! Emergency Stop!");
                    stopNavigation();
                }
             }
        }
        
        // 2. Update Motor PID (if navigating or if manual mode needs it, but manual mode has its own task)
        // Actually, MotorController is global. We should update it here if THIS task owns it.
        // But ManualControlTask also runs.
        // We should explicitly update it ONLY if we are active? 
        // Or let a separate ControlTask do it?
        // Current design: Tasks run loops.
        // If Manual mode is active, this loop pauses navigation logic.
        // Checking TOF here protects navigation.
        
        // Update PID if navigating
        if (isNavigating) {
             if (now - lastPIDUpdate >= pidInterval) {
                 motorController.update(); 
                 lastPIDUpdate = now;
             }
        }

        // Check if manual mode is active - if so, pause navigation
        if (sharedData.isManualModeActive()) {
            if (isNavigating) {
                Serial.println("[Navigation] Manual mode active - pausing navigation");
                stopNavigation();
            }
        } else if (isNavigating) {
            processNavigation();
        }
        
        // Update at specified interval (Navigation Logic is slower, e.g. GPS)
        vTaskDelay(pdMS_TO_TICKS(10)); // Faster tick to allow PID updates
    }
}

// ============================================================================
// NAVIGATION PROCESSING
// ============================================================================

void NavigationTask::processNavigation() {
    unsigned long currentTime = millis();
    
    // Check if it's time to update navigation
    if (currentTime - lastUpdateTime < navigationUpdateInterval) {
        return;
    }
    
    lastUpdateTime = currentTime;
    
    // Get current position and heading
    GPSPosition currentPosition;
    IMUData currentIMUData;
    
    if (!sharedData.getPosition(currentPosition) || !sharedData.getIMUData(currentIMUData)) {
        Serial.println("[Navigation] Warning: No valid position or IMU data available");
        return;
    }
    
    if (!currentPosition.isValid || !currentIMUData.isValid) {
        Serial.println("[Navigation] Warning: Invalid position or IMU data");
        return;
    }
    
    // Check if we have waypoints
    if (!sharedData.hasWaypoints()) {
        Serial.println("[Navigation] No waypoints available, stopping navigation");
        stopNavigation();
        return;
    }
    
    // Get current waypoint
    Waypoint currentWaypoint;
    if (!sharedData.getWaypoint(currentWaypointIndex, currentWaypoint)) {
        Serial.println("[Navigation] Error: Could not get current waypoint");
        stopNavigation();
        return;
    }
    
    // Update target coordinates
    targetLatitude = currentWaypoint.latitude;
    targetLongitude = currentWaypoint.longitude;
    
    // Calculate target bearing
    targetBearing = calculateBearing(
        currentPosition.latitude, currentPosition.longitude,
        targetLatitude, targetLongitude
    );
    
    // Calculate cross-track error
    calculateCrossTrackError();
    
    // Calculate PID control
    calculatePID();
    
    // Update motor speeds
    updateMotorSpeeds();
    
    // Check if waypoint reached
    if (isWaypointReached()) {
        moveToNextWaypoint();
    }
    
    // Print navigation info periodically
    static unsigned long lastPrintTime = 0;
    if (currentTime - lastPrintTime > 5000) { // Print every 5 seconds
        printNavigationInfo();
        lastPrintTime = currentTime;
    }
}

// ============================================================================
// PID CONTROL
// ============================================================================

void NavigationTask::calculatePID() {
    // Calculate heading error (difference between target and current heading)
    IMUData currentIMUData;
    sharedData.getIMUData(currentIMUData);
    float currentHeading = currentIMUData.heading;
    float headingError = normalizeAngle(targetBearing - currentHeading);
    
    // Apply cross-track error correction
    float xteCorrection = K_XTE * crossTrackError;
    headingError += xteCorrection;
    
    // Normalize error to -180 to +180 degrees
    if (headingError > 180.0) {
        headingError -= 360.0;
    } else if (headingError < -180.0) {
        headingError += 360.0;
    }
    
    // PID calculation
    pidError = headingError;
    pidIntegral += pidError;
    pidDerivative = pidError - pidLastError;
    
    // Apply integral windup protection
    if (pidIntegral > 100.0) pidIntegral = 100.0;
    if (pidIntegral < -100.0) pidIntegral = -100.0;
    
    // Calculate PID output
    pidOutput = KP * pidError + KI * pidIntegral + KD * pidDerivative;
    
    // Limit output
    if (pidOutput > 255.0) pidOutput = 255.0;
    if (pidOutput < -255.0) pidOutput = -255.0;
    
    pidLastError = pidError;
}

// ============================================================================
// CROSS-TRACK ERROR CALCULATION
// ============================================================================

void NavigationTask::calculateCrossTrackError() {
    GPSPosition currentPosition;
    sharedData.getPosition(currentPosition);
    
    if (!currentPosition.isValid) {
        crossTrackError = 0.0;
        return;
    }
    
    // Calculate distance from current position to target
    double distance = calculateDistance(
        currentPosition.latitude, currentPosition.longitude,
        targetLatitude, targetLongitude
    );
    
    // Calculate bearing from current position to target
    double bearing = calculateBearing(
        currentPosition.latitude, currentPosition.longitude,
        targetLatitude, targetLongitude
    );
    
    // Get current heading
    IMUData currentIMUData;
    sharedData.getIMUData(currentIMUData);
    double currentHeading = currentIMUData.heading;
    
    // Calculate cross-track error (perpendicular distance from path)
    double headingDiff = normalizeAngle(bearing - currentHeading);
    crossTrackError = distance * sin(radians(headingDiff));
}

// ============================================================================
// MOTOR CONTROL
// ============================================================================

void NavigationTask::updateMotorSpeeds() {
    // Calculate motor speeds based on PID output
    int speedDifference = (int)pidOutput;
    
    leftMotorSpeed = baseSpeed + speedDifference;
    rightMotorSpeed = baseSpeed - speedDifference;
    
    // Ensure speeds are within valid range
    if (leftMotorSpeed > 255) leftMotorSpeed = 255;
    if (leftMotorSpeed < 0) leftMotorSpeed = 0;
    if (rightMotorSpeed > 255) rightMotorSpeed = 255;
    if (rightMotorSpeed < 0) rightMotorSpeed = 0;
    
    // Apply motor speeds using motor controller
    motorController.setMotorSpeeds(leftMotorSpeed, rightMotorSpeed);
}

void NavigationTask::setMotorSpeed(int leftSpeed, int rightSpeed) {
    // Use motor controller to set speeds
    motorController.setMotorSpeeds(leftSpeed, rightSpeed);
}

void NavigationTask::stopMotors() {
    motorController.stopMotors();
    leftMotorSpeed = 0;
    rightMotorSpeed = 0;
}

// ============================================================================
// WAYPOINT MANAGEMENT
// ============================================================================

bool NavigationTask::isWaypointReached() {
    GPSPosition currentPosition;
    sharedData.getPosition(currentPosition);
    
    if (!currentPosition.isValid) {
        return false;
    }
    
    // Calculate distance to current waypoint
    double distance = calculateDistance(
        currentPosition.latitude, currentPosition.longitude,
        targetLatitude, targetLongitude
    );
    
    return distance <= WAYPOINT_THRESHOLD;
}

void NavigationTask::moveToNextWaypoint() {
    Serial.printf("[Navigation] Waypoint %d reached!\n", currentWaypointIndex);
    
    currentWaypointIndex++;
    
    // Check if we've completed all waypoints
    if (currentWaypointIndex >= sharedData.getWaypointCount()) {
        Serial.println("[Navigation] All waypoints completed! Stopping navigation.");
        stopNavigation();
        return;
    }
    
    Serial.printf("[Navigation] Moving to waypoint %d\n", currentWaypointIndex);
    
    // Reset PID for new waypoint
    pidIntegral = 0.0;
    pidLastError = 0.0;
}

// ============================================================================
// CONTROL METHODS
// ============================================================================

bool NavigationTask::startNavigation() {
    if (isNavigating) {
        Serial.println("[Navigation] Already navigating");
        return false;
    }
    
    if (!sharedData.hasWaypoints()) {
        Serial.println("[Navigation] No waypoints available");
        return false;
    }
    
    // Reset navigation state
    currentWaypointIndex = 0;
    pidIntegral = 0.0;
    pidLastError = 0.0;
    
    // Update rover state
    RoverState state;
    sharedData.getRoverState(state);
    state.isNavigating = true;
    state.currentWaypointIndex = 0;
    state.totalWaypoints = sharedData.getWaypointCount();
    sharedData.setRoverState(state);
    
    isNavigating = true;
    Serial.println("[Navigation] Navigation started");
    return true;
}

bool NavigationTask::stopNavigation() {
    if (!isNavigating) {
        return false;
    }
    
    stopMotors();
    isNavigating = false;
    
    // Update rover state
    RoverState state;
    sharedData.getRoverState(state);
    state.isNavigating = false;
    state.currentSpeed = 0.0;
    sharedData.setRoverState(state);
    
    Serial.println("[Navigation] Navigation stopped");
    return true;
}

bool NavigationTask::pauseNavigation() {
    if (!isNavigating) {
        return false;
    }
    
    stopMotors();
    Serial.println("[Navigation] Navigation paused");
    return true;
}

bool NavigationTask::resumeNavigation() {
    if (!isNavigating) {
        return false;
    }
    
    Serial.println("[Navigation] Navigation resumed");
    return true;
}

// ============================================================================
// STATUS METHODS
// ============================================================================

bool NavigationTask::isActive() {
    return isNavigating;
}

int NavigationTask::getCurrentWaypointIndex() {
    return currentWaypointIndex;
}

double NavigationTask::getTargetBearing() {
    return targetBearing;
}

double NavigationTask::getCrossTrackError() {
    return crossTrackError;
}

void NavigationTask::getMotorSpeeds(int& left, int& right) {
    left = leftMotorSpeed;
    right = rightMotorSpeed;
}

// ============================================================================
// CONFIGURATION METHODS
// ============================================================================

void NavigationTask::setBaseSpeed(int speed) {
    if (speed >= 0 && speed <= 255) {
        baseSpeed = speed;
    }
}

void NavigationTask::setPIDGains(float kp, float ki, float kd) {
    // These would be used if we had configurable PID gains
    // For now, we use the constants from config.h
}

void NavigationTask::setWaypointThreshold(double threshold) {
    // This would be used if we had configurable waypoint threshold
    // For now, we use WAYPOINT_THRESHOLD from config.h
}

// ============================================================================
// DEBUG METHODS
// ============================================================================

void NavigationTask::printNavigationInfo() {
    Serial.println("=== Navigation Status ===");
    Serial.printf("Navigating: %s\n", isNavigating ? "Yes" : "No");
    Serial.printf("Current Waypoint: %d\n", currentWaypointIndex);
    Serial.printf("Target Bearing: %.2f°\n", targetBearing);
    Serial.printf("Cross-Track Error: %.2f m\n", crossTrackError);
    Serial.printf("PID Output: %.2f\n", pidOutput);
    Serial.printf("Left Motor: %d, Right Motor: %d\n", leftMotorSpeed, rightMotorSpeed);
    Serial.println("========================");
}

// ============================================================================
// FREE RTOS TASK FUNCTION
// ============================================================================

void navigationTaskFunction(void* parameter) {
    NavigationTask* navigationTask = (NavigationTask*)parameter;
    
    if (navigationTask->initialize()) {
        navigationTask->run();
    } else {
        Serial.println("[Navigation] Failed to initialize navigation task");
    }
    
    vTaskDelete(NULL);
}
