#include "tasks/GPSTask.h"
#include "config/config.h"
#include "config/pins.h"

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

// Global instance defined in main.cpp

// ============================================================================
// CONSTRUCTOR/DESTRUCTOR
// ============================================================================

GPSTask::GPSTask() : gpsInitialized(false), lastUpdateTime(0), lastFixTime(0) {
}

GPSTask::~GPSTask() {
    stop();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool GPSTask::initialize() {
    Serial.println("Initializing GPS task...");
    
    // Initialize Serial2 for GPS communication
    Serial2.begin(GPS_BAUD_RATE, SERIAL_8N1, PIN_GPS_RX, PIN_GPS_TX);
    
    // Wait a moment for GPS to start
    delay(1000);
    
    // Check if GPS is responding
    unsigned long startTime = millis();
    bool gpsResponding = false;
    
    while (millis() - startTime < 5000) { // 5 second timeout
        while (Serial2.available()) {
            char c = Serial2.read();
            if (gps.encode(c)) {
                gpsResponding = true;
                break;
            }
        }
        if (gpsResponding) break;
        delay(100);
    }
    
    if (gpsResponding) {
        gpsInitialized = true;
        Serial.println("GPS initialized successfully");
        Serial.printf("GPS baud rate: %d\n", GPS_BAUD_RATE);
        return true;
    } else {
        Serial.println("ERROR: GPS not responding");
        return false;
    }
}

// ============================================================================
// MAIN RUN LOOP
// ============================================================================

void GPSTask::run() {
    if (!gpsInitialized) {
        Serial.println("ERROR: GPS not initialized");
        vTaskDelay(pdMS_TO_TICKS(1000));
        return;
    }
    
    // Read GPS data from Serial2
    bool newData = false;
    while (Serial2.available()) {
        char c = Serial2.read();
        if (gps.encode(c)) {
            newData = true;
        }
    }
    
    if (newData) {
        processGPSData();
        lastUpdateTime = millis();
    }
    
    // Check for GPS timeout (no data for 5 seconds)
    if (millis() - lastUpdateTime > 5000) {
        Serial.println("WARNING: No GPS data received for 5 seconds");
    }
}

// ============================================================================
// GPS DATA PROCESSING
// ============================================================================

void GPSTask::processGPSData() {
    // Check if we have a valid fix
    if (gps.location.isValid()) {
        updatePosition();
        lastFixTime = millis();
        
        // Print GPS info periodically
        static unsigned long lastPrintTime = 0;
        if (millis() - lastPrintTime > 10000) { // Every 10 seconds
            printGPSInfo();
            lastPrintTime = millis();
        }
    } else {
        // No valid fix
        if (millis() - lastFixTime > 30000) { // 30 seconds without fix
            Serial.println("WARNING: No GPS fix for 30 seconds");
            lastFixTime = millis(); // Reset timer
        }
    }
    
    // Update system status
    updateSystemStatus();
}

void GPSTask::updatePosition() {
    GPSPosition position;
    
    // Get current position from TinyGPS++
    position.latitude = gps.location.lat();
    position.longitude = gps.location.lng();
    position.timestamp = millis();
    
    // Validate position
    if (isValidPosition(position.latitude, position.longitude)) {
        // Update shared data
        if (sharedData.setPosition(position)) {
            Serial.printf("GPS: %.6f, %.6f\n", 
                         position.latitude, position.longitude);
        } else {
            Serial.println("ERROR: Failed to update GPS position in shared data");
        }
    } else {
        Serial.println("WARNING: Invalid GPS position received");
    }
}

void GPSTask::updateSystemStatus() {
    SystemStatus status;
    if (sharedData.getSystemStatus(status)) {
        status.gpsFix = gps.location.isValid();
        sharedData.setSystemStatus(status);
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

bool GPSTask::isValidPosition(double lat, double lng) {
    // Check for valid latitude (-90 to 90)
    if (lat < -90.0 || lat > 90.0) {
        return false;
    }
    
    // Check for valid longitude (-180 to 180)
    if (lng < -180.0 || lng > 180.0) {
        return false;
    }
    
    // Check for zero coordinates (likely invalid)
    if (lat == 0.0 && lng == 0.0) {
        return false;
    }
    
    return true;
}

void GPSTask::printGPSInfo() {
    Serial.println("=== GPS Status ===");
    Serial.printf("Fix: %s\n", gps.location.isValid() ? "YES" : "NO");
    Serial.printf("Satellites: %d\n", gps.satellites.value());
    Serial.printf("HDOP: %.1f\n", gps.hdop.value());
    
    if (gps.location.isValid()) {
        Serial.printf("Position: %.6f, %.6f\n", 
                     gps.location.lat(), gps.location.lng());
        Serial.printf("Altitude: %.1f m\n", gps.altitude.meters());
        Serial.printf("Speed: %.1f km/h\n", gps.speed.kmph());
        Serial.printf("Course: %.1f°\n", gps.course.deg());
    }
    
    Serial.printf("Last update: %lu ms ago\n", millis() - lastUpdateTime);
    Serial.println("==================");
}

bool GPSTask::hasFix() const {
    return gps.location.isValid();
}

int GPSTask::getSatellites() {
    return gps.satellites.isValid() ? gps.satellites.value() : 0;
}

float GPSTask::getHDOP() {
    return gps.hdop.isValid() ? gps.hdop.value() : 0.0f;
}

float GPSTask::getAltitude() {
    return gps.altitude.isValid() ? gps.altitude.meters() : 0.0f;
}

float GPSTask::getSpeed() {
    return gps.speed.isValid() ? gps.speed.kmph() : 0.0f;
}

void GPSTask::stop() {
    Serial2.end();
    gpsInitialized = false;
    Serial.println("GPS task stopped");
}

// ============================================================================
// TASK FUNCTION
// ============================================================================

void gpsTaskFunction(void* parameter) {
    Serial.println("GPS task started");
    
    if (!gpsTask.initialize()) {
        Serial.println("ERROR: Failed to initialize GPS task");
        vTaskDelete(NULL);
        return;
    }
    
    while (true) {
        gpsTask.run();
        vTaskDelay(pdMS_TO_TICKS(GPS_UPDATE_RATE));
    }
}
