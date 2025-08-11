#ifndef PINS_H
#define PINS_H

#include <Arduino.h>

// ============================================================================
// MOTOR DRIVER PINS (TB6612FNG)
// ============================================================================

// Left Motor Control
#define PIN_LEFT_MOTOR_PWM      12    // PWMA - PWM speed control
#define PIN_LEFT_MOTOR_IN1      27    // AI1 - Direction control 1
#define PIN_LEFT_MOTOR_IN2      14    // AI2 - Direction control 2

// Right Motor Control
#define PIN_RIGHT_MOTOR_PWM     32    // PWMB - PWM speed control
#define PIN_RIGHT_MOTOR_IN1     33    // BI1 - Direction control 1
#define PIN_RIGHT_MOTOR_IN2     25    // BI2 - Direction control 2

// Motor Driver Enable (if needed)
#define PIN_MOTOR_STBY          26    // STBY - Standby control (optional)

// ============================================================================
// GPS MODULE PINS (u-blox M10)
// ============================================================================

#define PIN_GPS_RX              16    // GPS TX -> ESP32 RX
#define PIN_GPS_TX              17    // GPS RX -> ESP32 TX

// ============================================================================
// IMU MODULE PINS (GY-87)
// ============================================================================

#define PIN_IMU_SDA             21    // I2C Data line
#define PIN_IMU_SCL             22    // I2C Clock line

// ============================================================================
// STATUS LED PINS (Optional)
// ============================================================================

#define PIN_STATUS_LED          2     // Built-in LED for status indication
#define PIN_WIFI_LED            4     // Optional LED for WiFi status
#define PIN_GPS_LED             5     // Optional LED for GPS fix status

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
    pinMode(PIN_MOTOR_STBY, OUTPUT); \
    digitalWrite(PIN_MOTOR_STBY, HIGH); // Enable motor driver

#define SETUP_STATUS_PINS() \
    pinMode(PIN_STATUS_LED, OUTPUT); \
    pinMode(PIN_WIFI_LED, OUTPUT); \
    pinMode(PIN_GPS_LED, OUTPUT)

#define SETUP_BUTTON_PINS() \
    pinMode(PIN_EMERGENCY_STOP, INPUT_PULLUP); \
    pinMode(PIN_MODE_SELECT, INPUT_PULLUP)

#endif // PINS_H
