#include "tasks/TelemetryTask.h"
#include <Arduino.h>
#include <WiFi.h>

// ============================================================================
// CONSTRUCTOR AND DESTRUCTOR
// ============================================================================

TelemetryTask::TelemetryTask() 
    : isActive(false), lastTransmissionTime(0), telemetryInterval(TELEMETRY_UPDATE_RATE) {
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
    while (true) {
        if (isActive) {
            processTelemetry();
        }
        
        // Update at specified interval
        vTaskDelay(pdMS_TO_TICKS(telemetryInterval));
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
    
    // Check if we have connected clients
    if (!hasConnectedClients()) {
        return; // No clients connected, skip transmission
    }
    
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

// ============================================================================
// TELEMETRY DATA BUILDING
// ============================================================================

void TelemetryTask::buildTelemetryData() {
    // Clear previous data
    telemetryDoc.clear();
    
    // Get current timestamp
    telemetryDoc["timestamp"] = millis();
    telemetryDoc["type"] = "telemetry";
    
    // Get GPS position data
    GPSPosition currentPosition;
    if (sharedData.getPosition(currentPosition)) {
        JsonObject position = telemetryDoc.createNestedObject("position");
        position["latitude"] = currentPosition.latitude;
        position["longitude"] = currentPosition.longitude;
        position["isValid"] = currentPosition.isValid;
        position["timestamp"] = currentPosition.timestamp;
    }
    
    // Get IMU data
    IMUData currentIMUData;
    if (sharedData.getIMUData(currentIMUData)) {
        JsonObject imu = telemetryDoc.createNestedObject("imu");
        imu["heading"] = currentIMUData.heading;
        imu["temperature"] = currentIMUData.temperature;
        imu["isValid"] = currentIMUData.isValid;
        imu["timestamp"] = currentIMUData.timestamp;
        
        // Add acceleration data
        JsonArray acceleration = imu.createNestedArray("acceleration");
        acceleration.add(currentIMUData.acceleration[0]);
        acceleration.add(currentIMUData.acceleration[1]);
        acceleration.add(currentIMUData.acceleration[2]);
        
        // Add gyroscope data
        JsonArray gyroscope = imu.createNestedArray("gyroscope");
        gyroscope.add(currentIMUData.gyroscope[0]);
        gyroscope.add(currentIMUData.gyroscope[1]);
        gyroscope.add(currentIMUData.gyroscope[2]);
        
        // Add magnetometer data
        JsonArray magnetometer = imu.createNestedArray("magnetometer");
        magnetometer.add(currentIMUData.magnetometer[0]);
        magnetometer.add(currentIMUData.magnetometer[1]);
        magnetometer.add(currentIMUData.magnetometer[2]);
    }
    
    // Get rover state
    RoverState roverState;
    if (sharedData.getRoverState(roverState)) {
        JsonObject state = telemetryDoc.createNestedObject("rover");
        state["isNavigating"] = roverState.isNavigating;
        state["isConnected"] = roverState.isConnected;
        state["currentWaypointIndex"] = roverState.currentWaypointIndex;
        state["totalWaypoints"] = roverState.totalWaypoints;
        state["currentSpeed"] = roverState.currentSpeed;
        state["lastUpdateTime"] = roverState.lastUpdateTime;
        // Mission-related rover fields
        state["missionState"] = (int)sharedData.getMissionState();
        state["currentSegmentIndex"] = roverState.currentSegmentIndex;
        state["totalSegments"] = roverState.totalSegments;
        state["missionProgressPct"] = roverState.missionProgress;
        state["distanceToTarget"] = roverState.distanceToTarget;
        state["totalDistance"] = roverState.totalDistance;
        state["crossTrackError"] = roverState.crossTrackError;
        state["missionElapsedMs"] = roverState.missionElapsedTime;
        state["etaSec"] = roverState.estimatedTimeRemaining;
    }
    
    // Get system status
    SystemStatus systemStatus;
    if (sharedData.getSystemStatus(systemStatus)) {
        JsonObject status = telemetryDoc.createNestedObject("system");
        status["wifiConnected"] = systemStatus.wifiConnected;
        status["gpsFix"] = systemStatus.gpsFix;
        status["imuCalibrated"] = systemStatus.imuCalibrated;
        status["wifiSignalStrength"] = systemStatus.wifiSignalStrength;
        status["batteryVoltage"] = systemStatus.batteryVoltage;
        status["uptime"] = systemStatus.uptime;
    }
    
    // Add WiFi information
    JsonObject wifi = telemetryDoc.createNestedObject("wifi");
    wifi["connected"] = WiFi.status() == WL_CONNECTED;
    wifi["ssid"] = WiFi.SSID();
    wifi["rssi"] = WiFi.RSSI();
    wifi["localIP"] = WiFi.localIP().toString();
    
    // Add waypoints information
    int waypointCount = sharedData.getWaypointCount();
    if (waypointCount > 0) {
        JsonArray waypoints = telemetryDoc.createNestedArray("waypoints");
        for (int i = 0; i < waypointCount; i++) {
            Waypoint waypoint;
            if (sharedData.getWaypoint(i, waypoint)) {
                JsonObject wp = waypoints.createNestedObject();
                wp["index"] = i;
                wp["latitude"] = waypoint.latitude;
                wp["longitude"] = waypoint.longitude;
                wp["isValid"] = waypoint.isValid;
            }
        }
    }

    // Mission info summary
    {
        JsonObject mission = telemetryDoc.createNestedObject("mission");
        mission["id"] = sharedData.getMissionId();
        mission["state"] = (int)sharedData.getMissionState();
        mission["segmentCount"] = sharedData.getPathSegmentCount();
        // Parameters snapshot
        MissionParameters mp = sharedData.getMissionParameters();
        JsonObject params = mission.createNestedObject("parameters");
        params["speed_mps"] = mp.speed_mps;
        params["cte_threshold_m"] = mp.cte_threshold_m;
        params["mission_timeout_s"] = mp.mission_timeout_s;
        params["total_distance_m"] = mp.total_distance_m;
        params["estimated_duration_s"] = mp.estimated_duration_s;
    }
    
    // Add memory information
    JsonObject memory = telemetryDoc.createNestedObject("memory");
    memory["freeHeap"] = ESP.getFreeHeap();
    memory["minFreeHeap"] = ESP.getMinFreeHeap();
    memory["maxAllocHeap"] = ESP.getMaxAllocHeap();
    memory["heapFragmentation"] = 0; // ESP.getHeapFragmentation() not available
}

// ============================================================================
// TELEMETRY TRANSMISSION
// ============================================================================

void TelemetryTask::sendTelemetryData() {
    // Serialize JSON to string
    String telemetryString;
    serializeJson(telemetryDoc, telemetryString);
    
    // Add newline for TCP transmission
    telemetryString += "\n";
    
    // Send to all connected clients
    // Note: This assumes the WiFiTask has a method to broadcast to clients
    // For now, we'll print to serial for debugging
    Serial.println("[Telemetry] Sending telemetry data:");
    Serial.println(telemetryString);
    
    // TODO: Implement actual client transmission through WiFiTask
    // This would require a method in WiFiTask to broadcast to connected clients
    // For example: wifiTask.broadcastToClients(telemetryString);
}

// ============================================================================
// CLIENT CONNECTION CHECK
// ============================================================================

bool TelemetryTask::hasConnectedClients() {
    // Check if WiFi is connected
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }
    
    // TODO: Check if there are actual TCP clients connected
    // This would require a method in WiFiTask to check client connections
    // For now, we'll assume there's always a client when WiFi is connected
    
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
