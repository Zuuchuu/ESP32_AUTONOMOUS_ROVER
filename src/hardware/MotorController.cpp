#include "hardware/MotorController.h"
#include "config/config.h"

// ============================================================================
// CONSTRUCTOR AND DESTRUCTOR
// ============================================================================

MotorController::MotorController() 
    : leftMotorSpeed(0), rightMotorSpeed(0), isInitialized(false),
      leftPWMChannel(PWM_CHANNEL_LEFT), rightPWMChannel(PWM_CHANNEL_RIGHT) {
}

MotorController::~MotorController() {
    stopMotors();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool MotorController::initialize() {
    Serial.println("[MotorController] Initializing motor controller...");
    
    // Setup motor control pins
    SETUP_MOTOR_PINS();
    
    // Setup PWM channels for motor speed control
    ledcSetup(leftPWMChannel, PWM_FREQ, PWM_RESOLUTION);
    ledcSetup(rightPWMChannel, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(PIN_LEFT_MOTOR_PWM, leftPWMChannel);
    ledcAttachPin(PIN_RIGHT_MOTOR_PWM, rightPWMChannel);
    
    // Initialize motor speeds to zero
    stopMotors();
    
    isInitialized = true;
    Serial.println("[MotorController] Motor controller initialized successfully");
    return true;
}

// ============================================================================
// MOTOR CONTROL METHODS
// ============================================================================

void MotorController::setMotorSpeeds(int leftSpeed, int rightSpeed) {
    if (!isInitialized) {
        Serial.println("[MotorController] Error: Motor controller not initialized");
        return;
    }
    
    setLeftMotorSpeed(leftSpeed);
    setRightMotorSpeed(rightSpeed);
}

void MotorController::setLeftMotorSpeed(int speed) {
    if (!isInitialized) {
        Serial.println("[MotorController] Error: Motor controller not initialized");
        return;
    }
    
    // Ensure speed is within valid range
    if (speed > 255) speed = 255;
    if (speed < -255) speed = -255;
    
    leftMotorSpeed = abs(speed);
    
    if (speed > 0) {
        setLeftMotorDirection(true);  // Forward
        setLeftMotorPWM(leftMotorSpeed);
    } else if (speed < 0) {
        setLeftMotorDirection(false); // Backward
        setLeftMotorPWM(leftMotorSpeed);
    } else {
        // Stop motor
        digitalWrite(PIN_LEFT_MOTOR_IN1, LOW);
        digitalWrite(PIN_LEFT_MOTOR_IN2, LOW);
        ledcWrite(leftPWMChannel, 0);
    }
}

void MotorController::setRightMotorSpeed(int speed) {
    if (!isInitialized) {
        Serial.println("[MotorController] Error: Motor controller not initialized");
        return;
    }
    
    // Ensure speed is within valid range
    if (speed > 255) speed = 255;
    if (speed < -255) speed = -255;
    
    rightMotorSpeed = abs(speed);
    
    if (speed > 0) {
        setRightMotorDirection(true);  // Forward
        setRightMotorPWM(rightMotorSpeed);
    } else if (speed < 0) {
        setRightMotorDirection(false); // Backward
        setRightMotorPWM(rightMotorSpeed);
    } else {
        // Stop motor
        digitalWrite(PIN_RIGHT_MOTOR_IN1, LOW);
        digitalWrite(PIN_RIGHT_MOTOR_IN2, LOW);
        ledcWrite(rightPWMChannel, 0);
    }
}

void MotorController::stopMotors() {
    if (!isInitialized) {
        return;
    }
    
    digitalWrite(PIN_LEFT_MOTOR_IN1, LOW);
    digitalWrite(PIN_LEFT_MOTOR_IN2, LOW);
    digitalWrite(PIN_RIGHT_MOTOR_IN1, LOW);
    digitalWrite(PIN_RIGHT_MOTOR_IN2, LOW);
    
    ledcWrite(leftPWMChannel, 0);
    ledcWrite(rightPWMChannel, 0);
    
    leftMotorSpeed = 0;
    rightMotorSpeed = 0;
}

void MotorController::stopLeftMotor() {
    if (!isInitialized) {
        return;
    }
    
    digitalWrite(PIN_LEFT_MOTOR_IN1, LOW);
    digitalWrite(PIN_LEFT_MOTOR_IN2, LOW);
    ledcWrite(leftPWMChannel, 0);
    leftMotorSpeed = 0;
}

void MotorController::stopRightMotor() {
    if (!isInitialized) {
        return;
    }
    
    digitalWrite(PIN_RIGHT_MOTOR_IN1, LOW);
    digitalWrite(PIN_RIGHT_MOTOR_IN2, LOW);
    ledcWrite(rightPWMChannel, 0);
    rightMotorSpeed = 0;
}

// ============================================================================
// PRIVATE METHODS
// ============================================================================

void MotorController::setLeftMotorDirection(bool forward) {
    if (forward) {
        digitalWrite(PIN_LEFT_MOTOR_IN1, HIGH);
        digitalWrite(PIN_LEFT_MOTOR_IN2, LOW);
    } else {
        digitalWrite(PIN_LEFT_MOTOR_IN1, LOW);
        digitalWrite(PIN_LEFT_MOTOR_IN2, HIGH);
    }
}

void MotorController::setRightMotorDirection(bool forward) {
    if (forward) {
        digitalWrite(PIN_RIGHT_MOTOR_IN1, HIGH);
        digitalWrite(PIN_RIGHT_MOTOR_IN2, LOW);
    } else {
        digitalWrite(PIN_RIGHT_MOTOR_IN1, LOW);
        digitalWrite(PIN_RIGHT_MOTOR_IN2, HIGH);
    }
}

void MotorController::setLeftMotorPWM(int speed) {
    ledcWrite(leftPWMChannel, speed);
}

void MotorController::setRightMotorPWM(int speed) {
    ledcWrite(rightPWMChannel, speed);
}

// ============================================================================
// STATUS METHODS
// ============================================================================

void MotorController::getMotorSpeeds(int& left, int& right) {
    left = leftMotorSpeed;
    right = rightMotorSpeed;
}

// ============================================================================
// UTILITY METHODS
// ============================================================================

void MotorController::emergencyStop() {
    Serial.println("[MotorController] EMERGENCY STOP!");
    stopMotors();
}

void MotorController::setPWMChannels(int leftChannel, int rightChannel) {
    if (isInitialized) {
        Serial.println("[MotorController] Warning: Cannot change PWM channels after initialization");
        return;
    }
    
    leftPWMChannel = leftChannel;
    rightPWMChannel = rightChannel;
}
