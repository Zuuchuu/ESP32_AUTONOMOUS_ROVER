#include "hardware/MotorController.h"
#include "config/config.h"

// Global Instance
MotorController motorController;

// ============================================================================
// CONSTRUCTOR AND DESTRUCTOR
// ============================================================================

MotorController::MotorController() 
    : leftMotorSpeed(0), rightMotorSpeed(0), isInitialized(false),
      leftPWMChannel(PWM_CHANNEL_LEFT), rightPWMChannel(PWM_CHANNEL_RIGHT),
      leftEncoder(nullptr), rightEncoder(nullptr), pidEnabled(false),
      kp(MOTOR_PID_KP), ki(MOTOR_PID_KI), kd(MOTOR_PID_KD) {
        
    // Calculate max encoder counts per PID interval
    // For synchronized 150:1 N20 motors @ 5V DC:
    // (120 RPM / 60) × 4200 CPR × 0.020s = 168 counts/interval
    float intervalSec = MOTOR_PID_INTERVAL_MS / 1000.0f;
    float maxCounts = (MOTOR_MAX_RPM / 60.0f) * LEFT_MOTOR_ENCODER_CPR * intervalSec;
    
    // Both motors use same CPR since they're matched 150:1
    pidLeft = {0, 0, 0, 0, maxCounts, 0, 0};
    pidRight = {0, 0, 0, 0, maxCounts, 0, 0};
}

MotorController::~MotorController() {
    stopMotors();
    if (leftEncoder) delete leftEncoder;
    if (rightEncoder) delete rightEncoder;
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool MotorController::initialize() {
    if (isInitialized) {
        return true;
    }

    Serial.println("[MotorController] Initializing for skid-steer drive...");
    
    // Setup motor control pins
    SETUP_MOTOR_PINS();
    
    // Setup PWM channels for motor speed control (5kHz, 8-bit resolution)
    ledcSetup(leftPWMChannel, PWM_FREQ, PWM_RESOLUTION);
    ledcSetup(rightPWMChannel, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(PIN_LEFT_MOTOR_PWM, leftPWMChannel);
    ledcAttachPin(PIN_RIGHT_MOTOR_PWM, rightPWMChannel);
    
    // Initialize Encoders for synchronized 150:1 N20 motors
    // CPR = 7 PPR × 4 (quadrature) × 150 = 4200 counts/rev
    // Left encoder reversed due to physical mounting
    leftEncoder = new MotorEncoder(PIN_LEFT_ENCODER_A, PIN_LEFT_ENCODER_B, 
                                    LEFT_MOTOR_ENCODER_CPR, true);
    rightEncoder = new MotorEncoder(PIN_RIGHT_ENCODER_A, PIN_RIGHT_ENCODER_B, 
                                     RIGHT_MOTOR_ENCODER_CPR, false);
    
    leftEncoder->begin();
    rightEncoder->begin();
    
    // Initialize motor speeds to zero
    stopMotors();
    
    isInitialized = true;
    enablePID(true);
    
    Serial.printf("[MotorController] Initialized - CPR: %.0f, Max counts/interval: %.1f\n",
                  LEFT_MOTOR_ENCODER_CPR, pidLeft.maxCountsPerInterval);
    return true;
}

// ============================================================================
// MOTOR CONTROL METHODS - SKID STEER
// ============================================================================

void MotorController::setMotorSpeeds(int leftSpeed, int rightSpeed) {
    if (!isInitialized) return;

    // Clamp input to valid range (-255 to 255)
    leftSpeed = constrain(leftSpeed, -255, 255);
    rightSpeed = constrain(rightSpeed, -255, 255);
    
    if (pidEnabled) {
        // Map PWM command to target encoder counts per interval
        // This ensures both sides target the same wheel speed
        float leftTarget = (float)leftSpeed * pidLeft.maxCountsPerInterval / 255.0f;
        float rightTarget = (float)rightSpeed * pidRight.maxCountsPerInterval / 255.0f;
        
        pidLeft.targetSpeed = leftTarget;
        pidRight.targetSpeed = rightTarget;
    } else {
        // Open-loop control (no encoder feedback)
        setLeftMotorSpeed(leftSpeed);
        setRightMotorSpeed(rightSpeed);
    }
}

void MotorController::setLeftMotorSpeed(int speed) {
    if (!isInitialized) return;
    
    speed = constrain(speed, -255, 255);
    
    if (pidEnabled) {
        pidLeft.targetSpeed = (float)speed * pidLeft.maxCountsPerInterval / 255.0f;
        return;
    }
    
    // Open-loop control
    leftMotorSpeed = abs(speed);
    
    if (speed > 0) {
        setLeftMotorDirection(true);
        setLeftMotorPWM(leftMotorSpeed);
    } else if (speed < 0) {
        setLeftMotorDirection(false);
        setLeftMotorPWM(leftMotorSpeed);
    } else {
        digitalWrite(PIN_LEFT_MOTOR_IN1, LOW);
        digitalWrite(PIN_LEFT_MOTOR_IN2, LOW);
        ledcWrite(leftPWMChannel, 0);
    }
}

void MotorController::setRightMotorSpeed(int speed) {
    if (!isInitialized) return;
    
    speed = constrain(speed, -255, 255);
    
    if (pidEnabled) {
        pidRight.targetSpeed = (float)speed * pidRight.maxCountsPerInterval / 255.0f;
        return;
    }

    // Open-loop control
    rightMotorSpeed = abs(speed);
    
    if (speed > 0) {
        setRightMotorDirection(true);
        setRightMotorPWM(rightMotorSpeed);
    } else if (speed < 0) {
        setRightMotorDirection(false);
        setRightMotorPWM(rightMotorSpeed);
    } else {
        digitalWrite(PIN_RIGHT_MOTOR_IN1, LOW);
        digitalWrite(PIN_RIGHT_MOTOR_IN2, LOW);
        ledcWrite(rightPWMChannel, 0);
    }
}

void MotorController::stopMotors() {
    if (!isInitialized) return;
    
    // Reset PID states
    pidLeft.targetSpeed = 0;
    pidRight.targetSpeed = 0;
    pidLeft.errorSum = 0;
    pidRight.errorSum = 0;
    pidLeft.currentPWM = 0;
    pidRight.currentPWM = 0;
    
    // Apply braking (both H-bridge inputs LOW)
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
    pidLeft.targetSpeed = 0;
    pidLeft.errorSum = 0;
    pidLeft.currentPWM = 0;
    digitalWrite(PIN_LEFT_MOTOR_IN1, LOW);
    digitalWrite(PIN_LEFT_MOTOR_IN2, LOW);
    ledcWrite(leftPWMChannel, 0);
    leftMotorSpeed = 0;
}

void MotorController::stopRightMotor() {
    pidRight.targetSpeed = 0;
    pidRight.errorSum = 0;
    pidRight.currentPWM = 0;
    digitalWrite(PIN_RIGHT_MOTOR_IN1, LOW);
    digitalWrite(PIN_RIGHT_MOTOR_IN2, LOW);
    ledcWrite(rightPWMChannel, 0);
    rightMotorSpeed = 0;
}

// ============================================================================
// PID CONTROL LOOP - Velocity Control
// ============================================================================

void MotorController::update() {
    if (!isInitialized || !pidEnabled) return;
    
    int leftPWM, rightPWM;
    
    // Run velocity PID for both motor channels
    updatePID(pidLeft, leftEncoder, leftPWM);
    updatePID(pidRight, rightEncoder, rightPWM);
    
    // Apply PWM with direction
    if (leftPWM >= 0) {
        setLeftMotorDirection(true);
        setLeftMotorPWM(leftPWM);
    } else {
        setLeftMotorDirection(false);
        setLeftMotorPWM(-leftPWM);
    }
    
    if (rightPWM >= 0) {
        setRightMotorDirection(true);
        setRightMotorPWM(rightPWM);
    } else {
        setRightMotorDirection(false);
        setRightMotorPWM(-rightPWM);
    }
    
    leftMotorSpeed = abs(leftPWM);
    rightMotorSpeed = abs(rightPWM);
}

void MotorController::updatePID(PIDState& state, MotorEncoder* encoder, int& pwmOutput) {
    unsigned long now = millis();
    unsigned long dt = now - state.lastTime;
    
    // Enforce fixed update interval for consistent timing
    if (dt < MOTOR_PID_INTERVAL_MS) {
        pwmOutput = state.currentPWM;
        return;
    }
    
    // Get encoder delta (counts since last call) - preserves absolute position
    long delta = encoder->getPositionDelta();
    float measuredSpeed = (float)delta;  // counts per interval
    state.currentSpeed = measuredSpeed;
    
    // ===== PID Calculation =====
    float error = state.targetSpeed - measuredSpeed;
    
    // Integral with anti-windup clamping
    state.errorSum += error;
    float maxIntegral = 255.0f / ki;
    state.errorSum = constrain(state.errorSum, -maxIntegral, maxIntegral);
    
    // Derivative on error
    float dErr = error - state.lastError;
    
    // PID terms
    float pTerm = kp * error;
    float iTerm = ki * state.errorSum;
    float dTerm = kd * dErr;
    
    // Feedforward: Base PWM proportional to target (improves response)
    float feedforward = 0.0f;
    if (state.maxCountsPerInterval > 0 && state.targetSpeed != 0) {
        // Scale to ~80% of max PWM to leave headroom for PID correction
        feedforward = (state.targetSpeed / state.maxCountsPerInterval) * 200.0f;
    }
    
    // Total output
    float output = feedforward + pTerm + iTerm + dTerm;
    
    // Clamp to valid PWM range
    int pwm = constrain((int)output, -255, 255);
    
    // Dead zone: Apply minimum PWM to overcome static friction
    if (state.targetSpeed != 0 && abs(pwm) < 30) {
        pwm = (pwm >= 0) ? 30 : -30;
    }
    
    // Store state for next iteration
    state.lastError = error;
    state.lastTime = now;
    state.currentPWM = pwm;
    
    pwmOutput = pwm;
}

void MotorController::enablePID(bool enable) {
    pidEnabled = enable;
    if (!enable) {
        stopMotors();
    } else {
        // Reset PID states when enabling
        pidLeft.errorSum = 0;
        pidLeft.lastError = 0;
        pidLeft.currentPWM = 0;
        pidRight.errorSum = 0;
        pidRight.lastError = 0;
        pidRight.currentPWM = 0;
        
        // Reset encoder delta counters
        if (leftEncoder) leftEncoder->getPositionDelta();
        if (rightEncoder) rightEncoder->getPositionDelta();
    }
}

void MotorController::setPIDTunings(float p, float i, float d) {
    kp = p;
    ki = i;
    kd = d;
    Serial.printf("[MotorController] PID tunings: Kp=%.2f, Ki=%.2f, Kd=%.2f\n", kp, ki, kd);
}

// ============================================================================
// ENCODER ACCESS - For Odometry
// ============================================================================

long MotorController::getLeftEncoderCount() {
    if (leftEncoder) return leftEncoder->getPosition();
    return 0;
}

long MotorController::getRightEncoderCount() {
    if (rightEncoder) return rightEncoder->getPosition();
    return 0;
}

// ============================================================================
// PRIVATE METHODS - H-Bridge Control
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
