#ifndef PINS_H
#define PINS_H

#include <Arduino.h>

// ============================================================================
// MOTOR DRIVER PINS (TB6612FNG)
// ============================================================================

// Left Motor Control
#define PIN_LEFT_MOTOR_PWM      14    // PWMA - PWM speed control
#define PIN_LEFT_MOTOR_IN1      26    // AI1 - Direction control 1
#define PIN_LEFT_MOTOR_IN2      27    // AI2 - Direction control 2

// Right Motor Control
#define PIN_RIGHT_MOTOR_PWM     32    // PWMB - PWM speed control
#define PIN_RIGHT_MOTOR_IN1     25    // BI1 - Direction control 1
#define PIN_RIGHT_MOTOR_IN2     33    // BI2 - Direction control 2

// Motor Encoders
// Left Motor Encoders
#define PIN_LEFT_ENCODER_A      18    // CH1
#define PIN_LEFT_ENCODER_B      19    // CH2

// Right Motor Encoders
#define PIN_RIGHT_ENCODER_A     5     // CH1
#define PIN_RIGHT_ENCODER_B     4     // CH2

// ============================================================================
// GPS MODULE PINS (u-blox M10)
// ============================================================================

#define PIN_GPS_RX              16    // GPS TX -> ESP32 RX
#define PIN_GPS_TX              17    // GPS RX -> ESP32 TX

// ============================================================================
// I2C BUS (OLED, IMU, TOF)
// ============================================================================

#define PIN_I2C_SDA             21    // SDA
#define PIN_I2C_SCL             22    // SCL

// ============================================================================
// STATUS LED PINS
// ============================================================================

#define PIN_STATUS_LED          2     // Built-in LED
#define PIN_WIFI_LED            23    // Reassigned from 4
#define PIN_GPS_LED             13    // Reassigned from 5

// ============================================================================
// BUTTON PINS (Optional - for manual control)
// ============================================================================

#define PIN_EMERGENCY_STOP      0     // Emergency stop button
#define PIN_MODE_SELECT         15    // Mode selection button

// ============================================================================
// PIN VALIDATION MACROS
// ============================================================================

// Check if pins are valid GPIO pins for ESP32
#define IS_VALID_GPIO_PIN(pin)  ((pin >= 0) && (pin <= 39) && (pin != 6) && (pin != 7) && (pin != 8) && (pin != 9) && (pin != 10) && (pin != 11))

// ============================================================================
// PIN DIRECTION SETUP MACROS
// ============================================================================

#define SETUP_MOTOR_PINS() \
    pinMode(PIN_LEFT_MOTOR_IN1, OUTPUT); \
    pinMode(PIN_LEFT_MOTOR_IN2, OUTPUT); \
    pinMode(PIN_RIGHT_MOTOR_IN1, OUTPUT); \
    pinMode(PIN_RIGHT_MOTOR_IN2, OUTPUT); \
    pinMode(PIN_LEFT_ENCODER_A, INPUT_PULLUP); \
    pinMode(PIN_LEFT_ENCODER_B, INPUT_PULLUP); \
    pinMode(PIN_RIGHT_ENCODER_A, INPUT_PULLUP); \
    pinMode(PIN_RIGHT_ENCODER_B, INPUT_PULLUP);

#define SETUP_STATUS_PINS() \
    pinMode(PIN_STATUS_LED, OUTPUT); \
    pinMode(PIN_WIFI_LED, OUTPUT); \
    pinMode(PIN_GPS_LED, OUTPUT)

#define SETUP_BUTTON_PINS() \
    pinMode(PIN_EMERGENCY_STOP, INPUT_PULLUP); \
    pinMode(PIN_MODE_SELECT, INPUT_PULLUP)

#endif // PINS_H
