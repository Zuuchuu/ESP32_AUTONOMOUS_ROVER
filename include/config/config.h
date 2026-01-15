#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ============================================================================
// SYSTEM CONFIGURATION
// ============================================================================

// Task Priorities (Higher number = higher priority)
#define TASK_PRIORITY_WIFI        1
#define TASK_PRIORITY_GPS         2
#define TASK_PRIORITY_IMU         2
#define TASK_PRIORITY_NAVIGATION  3
#define TASK_PRIORITY_TELEMETRY   1
#define TASK_PRIORITY_DISPLAY     1
#define TASK_PRIORITY_TOF         2
#define TASK_PRIORITY_ENCODER     2

// Task Stack Sizes (in bytes)
#define TASK_STACK_SIZE_WIFI      4096
#define TASK_STACK_SIZE_GPS       4096
#define TASK_STACK_SIZE_IMU       4096
#define TASK_STACK_SIZE_NAVIGATION 4096
#define TASK_STACK_SIZE_TELEMETRY 4096
#define TASK_STACK_SIZE_DISPLAY   4096
#define TASK_STACK_SIZE_TOF       4096
#define TASK_STACK_SIZE_ENCODER   4096

// Task Core Assignment (0 or 1)
#define TASK_CORE_WIFI           0
#define TASK_CORE_GPS            0
#define TASK_CORE_IMU            0
#define TASK_CORE_NAVIGATION     1
#define TASK_CORE_TELEMETRY      1
#define TASK_CORE_DISPLAY        0
#define TASK_CORE_TOF            0
#define TASK_CORE_ENCODER        0

// ============================================================================
// NETWORK CONFIGURATION
// ============================================================================

#define SERVER_PORT              80
#define TCP_SERVER_PORT          80
#define MAX_CLIENTS              1
#define JSON_BUFFER_SIZE         1024

// ============================================================================
// NAVIGATION CONFIGURATION
// ============================================================================

#define WAYPOINT_THRESHOLD       0.3    // meters
#define BASE_SPEED               100    // PWM 0-255 (Approx 8 cm/s)
#define K_XTE                    10.0   // degrees per meter (Cross Track Error gain)

// PID Coefficients (Heuristic Tuning for N20 Motors - Standard Steering)
// Scaled for dt-based calculation
#define KP                       5.00   // Proportional (1 deg error -> 5 PWM diff)
#define KI                       0.01   // Integral (Slow accumulation)
#define KD                       0.10   // Derivative (Damping)

#define EARTH_RADIUS             6371000 // meters

// ============================================================================
// MECH & MOTOR CONFIGURATION
// ============================================================================

#define WHEEL_DIAMETER_MM        43.0
#define TRACK_WIDTH_MM           140.0
#define MOTOR_MAX_RPM            90.0
#define MOTOR_ENCODER_CPR        3575.0

// Calculated Constants
// Max Speed = 90 RPM * (pi * 0.043) / 60 ~= 0.20 m/s
// Counts per Loop (20ms @ 90RPM): (90/60) * 3575 * 0.02 ~= 107
#define MAX_COUNTS_PER_LOOP      107    // For Speed PID Feedforward

// ============================================================================
// MOTOR CONFIGURATION
// ============================================================================

#define PWM_FREQ                 5000
#define PWM_RESOLUTION           8
#define PWM_CHANNEL_LEFT         0
#define PWM_CHANNEL_RIGHT        1

// ============================================================================
// SENSOR CONFIGURATION
// ============================================================================

#define GPS_BAUD_RATE            9600
#define IMU_UPDATE_RATE          100    // ms
#define GPS_UPDATE_RATE          1000   // ms
#define TELEMETRY_UPDATE_RATE    1000   // ms
#define DISPLAY_UPDATE_RATE      200    // ms (5Hz)
#define TOF_UPDATE_RATE          100    // ms (10Hz)
#define ENCODER_UPDATE_RATE      50     // ms (20Hz)

// ============================================================================
// SYSTEM LIMITS
// ============================================================================

#define MAX_WAYPOINTS            10
#define MAX_JSON_STRING_LENGTH   512
#define MAX_RECONNECT_ATTEMPTS   5
#define WIFI_TIMEOUT_MS          10000

// ============================================================================
// DEBUG CONFIGURATION
// ============================================================================

#define DEBUG_SERIAL_BAUD        115200
#define ENABLE_DEBUG_LOGGING     true
#define ENABLE_SENSOR_DEBUG      true
#define ENABLE_NAVIGATION_DEBUG  true

// ============================================================================
// ERROR HANDLING
// ============================================================================

#define ERROR_RETRY_DELAY_MS     1000
#define MAX_ERROR_RETRIES        3
#define WATCHDOG_TIMEOUT_MS      30000

#endif // CONFIG_H
