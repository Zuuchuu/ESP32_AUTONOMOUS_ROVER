#ifndef MOTOR_CONTROLLER_H
#define MOTOR_CONTROLLER_H

#include <Arduino.h>
#include "config/pins.h"
#include "config/config.h"

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
    
    // Private methods
    void setLeftMotorDirection(bool forward);
    void setRightMotorDirection(bool forward);
    void setLeftMotorPWM(int speed);
    void setRightMotorPWM(int speed);
    
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
};

#endif // MOTOR_CONTROLLER_H
