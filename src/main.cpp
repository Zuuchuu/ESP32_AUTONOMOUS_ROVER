#include <Arduino.h>
#include <WiFi.h>
#include <Wire.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

// Configuration includes
#include "config/config.h"
#include "config/pins.h"
#include "config/wifi_config.h"

// Core includes
#include "core/SharedData.h"


// Task includes
#include "tasks/WiFiTask.h"
#include "tasks/GPSTask.h"
#include "tasks/IMUTask.h"
#include "tasks/NavigationTask.h"
#include "tasks/TelemetryTask.h"
#include "tasks/ManualControlTask.h"

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

// Task handles
TaskHandle_t wifiTaskHandle = NULL;
TaskHandle_t gpsTaskHandle = NULL;
TaskHandle_t imuTaskHandle = NULL;
TaskHandle_t navigationTaskHandle = NULL;
TaskHandle_t telemetryTaskHandle = NULL;
TaskHandle_t manualControlTaskHandle = NULL;

// Task instances
WiFiTask wifiTask;
GPSTask gpsTask;
IMUTask imuTask;
NavigationTask navigationTask;
TelemetryTask telemetryTask;
ManualControlTask manualControlTask;

// System state
bool systemInitialized = false;

// ============================================================================
// FORWARD DECLARATIONS
// ============================================================================

void setupPins();
void setupWiFi();
void createTasks();
void startTasks();
void systemWatchdog();

// ============================================================================
// TASK FUNCTION PROTOTYPES
// ============================================================================

// Task functions are declared in their respective header files
// and implemented in their .cpp files

// ============================================================================
// ARDUINO SETUP FUNCTION
// ============================================================================

void setup() {
    Serial.begin(115200);
    Serial.println("ESP32 Autonomous Rover starting up...");
    
    // Initialize shared data
    if (!sharedData.initialize()) {
        Serial.println("ERROR: Failed to initialize shared data");
        return;
    }
    
    // Setup hardware pins
    setupPins();
    
    // Setup WiFi
    setupWiFi();
    
    // Create FreeRTOS tasks
    createTasks();
    
    // Start all tasks
    startTasks();
    
    systemInitialized = true;
    Serial.println("System initialization complete");
    
    // Print initial status
    sharedData.printStatus();
}

// ============================================================================
// ARDUINO LOOP FUNCTION
// ============================================================================

void loop() {
    // Main loop is mostly empty since we use FreeRTOS tasks
    // This can be used for system monitoring and watchdog functionality
    
    static unsigned long lastWatchdogTime = 0;
    unsigned long currentTime = millis();
    
    // Run system watchdog every 5 seconds
    if (currentTime - lastWatchdogTime > 5000) {
        systemWatchdog();
        lastWatchdogTime = currentTime;
    }
    
    // Small delay to prevent watchdog from consuming too much CPU
    delay(100);
}

// ============================================================================
// SETUP FUNCTIONS
// ============================================================================

void setupPins() {
    Serial.println("Setting up hardware pins...");
    
    // Setup motor control pins
    SETUP_MOTOR_PINS();
    
    // Setup status LED pins
    SETUP_STATUS_PINS();
    
    // Setup button pins (optional)
    SETUP_BUTTON_PINS();
    
    // Initialize PWM for motor control
    ledcSetup(PWM_CHANNEL_LEFT, PWM_FREQ, PWM_RESOLUTION);
    ledcSetup(PWM_CHANNEL_RIGHT, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(PIN_LEFT_MOTOR_PWM, PWM_CHANNEL_LEFT);
    ledcAttachPin(PIN_RIGHT_MOTOR_PWM, PWM_CHANNEL_RIGHT);
    
    Serial.println("Hardware pins setup complete");
}

void setupWiFi() {
    Serial.println("Setting up WiFi connection...");
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < WIFI_MAX_RETRIES) {
        delay(WIFI_RETRY_DELAY_MS);
        attempts++;
        Serial.printf("WiFi connection attempt %d/%d\n", attempts, WIFI_MAX_RETRIES);
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("WiFi connected successfully");
        Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("RSSI: %d dBm\n", WiFi.RSSI());
        
        // Update system status
        SystemStatus status;
        sharedData.getSystemStatus(status);
        status.wifiConnected = true;
        status.wifiSignalStrength = WiFi.RSSI();
        sharedData.setSystemStatus(status);
    } else {
        Serial.printf("ERROR: WiFi connection failed after %d attempts\n", WIFI_MAX_RETRIES);
    }
}

void createTasks() {
    Serial.println("Creating FreeRTOS tasks...");
    
    // Create WiFi task
    xTaskCreatePinnedToCore(
        wifiTaskFunction,
        "WiFiTask",
        TASK_STACK_SIZE_WIFI,
        &wifiTask,
        TASK_PRIORITY_WIFI,
        &wifiTaskHandle,
        TASK_CORE_WIFI
    );
    
    // Create GPS task
    xTaskCreatePinnedToCore(
        gpsTaskFunction,
        "GPSTask",
        TASK_STACK_SIZE_GPS,
        &gpsTask,
        TASK_PRIORITY_GPS,
        &gpsTaskHandle,
        TASK_CORE_GPS
    );
    
    // Create IMU task
    xTaskCreatePinnedToCore(
        imuTaskFunction,
        "IMUTask",
        TASK_STACK_SIZE_IMU,
        &imuTask,
        TASK_PRIORITY_IMU,
        &imuTaskHandle,
        TASK_CORE_IMU
    );
    
    // Create Navigation task
    xTaskCreatePinnedToCore(
        navigationTaskFunction,
        "NavigationTask",
        TASK_STACK_SIZE_NAVIGATION,
        &navigationTask,
        TASK_PRIORITY_NAVIGATION,
        &navigationTaskHandle,
        TASK_CORE_NAVIGATION
    );
    
    // Set up telemetry transmission callback BEFORE creating the task
    telemetryTask.setTelemetryTransmitter([](const String& data) {
        if (wifiTask.isClientConnected()) {
            wifiTask.sendRaw(data);
        }
    });
    
    // Create Telemetry task (now with callback already set)
    xTaskCreatePinnedToCore(
        telemetryTaskFunction,
        "TelemetryTask",
        TASK_STACK_SIZE_TELEMETRY,
        &telemetryTask,
        TASK_PRIORITY_TELEMETRY,
        &telemetryTaskHandle,
        TASK_CORE_TELEMETRY
    );
    
    // Create Manual Control task (higher priority than navigation)
    xTaskCreatePinnedToCore(
        manualControlTaskFunction,
        "ManualControlTask",
        TASK_STACK_SIZE_NAVIGATION,  // Use same stack size as navigation
        &manualControlTask,
        TASK_PRIORITY_NAVIGATION + 1,  // Higher priority than navigation
        &manualControlTaskHandle,
        TASK_CORE_NAVIGATION
    );
    
    // Initialize manual control task
    if (!manualControlTask.initialize()) {
        Serial.println("ERROR: Failed to initialize manual control task");
    }
    
    // Give the telemetry task time to start and initialize
    vTaskDelay(pdMS_TO_TICKS(1000));
    
    // Start telemetry task now that it's running
    telemetryTask.startTelemetry();
    
    Serial.println("All tasks created successfully");
}

void startTasks() {
    Serial.println("Starting all tasks...");
    
    // Tasks will start automatically when created
    // We can add additional startup logic here if needed
    
    Serial.println("All tasks started");
}

// ============================================================================
// TASK FUNCTIONS
// ============================================================================

// All task functions are now implemented in their respective .cpp files:
// - wifiTaskFunction in WiFiTask.cpp
// - gpsTaskFunction in GPSTask.cpp  
// - imuTaskFunction in IMUTask.cpp
// - navigationTaskFunction in NavigationTask.cpp
// - telemetryTaskFunction in TelemetryTask.cpp
// - manualControlTaskFunction in ManualControlTask.cpp

// ============================================================================
// SYSTEM MONITORING
// ============================================================================

void systemWatchdog() {
    static unsigned long lastMemoryLog = 0;
    unsigned long currentTime = millis();
    
    // Log memory usage every 30 seconds
    if (currentTime - lastMemoryLog > 30000) {
        Serial.printf("Free heap: %d bytes\n", ESP.getFreeHeap());
        Serial.printf("Min free heap: %d bytes\n", ESP.getMinFreeHeap());
        lastMemoryLog = currentTime;
    }
    
    // Check task status
    if (wifiTaskHandle && eTaskGetState(wifiTaskHandle) == eDeleted) {
        Serial.println("ERROR: WiFi task has been deleted unexpectedly");
    }
    
    if (gpsTaskHandle && eTaskGetState(gpsTaskHandle) == eDeleted) {
        Serial.println("ERROR: GPS task has been deleted unexpectedly");
    }
    
    if (imuTaskHandle && eTaskGetState(imuTaskHandle) == eDeleted) {
        Serial.println("ERROR: IMU task has been deleted unexpectedly");
    }
    
    if (navigationTaskHandle && eTaskGetState(navigationTaskHandle) == eDeleted) {
        Serial.println("ERROR: Navigation task has been deleted unexpectedly");
    }
    
    if (telemetryTaskHandle && eTaskGetState(telemetryTaskHandle) == eDeleted) {
        Serial.println("ERROR: Telemetry task has been deleted unexpectedly");
    }
    
    if (manualControlTaskHandle && eTaskGetState(manualControlTaskHandle) == eDeleted) {
        Serial.println("ERROR: Manual Control task has been deleted unexpectedly");
    }
    
    // Update system uptime
    SystemStatus status;
    if (sharedData.getSystemStatus(status)) {
        status.uptime = currentTime;
        sharedData.setSystemStatus(status);
    }
}