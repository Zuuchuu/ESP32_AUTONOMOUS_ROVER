#include "tasks/TelemetryTask.h"
#include "tasks/GPSTask.h"
#include "core/SharedData.h"
#include <Arduino.h>
#include <WiFi.h>
#include <functional>

// External GPS task instance
extern GPSTask gpsTask;

// ============================================================================
// CONSTRUCTOR AND DESTRUCTOR
// ============================================================================

TelemetryTask::TelemetryTask() 
    : isActive(false), lastTransmissionTime(0), telemetryInterval(TELEMETRY_UPDATE_RATE), telemetryTransmitter(nullptr) {
}

TelemetryTask::~TelemetryTask() {
    // Cleanup if needed
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool TelemetryTask::initialize() {
    Serial.println("[Telemetry] Initializing telemetry system...");
    
    // Initialize JSON document
    telemetryDoc.clear();
    
    // Set initial state
    isActive = false;
    lastTransmissionTime = 0;
    
    Serial.println("[Telemetry] Telemetry system initialized successfully");
    return true;
}

// ============================================================================
// MAIN TELEMETRY LOOP
// ============================================================================

void TelemetryTask::run() {
    Serial.println("[Telemetry] Telemetry task loop started");
    
    while (true) {
        if (isActive) {
            processTelemetry();
            
            // Debug output every 5 seconds when active
            static unsigned long lastDebugTime = 0;
            if (millis() - lastDebugTime > 5000) {
                Serial.printf("[Telemetry] Task running, Active: %s, Interval: %lu ms, Clients: %s\n", 
                           isActive ? "Yes" : "No", telemetryInterval, 
                           hasConnectedClients() ? "Available" : "None");
                lastDebugTime = millis();
            }
        } else {
            // Debug output every 10 seconds when inactive
            static unsigned long lastInactiveDebugTime = 0;
            if (millis() - lastInactiveDebugTime > 10000) {
                Serial.println("[Telemetry] Task waiting for activation...");
                lastInactiveDebugTime = millis();
            }
        }
        
        // Small delay to prevent watchdog issues
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

// ============================================================================
// TELEMETRY PROCESSING
// ============================================================================

void TelemetryTask::processTelemetry() {
    unsigned long currentTime = millis();
    
    // Check if it's time to send telemetry
    if (currentTime - lastTransmissionTime < telemetryInterval) {
        return;
    }
    
    lastTransmissionTime = currentTime;
    
    // Always process telemetry when active, regardless of client status
    // The transmission callback will handle client availability
    if (isActive) {
        // Build and send telemetry data
        buildTelemetryData();
        sendTelemetryData();
        
        // Print telemetry info periodically
        static unsigned long lastPrintTime = 0;
        if (currentTime - lastPrintTime > 10000) { // Print every 10 seconds
            printTelemetryInfo();
            lastPrintTime = currentTime;
        }
    }
}

// ============================================================================
// TELEMETRY DATA BUILDING
// ============================================================================

void TelemetryTask::buildTelemetryData() {
    // Clear previous data
    telemetryDoc.clear();
    
    // Get GPS position data
    GPSPosition currentPosition;
    bool hasPosition = sharedData.getPosition(currentPosition);
    
    // Get IMU data  
    IMUData currentIMUData;
    bool hasIMU = sharedData.getIMUData(currentIMUData);
    
    // Build Control Station compatible format
    if (hasPosition) {
        telemetryDoc["lat"] = currentPosition.latitude;
        telemetryDoc["lon"] = currentPosition.longitude;
        
        // Add GPS metadata from GPSTask
        telemetryDoc["altitude"] = gpsTask.getAltitude();
        telemetryDoc["satellites"] = gpsTask.getSatellites();
        telemetryDoc["hdop"] = gpsTask.getHDOP();
    } else {
        telemetryDoc["lat"] = 0.0;
        telemetryDoc["lon"] = 0.0;
        telemetryDoc["altitude"] = 0.0;
        telemetryDoc["satellites"] = 0;
        telemetryDoc["hdop"] = 99.0;
    }
    
    if (hasIMU) {
        telemetryDoc["heading"] = currentIMUData.heading;
        telemetryDoc["temperature"] = currentIMUData.temperature;
        
        // Create BNO055 enhanced IMU data structure
        JsonObject imu_data = telemetryDoc["imu_data"].to<JsonObject>();
        
        // Enhanced BNO055 data 
        imu_data["roll"] = currentIMUData.roll;
        imu_data["pitch"] = currentIMUData.pitch;
        
        // Quaternion
        JsonArray quat = imu_data["quaternion"].to<JsonArray>();
        quat.add(currentIMUData.quaternion[0]);
        quat.add(currentIMUData.quaternion[1]);
        quat.add(currentIMUData.quaternion[2]);
        quat.add(currentIMUData.quaternion[3]);
        
        // Raw sensor data
        JsonArray accel = imu_data["accel"].to<JsonArray>();
        accel.add(currentIMUData.acceleration[0]);
        accel.add(currentIMUData.acceleration[1]);
        accel.add(currentIMUData.acceleration[2]);
        
        JsonArray gyro = imu_data["gyro"].to<JsonArray>();
        gyro.add(currentIMUData.gyroscope[0]);
        gyro.add(currentIMUData.gyroscope[1]);
        gyro.add(currentIMUData.gyroscope[2]);
        
        JsonArray mag = imu_data["mag"].to<JsonArray>();
        mag.add(currentIMUData.magnetometer[0]);
        mag.add(currentIMUData.magnetometer[1]);
        mag.add(currentIMUData.magnetometer[2]);
        
        // Enhanced BNO055 data
        JsonArray linear_accel = imu_data["linear_accel"].to<JsonArray>();
        linear_accel.add(currentIMUData.linearAccel[0]);
        linear_accel.add(currentIMUData.linearAccel[1]);
        linear_accel.add(currentIMUData.linearAccel[2]);
        
        JsonArray gravity = imu_data["gravity"].to<JsonArray>();
        gravity.add(currentIMUData.gravity[0]);
        gravity.add(currentIMUData.gravity[1]);
        gravity.add(currentIMUData.gravity[2]);
        
        // BNO055 calibration status
        JsonObject cal = imu_data["calibration"].to<JsonObject>();
        cal["sys"] = currentIMUData.calibrationStatus.system;
        cal["gyro"] = currentIMUData.calibrationStatus.gyroscope;
        cal["accel"] = currentIMUData.calibrationStatus.accelerometer;
        cal["mag"] = currentIMUData.calibrationStatus.magnetometer;
        
        // Temperature in IMU data for BNO055
        imu_data["temperature"] = currentIMUData.temperature;
    } else {
        telemetryDoc["heading"] = 0.0;
        telemetryDoc["temperature"] = 0.0;
        
        // Create empty IMU structure
        JsonObject imu_data = telemetryDoc["imu_data"].to<JsonObject>();
        imu_data["roll"] = 0.0;
        imu_data["pitch"] = 0.0;
        
        JsonArray quat = imu_data["quaternion"].to<JsonArray>();
        quat.add(1.0); quat.add(0.0); quat.add(0.0); quat.add(0.0);
        
        JsonArray accel = imu_data["accel"].to<JsonArray>();
        accel.add(0.0); accel.add(0.0); accel.add(0.0);
        
        JsonArray gyro = imu_data["gyro"].to<JsonArray>();
        gyro.add(0.0); gyro.add(0.0); gyro.add(0.0);
        
        JsonArray mag = imu_data["mag"].to<JsonArray>();
        mag.add(0.0); mag.add(0.0); mag.add(0.0);
        
        JsonArray linear_accel = imu_data["linear_accel"].to<JsonArray>();
        linear_accel.add(0.0); linear_accel.add(0.0); linear_accel.add(0.0);
        
        JsonArray gravity = imu_data["gravity"].to<JsonArray>();
        gravity.add(0.0); gravity.add(0.0); gravity.add(0.0);
        
        JsonObject cal = imu_data["calibration"].to<JsonObject>();
        cal["sys"] = 0; cal["gyro"] = 0; cal["accel"] = 0; cal["mag"] = 0;
        
        imu_data["temperature"] = 0.0;
    }
    
    // Add WiFi signal strength
    telemetryDoc["wifi_strength"] = WiFi.RSSI();
    
    // Add sensor connection status (individual IMU sensors)
    JsonObject sensors = telemetryDoc["sensors"].to<JsonObject>();
    sensors["accel"] = hasIMU;  // Accelerometer
    sensors["gyro"] = hasIMU;   // Gyroscope
    sensors["mag"] = hasIMU;    // Magnetometer
    sensors["gps"] = hasPosition && currentPosition.isValid;  // GPS with valid fix
    sensors["tof"] = false; // TODO: Add TOF sensor status when implemented
    
    
    // Add TOF sensor data (placeholder for future implementation)
    JsonObject tof_data = telemetryDoc["tof_data"].to<JsonObject>();
    tof_data["distance"] = 0; // millimeters
    tof_data["status"] = false;
    
    // Add basic system status for Control Station
    telemetryDoc["system_status"] = "operational";
    telemetryDoc["timestamp"] = millis();
}

// ============================================================================
// TELEMETRY TRANSMISSION
// ============================================================================

void TelemetryTask::sendTelemetryData() {
    // Serialize JSON directly to pre-allocated buffer (zero heap allocation)
    size_t len = serializeJson(telemetryDoc, telemetryBuffer, sizeof(telemetryBuffer) - 2);
    
    // Add newline for TCP transmission
    telemetryBuffer[len] = '\n';
    telemetryBuffer[len + 1] = '\0';
    len++;
    
    // Send to connected clients via telemetry transmitter callback
    if (telemetryTransmitter) {
        telemetryTransmitter(telemetryBuffer, len);
    }
    
    // Reduced debug logging (only every 30 seconds)
    static unsigned long lastSerialPrint = 0;
    if (millis() - lastSerialPrint > 30000) {
        Serial.printf("[Telemetry] Sent %d bytes\n", len);
        lastSerialPrint = millis();
    }
}

// ============================================================================
// CLIENT CONNECTION CHECK
// ============================================================================

bool TelemetryTask::hasConnectedClients() {
    // If telemetry is not active, no clients
    if (!isActive) {
        return false;
    }
    
    // Check if WiFi is connected
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }
    
    // Check if we have a telemetry transmitter callback set
    // This indicates that the system is ready to send data
    if (!telemetryTransmitter) {
        return false;
    }
    
    // Telemetry is active, WiFi is connected, and transmitter is set
    // The transmission callback will handle actual client availability
    return true;
}

// ============================================================================
// CONTROL METHODS
// ============================================================================

bool TelemetryTask::startTelemetry() {
    if (isActive) {
        Serial.println("[Telemetry] Already running");
        return false;
    }
    
    isActive = true;
    lastTransmissionTime = 0;
    Serial.println("[Telemetry] Telemetry transmission started");
    return true;
}

bool TelemetryTask::stopTelemetry() {
    if (!isActive) {
        return false;
    }
    
    isActive = false;
    Serial.println("[Telemetry] Telemetry transmission stopped");
    return true;
}

bool TelemetryTask::pauseTelemetry() {
    if (!isActive) {
        return false;
    }
    
    Serial.println("[Telemetry] Telemetry transmission paused");
    return true;
}

bool TelemetryTask::resumeTelemetry() {
    if (!isActive) {
        return false;
    }
    
    Serial.println("[Telemetry] Telemetry transmission resumed");
    return true;
}

// ============================================================================
// STATUS METHODS
// ============================================================================

bool TelemetryTask::isRunning() {
    return isActive;
}

unsigned long TelemetryTask::getLastTransmissionTime() {
    return lastTransmissionTime;
}

unsigned long TelemetryTask::getTelemetryInterval() {
    return telemetryInterval;
}

// ============================================================================
// CONFIGURATION METHODS
// ============================================================================

void TelemetryTask::setTelemetryInterval(unsigned long interval) {
    if (interval > 0) {
        telemetryInterval = interval;
        Serial.printf("[Telemetry] Telemetry interval set to %lu ms\n", interval);
    }
}

void TelemetryTask::setTransmissionEnabled(bool enabled) {
    if (enabled && !isActive) {
        startTelemetry();
    } else if (!enabled && isActive) {
        stopTelemetry();
    }
}

void TelemetryTask::setTelemetryTransmitter(std::function<void(const char*, size_t)> transmitter) {
    telemetryTransmitter = transmitter;
    Serial.println("[Telemetry] Telemetry transmitter callback set");
}

// ============================================================================
// DEBUG METHODS
// ============================================================================

void TelemetryTask::printTelemetryInfo() {
    Serial.println("=== Telemetry Status ===");
    Serial.printf("Active: %s\n", isActive ? "Yes" : "No");
    Serial.printf("Interval: %lu ms\n", telemetryInterval);
    Serial.printf("Last Transmission: %lu ms ago\n", millis() - lastTransmissionTime);
    Serial.printf("WiFi Connected: %s\n", WiFi.status() == WL_CONNECTED ? "Yes" : "No");
    Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
    Serial.println("=======================");
}

// ============================================================================
// FREE RTOS TASK FUNCTION
// ============================================================================

void telemetryTaskFunction(void* parameter) {
    TelemetryTask* telemetryTask = (TelemetryTask*)parameter;
    
    if (telemetryTask->initialize()) {
        telemetryTask->run();
    } else {
        Serial.println("[Telemetry] Failed to initialize telemetry task");
    }
    
    vTaskDelete(NULL);
}
