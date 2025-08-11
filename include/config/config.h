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

// Task Stack Sizes (in bytes)
#define TASK_STACK_SIZE_WIFI      8192
#define TASK_STACK_SIZE_GPS       4096
#define TASK_STACK_SIZE_IMU       4096
#define TASK_STACK_SIZE_NAVIGATION 8192
#define TASK_STACK_SIZE_TELEMETRY 4096

// Task Core Assignment (0 or 1)
#define TASK_CORE_WIFI           0
#define TASK_CORE_GPS            0
#define TASK_CORE_IMU            0
#define TASK_CORE_NAVIGATION     1
#define TASK_CORE_TELEMETRY      1

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

#define WAYPOINT_THRESHOLD       2.0    // meters
#define BASE_SPEED               100    // PWM 0-255
#define K_XTE                    10.0   // degrees per meter
#define KP                       0.5    // PID proportional gain
#define KI                       0.1    // PID integral gain
#define KD                       0.05   // PID derivative gain
#define EARTH_RADIUS             6371000 // meters

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
