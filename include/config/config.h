#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ============================================================================
// SYSTEM CONFIGURATION
// ============================================================================

// Task Priorities (Higher number = higher priority)
// Critical path: Sensors -> Navigation -> Control
#define TASK_PRIORITY_ENCODER     4  // Highest - timing critical encoder ISR data
#define TASK_PRIORITY_IMU         4  // High - 100Hz sensor fusion
#define TASK_PRIORITY_NAVIGATION  3  // Real-time motor control
#define TASK_PRIORITY_GPS         2  // Medium - 1Hz updates
#define TASK_PRIORITY_TOF         2  // Medium - obstacle detection
#define TASK_PRIORITY_WIFI        2  // Medium - command handling
#define TASK_PRIORITY_TELEMETRY   1  // Low - can be delayed
#define TASK_PRIORITY_DISPLAY     1  // Lowest - cosmetic only

// Task Stack Sizes (in bytes)
// Optimized based on function requirements + 512-byte safety margin
// Monitor with uxTaskGetStackHighWaterMark() to verify
#define TASK_STACK_SIZE_WIFI      3072  // JSON parsing, TCP buffer
#define TASK_STACK_SIZE_GPS       2048  // Serial parsing only
#define TASK_STACK_SIZE_IMU       3072  // I2C + NVS + sensor fusion
#define TASK_STACK_SIZE_NAVIGATION 3072  // PID + trig calculations
#define TASK_STACK_SIZE_TELEMETRY 3584  // JSON serialization (largest payload)
#define TASK_STACK_SIZE_DISPLAY   2048  // Simple I2C writes
#define TASK_STACK_SIZE_TOF       3072  // VL53L0X I2C + ranging operations
#define TASK_STACK_SIZE_ENCODER   1536  // ISR-based, minimal logic

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
#define MOTOR_MAX_RPM            120.0     // N20 150:1 @ 5V DC (approx)
#define MOTOR_GEAR_RATIO         150       // 150:1 gear ratio
#define MOTOR_ENCODER_PPR        7         // Hall encoder pulses per motor shaft rev

// Encoder CPR (Counts Per Revolution of OUTPUT shaft)
// CPR = PPR × 4 (quadrature edges) × gear ratio = 7 × 4 × 150 = 4200
#define LEFT_MOTOR_ENCODER_CPR   4200.0f
#define RIGHT_MOTOR_ENCODER_CPR  4200.0f

// Motor Speed PID (inner loop - controls individual wheel speeds)
#define MOTOR_PID_KP             2.0f
#define MOTOR_PID_KI             0.1f
#define MOTOR_PID_KD             0.05f
#define MOTOR_PID_INTERVAL_MS    20        // 50Hz update rate

// Max counts per PID interval at max RPM
// (120 RPM / 60) × 4200 CPR × 0.020s = 168 counts/interval
#define MAX_COUNTS_PER_LOOP      168

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

#define GPS_BAUD_RATE            38400
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
