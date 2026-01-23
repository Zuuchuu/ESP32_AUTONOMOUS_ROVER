#ifndef MOTOR_CONTROLLER_H
#define MOTOR_CONTROLLER_H

#include <Arduino.h>
#include "config/pins.h"
#include "config/config.h"
#include "hardware/MotorEncoder.h"

// ============================================================================
// MOTOR CONTROLLER CLASS
// ============================================================================

class MotorController {
private:
    // Motor state
    int leftMotorSpeed;
    int rightMotorSpeed;
    bool isInitialized;
    
    // PWM channels
    int leftPWMChannel;
    int rightPWMChannel;
    
    // Encoders
    MotorEncoder* leftEncoder;
    MotorEncoder* rightEncoder;
    
    // PID Control
    bool pidEnabled;
    float kp, ki, kd;
    
    struct PIDState {
        float targetSpeed;          // Target ticks per interval (0-255 mapped)
        float currentSpeed;         // Measured ticks per interval
        float errorSum;             // Integral accumulator
        float lastError;            // Previous error for derivative
        float maxCountsPerInterval; // Motor-specific max counts (based on CPR)
        int currentPWM;             // Current PWM output for smooth ramping
        unsigned long lastTime;
    } pidLeft, pidRight;

    // Private methods
    void setLeftMotorDirection(bool forward);
    void setRightMotorDirection(bool forward);
    void setLeftMotorPWM(int speed);
    void setRightMotorPWM(int speed);
    void updatePID(PIDState& state, MotorEncoder* encoder, int& pwmOutput);

public:
    // Constructor
    MotorController();
    
    // Destructor
    ~MotorController();
    
    // Initialize motor controller
    bool initialize();
    
    // Motor control methods
    void setMotorSpeeds(int leftSpeed, int rightSpeed);
    void setLeftMotorSpeed(int speed);
    void setRightMotorSpeed(int speed);
    void stopMotors();
    void stopLeftMotor();
    void stopRightMotor();
    
    // Status methods
    void getMotorSpeeds(int& left, int& right);
    int getLeftMotorSpeed() const { return leftMotorSpeed; }
    int getRightMotorSpeed() const { return rightMotorSpeed; }
    bool isMotorInitialized() const { return isInitialized; }
    
    // Utility methods
    void emergencyStop();
    void setPWMChannels(int leftChannel, int rightChannel);
    
    // Control Loop
    void update(); // Call this frequently (~10-20Hz minimum)
    void enablePID(bool enable);
    void setPIDTunings(float p, float i, float d);
    long getLeftEncoderCount();
    long getRightEncoderCount();
};

extern MotorController motorController;

#endif // MOTOR_CONTROLLER_H
