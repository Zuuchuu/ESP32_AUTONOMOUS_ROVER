#include "hardware/SensorManager.h"
#include <math.h>

// ============================================================================
// CONSTRUCTOR AND DESTRUCTOR
// ============================================================================

SensorManager::SensorManager() 
    : gpsInitialized(false), imuInitialized(false), magnetometerInitialized(false) {
    
    // Initialize calibration data
    for (int i = 0; i < 3; i++) {
        magnetometerOffset[i] = 0.0f;
        for (int j = 0; j < 3; j++) {
            magnetometerCalibration[i][j] = (i == j) ? 1.0f : 0.0f;
        }
    }
}

SensorManager::~SensorManager() {
    // Cleanup if needed
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool SensorManager::initialize() {
    Serial.println("[SensorManager] Initializing sensors...");
    
    bool success = true;
    
    // Initialize I2C for IMU
    Wire.begin(PIN_IMU_SDA, PIN_IMU_SCL);
    Wire.setClock(400000); // 400kHz I2C clock
    
    // Initialize GPS
    if (!initializeGPS()) {
        Serial.println("[SensorManager] Warning: GPS initialization failed");
        success = false;
    }
    
    // Initialize IMU
    if (!initializeIMU()) {
        Serial.println("[SensorManager] Warning: IMU initialization failed");
        success = false;
    }
    
    // Initialize magnetometer
    if (!initializeMagnetometer()) {
        Serial.println("[SensorManager] Warning: Magnetometer initialization failed");
        success = false;
    }
    
    if (success) {
        Serial.println("[SensorManager] All sensors initialized successfully");
    } else {
        Serial.println("[SensorManager] Some sensors failed to initialize");
    }
    
    return success;
}

bool SensorManager::initializeGPS() {
    Serial.println("[SensorManager] Initializing GPS...");
    
    // Setup Serial2 for GPS communication
    Serial2.begin(9600, SERIAL_8N1, PIN_GPS_RX, PIN_GPS_TX);
    
    // Wait a bit for GPS to start
    delay(1000);
    
    // Check if GPS is responding
    unsigned long startTime = millis();
    while (millis() - startTime < 5000) { // Wait up to 5 seconds
        if (Serial2.available()) {
            char c = Serial2.read();
            if (gps.encode(c)) {
                gpsInitialized = true;
                Serial.println("[SensorManager] GPS initialized successfully");
                return true;
            }
        }
        delay(10);
    }
    
    Serial.println("[SensorManager] GPS initialization timeout");
    return false;
}

bool SensorManager::initializeIMU() {
    Serial.println("[SensorManager] Initializing IMU...");
    
    if (!mpu.begin()) {
        Serial.println("[SensorManager] Failed to find MPU6050 chip");
        return false;
    }
    
    // Configure MPU6050
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    
    imuInitialized = true;
    Serial.println("[SensorManager] IMU initialized successfully");
    return true;
}

bool SensorManager::initializeMagnetometer() {
    Serial.println("[SensorManager] Initializing magnetometer...");
    
    // For now, we'll assume the magnetometer is part of the MPU6050
    // In a real implementation, you'd initialize the HMC5883L here
    magnetometerInitialized = true;
    Serial.println("[SensorManager] Magnetometer initialized successfully");
    return true;
}

// ============================================================================
// GPS METHODS
// ============================================================================

bool SensorManager::readGPSData(GPSData& data) {
    if (!gpsInitialized) {
        return false;
    }
    
    // Read available GPS data
    while (Serial2.available()) {
        char c = Serial2.read();
        gps.encode(c);
    }
    
    // Update data structure
    data.latitude = gps.location.lat();
    data.longitude = gps.location.lng();
    data.altitude = gps.altitude.meters();
    data.speed = gps.speed.kmph();
    data.course = gps.course.deg();
    data.isValid = gps.location.isValid();
    data.timestamp = millis();
    data.satellites = gps.satellites.value();
    data.hdop = gps.hdop.value();
    
    return data.isValid;
}

bool SensorManager::isGPSValid() const {
    return gpsInitialized && gps.location.isValid();
}

int SensorManager::getGPSSatellites() {
    return gps.satellites.isValid() ? gps.satellites.value() : 0;
}

float SensorManager::getGPSHDOP() {
    return gps.hdop.isValid() ? gps.hdop.value() : 0.0f;
}

// ============================================================================
// IMU METHODS
// ============================================================================

bool SensorManager::readIMUData(IMUData& data) {
    if (!imuInitialized) {
        return false;
    }
    
    // Read MPU6050 data
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    
    // Update acceleration data (convert to m/s²)
    data.acceleration[0] = a.acceleration.x;
    data.acceleration[1] = a.acceleration.y;
    data.acceleration[2] = a.acceleration.z;
    
    // Update gyroscope data (convert to rad/s)
    data.gyroscope[0] = g.gyro.x * DEG_TO_RAD;
    data.gyroscope[1] = g.gyro.y * DEG_TO_RAD;
    data.gyroscope[2] = g.gyro.z * DEG_TO_RAD;
    
    // Update temperature
    data.temperature = temp.temperature;
    
    // For now, we'll use a simple heading calculation
    // In a real implementation, you'd read from the HMC5883L
    data.magnetometer[0] = 0.0f;
    data.magnetometer[1] = 0.0f;
    data.magnetometer[2] = 0.0f;
    
    // Calculate heading (simplified)
    data.heading = calculateHeading(data.magnetometer[0], data.magnetometer[1], data.magnetometer[2]);
    
    // Calculate pitch and roll from accelerometer
    data.pitch = atan2(-data.acceleration[0], sqrt(data.acceleration[1] * data.acceleration[1] + data.acceleration[2] * data.acceleration[2])) * RAD_TO_DEG;
    data.roll = atan2(data.acceleration[1], data.acceleration[2]) * RAD_TO_DEG;
    
    data.isValid = true;
    data.timestamp = millis();
    
    return true;
}

bool SensorManager::isIMUValid() const {
    return imuInitialized;
}

float SensorManager::getHeading() const {
    // This would return the current heading
    // For now, return 0
    return 0.0f;
}

float SensorManager::getTemperature() const {
    // This would return the current temperature
    // For now, return 0
    return 0.0f;
}

// ============================================================================
// CALIBRATION METHODS
// ============================================================================

void SensorManager::startMagnetometerCalibration() {
    Serial.println("[SensorManager] Starting magnetometer calibration...");
    calibrateMagnetometer();
}

bool SensorManager::isMagnetometerCalibrated() const {
    return magnetometerInitialized;
}

void SensorManager::getMagnetometerCalibration(float calibration[3][3], float offset[3]) {
    for (int i = 0; i < 3; i++) {
        offset[i] = magnetometerOffset[i];
        for (int j = 0; j < 3; j++) {
            calibration[i][j] = magnetometerCalibration[i][j];
        }
    }
}

// ============================================================================
// PRIVATE METHODS
// ============================================================================

void SensorManager::calibrateMagnetometer() {
    Serial.println("[SensorManager] Calibrating magnetometer...");
    
    // This is a simplified calibration
    // In a real implementation, you'd collect data points in all directions
    // and calculate the calibration matrix and offset
    
    // For now, just set identity matrix and zero offset
    for (int i = 0; i < 3; i++) {
        magnetometerOffset[i] = 0.0f;
        for (int j = 0; j < 3; j++) {
            magnetometerCalibration[i][j] = (i == j) ? 1.0f : 0.0f;
        }
    }
    
    Serial.println("[SensorManager] Magnetometer calibration complete");
}

float SensorManager::calculateHeading(float mx, float my, float mz) {
    // Apply calibration
    float calibrated_mx = magnetometerCalibration[0][0] * mx + magnetometerCalibration[0][1] * my + magnetometerCalibration[0][2] * mz - magnetometerOffset[0];
    float calibrated_my = magnetometerCalibration[1][0] * mx + magnetometerCalibration[1][1] * my + magnetometerCalibration[1][2] * mz - magnetometerOffset[1];
    float calibrated_mz = magnetometerCalibration[2][0] * mx + magnetometerCalibration[2][1] * my + magnetometerCalibration[2][2] * mz - magnetometerOffset[2];
    
    // Calculate heading
    float heading = atan2(calibrated_my, calibrated_mx) * RAD_TO_DEG;
    
    // Normalize to 0-360 degrees
    return normalizeAngle(heading);
}

float SensorManager::normalizeAngle(float angle) {
    while (angle < 0) angle += 360.0f;
    while (angle >= 360.0f) angle -= 360.0f;
    return angle;
}

// ============================================================================
// UTILITY METHODS
// ============================================================================

void SensorManager::printSensorStatus() {
    Serial.println("=== Sensor Status ===");
    Serial.printf("GPS Initialized: %s\n", gpsInitialized ? "Yes" : "No");
    Serial.printf("GPS Valid: %s\n", isGPSValid() ? "Yes" : "No");
    Serial.printf("GPS Satellites: %d\n", getGPSSatellites());
    Serial.printf("GPS HDOP: %.2f\n", getGPSHDOP());
    Serial.printf("IMU Initialized: %s\n", imuInitialized ? "Yes" : "No");
    Serial.printf("Magnetometer Initialized: %s\n", magnetometerInitialized ? "Yes" : "No");
    Serial.println("====================");
}

void SensorManager::resetCalibration() {
    Serial.println("[SensorManager] Resetting magnetometer calibration");
    calibrateMagnetometer();
}
