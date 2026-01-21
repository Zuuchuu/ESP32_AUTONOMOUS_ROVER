#ifndef LOG_LEVEL_H
#define LOG_LEVEL_H

// ============================================================================
// COMPILE-TIME LOG LEVEL SYSTEM
// ============================================================================
// Usage: Define LOG_LEVEL in platformio.ini build_flags for production:
//   build_flags = -DLOG_LEVEL=LOG_LEVEL_WARN
// Default is INFO level for development builds.

#define LOG_LEVEL_NONE    0
#define LOG_LEVEL_ERROR   1
#define LOG_LEVEL_WARN    2
#define LOG_LEVEL_INFO    3
#define LOG_LEVEL_DEBUG   4
#define LOG_LEVEL_VERBOSE 5

#ifndef LOG_LEVEL
#define LOG_LEVEL LOG_LEVEL_INFO  // Default for development
#endif

// ============================================================================
// LOGGING MACROS
// ============================================================================
// These macros are compile-time filtered - disabled levels produce no code.

#if LOG_LEVEL >= LOG_LEVEL_ERROR
#define LOG_ERROR(fmt, ...) Serial.printf("[ERR] " fmt "\n", ##__VA_ARGS__)
#else
#define LOG_ERROR(fmt, ...) ((void)0)
#endif

#if LOG_LEVEL >= LOG_LEVEL_WARN
#define LOG_WARN(fmt, ...) Serial.printf("[WRN] " fmt "\n", ##__VA_ARGS__)
#else
#define LOG_WARN(fmt, ...) ((void)0)
#endif

#if LOG_LEVEL >= LOG_LEVEL_INFO
#define LOG_INFO(fmt, ...) Serial.printf("[INF] " fmt "\n", ##__VA_ARGS__)
#else
#define LOG_INFO(fmt, ...) ((void)0)
#endif

#if LOG_LEVEL >= LOG_LEVEL_DEBUG
#define LOG_DEBUG(fmt, ...) Serial.printf("[DBG] " fmt "\n", ##__VA_ARGS__)
#else
#define LOG_DEBUG(fmt, ...) ((void)0)
#endif

#if LOG_LEVEL >= LOG_LEVEL_VERBOSE
#define LOG_VERBOSE(fmt, ...) Serial.printf("[VRB] " fmt "\n", ##__VA_ARGS__)
#else
#define LOG_VERBOSE(fmt, ...) ((void)0)
#endif

// ============================================================================
// TASK-SPECIFIC LOG MACROS
// ============================================================================
// Use these for consistent task identification in log output.

#define LOG_TASK_ERROR(task, fmt, ...) LOG_ERROR("[%s] " fmt, task, ##__VA_ARGS__)
#define LOG_TASK_WARN(task, fmt, ...)  LOG_WARN("[%s] " fmt, task, ##__VA_ARGS__)
#define LOG_TASK_INFO(task, fmt, ...)  LOG_INFO("[%s] " fmt, task, ##__VA_ARGS__)
#define LOG_TASK_DEBUG(task, fmt, ...) LOG_DEBUG("[%s] " fmt, task, ##__VA_ARGS__)

#endif // LOG_LEVEL_H
