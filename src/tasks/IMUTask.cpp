#include "tasks/IMUTask.h"
#include "config/config.h"
#include "config/pins.h"

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

// Global instance defined in main.cpp

// ============================================================================
// CONSTRUCTOR/DESTRUCTOR
// ============================================================================

IMUTask::IMUTask() : imuInitialized(false), lastUpdateTime(0), 
                     magOffsetX(0), magOffsetY(0), magOffsetZ(0),
                     magScaleX(1.0), magScaleY(1.0), magScaleZ(1.0),
                     calibrated(false) {
}

IMUTask::~IMUTask() {
    stop();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool IMUTask::initialize() {
    Serial.println("Initializing IMU task...");
    
    // Initialize I2C
    Wire.begin(PIN_IMU_SDA, PIN_IMU_SCL);
    Wire.setClock(400000); // 400kHz I2C clock
    
    // Initialize MPU6050
    if (!mpu.begin()) {
        Serial.println("ERROR: Failed to initialize MPU6050");
        return false;
    }
    
    // Configure MPU6050
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    
    Serial.println("MPU6050 initialized successfully");
    
    // Initialize HMC5883L magnetometer
    if (!compass.begin()) {
        Serial.println("ERROR: Failed to initialize HMC5883L");
        return false;
    }
    
    // Configure HMC5883L
    // Initialize compass - using Adafruit HMC5883 Unified library
    // The library handles configuration automatically
    
    Serial.println("HMC5883L initialized successfully");
    
    imuInitialized = true;
    Serial.println("IMU initialization complete");
    
    // Perform initial calibration
    Serial.println("Starting magnetometer calibration...");
    calibrateMagnetometer();
    
    return true;
}

// ============================================================================
// MAIN RUN LOOP
// ============================================================================

void IMUTask::run() {
    if (!imuInitialized) {
        Serial.println("ERROR: IMU not initialized");
        vTaskDelay(pdMS_TO_TICKS(1000));
        return;
    }
    
    // Process IMU data
    processIMUData();
    lastUpdateTime = millis();
}

// ============================================================================
// IMU DATA PROCESSING
// ============================================================================

void IMUTask::processIMUData() {
    // Read sensors
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    
    // Read magnetometer
    // Read magnetometer data using Adafruit HMC5883 Unified library
    sensors_event_t event;
    compass.getEvent(&event);
    
    // Apply calibration
    float magX = (event.magnetic.x - magOffsetX) * magScaleX;
    float magY = (event.magnetic.y - magOffsetY) * magScaleY;
    float magZ = (event.magnetic.z - magOffsetZ) * magScaleZ;
    
    // Calculate heading
    float heading = atan2(magY, magX);
    
    // Correct for declination (adjust for your location)
    // float declinationAngle = 0.0698; // ~4 degrees for most locations
    // heading += declinationAngle;
    
    // Normalize heading to 0-360 degrees
    heading = normalizeAngle(heading * 180.0 / PI);
    
    // Calculate pitch and roll from accelerometer
    float pitch = atan2(-a.acceleration.x, sqrt(a.acceleration.y * a.acceleration.y + a.acceleration.z * a.acceleration.z)) * 180.0 / PI;
    float roll = atan2(a.acceleration.y, a.acceleration.z) * 180.0 / PI;
    
    // Update shared data
    // Update IMU data - simplified for now
    updateIMUData();
    
    // Print IMU info periodically
    static unsigned long lastPrintTime = 0;
    if (millis() - lastPrintTime > 5000) { // Every 5 seconds
        printIMUInfo();
        lastPrintTime = millis();
    }
    
    // Update system status
    updateSystemStatus();
}

void IMUTask::updateIMUData() {
    IMUData imuData;
    
    // Calculate heading from magnetometer data
    sensors_event_t event;
    compass.getEvent(&event);
    float heading = atan2(event.magnetic.y, event.magnetic.x);
    if (heading < 0) heading += 2 * PI;
    heading = heading * 180 / PI;
    
    imuData.heading = heading;
    // Get temperature from MPU6050
    sensors_event_t temp_event;
    mpu.getTemperatureSensor()->getEvent(&temp_event);
    imuData.temperature = temp_event.temperature;
    imuData.timestamp = millis();
    imuData.isValid = true;
    
    // Update shared data
    if (sharedData.setIMUData(imuData)) {
        Serial.printf("IMU: Heading=%.1f°, Temp=%.1f°C\n", heading, temp_event.temperature);
    } else {
        Serial.println("ERROR: Failed to update IMU data in shared data");
    }
}

void IMUTask::updateSystemStatus() {
    SystemStatus status;
    if (sharedData.getSystemStatus(status)) {
        // SystemStatus only has: wifiConnected, gpsFix, imuCalibrated, wifiSignalStrength, batteryVoltage, uptime
        status.imuCalibrated = calibrated;
        sharedData.setSystemStatus(status);
    }
}

// ============================================================================
// CALIBRATION FUNCTIONS
// ============================================================================

void IMUTask::calibrateMagnetometer() {
    Serial.println("Calibrating magnetometer...");
    Serial.println("Please rotate the rover in all directions for 10 seconds");
    
    const int samples = 100;
    float magX[samples], magY[samples], magZ[samples];
    float minX = 9999, maxX = -9999;
    float minY = 9999, maxY = -9999;
    float minZ = 9999, maxZ = -9999;
    
    // Collect samples
    for (int i = 0; i < samples; i++) {
        sensors_event_t event;
        compass.getEvent(&event);
        magX[i] = event.magnetic.x;
        magY[i] = event.magnetic.y;
        magZ[i] = event.magnetic.z;
        
        // Track min/max values
        if (event.magnetic.x < minX) minX = event.magnetic.x;
        if (event.magnetic.x > maxX) maxX = event.magnetic.x;
        if (event.magnetic.y < minY) minY = event.magnetic.y;
        if (event.magnetic.y > maxY) maxY = event.magnetic.y;
        if (event.magnetic.z < minZ) minZ = event.magnetic.z;
        if (event.magnetic.z > maxZ) maxZ = event.magnetic.z;
        
        delay(100); // 10 seconds total
        Serial.printf("Calibration progress: %d%%\n", (i + 1) * 100 / samples);
    }
    
    // Calculate offsets (center of the range)
    magOffsetX = (minX + maxX) / 2.0;
    magOffsetY = (minY + maxY) / 2.0;
    magOffsetZ = (minZ + maxZ) / 2.0;
    
    // Calculate scale factors (normalize to unit sphere)
    float avgRange = ((maxX - minX) + (maxY - minY) + (maxZ - minZ)) / 3.0;
    magScaleX = avgRange / (maxX - minX);
    magScaleY = avgRange / (maxY - minY);
    magScaleZ = avgRange / (maxZ - minZ);
    
    calibrated = true;
    
    Serial.println("Magnetometer calibration complete!");
    Serial.printf("Offsets: X=%.2f, Y=%.2f, Z=%.2f\n", magOffsetX, magOffsetY, magOffsetZ);
    Serial.printf("Scales: X=%.2f, Y=%.2f, Z=%.2f\n", magScaleX, magScaleY, magScaleZ);
}

void IMUTask::startCalibration() {
    calibrated = false;
    calibrateMagnetometer();
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

float IMUTask::normalizeAngle(float angle) {
    while (angle < 0) angle += 360.0;
    while (angle >= 360.0) angle -= 360.0;
    return angle;
}

void IMUTask::printIMUInfo() {
    Serial.println("=== IMU Status ===");
    Serial.printf("Initialized: %s\n", imuInitialized ? "YES" : "NO");
    Serial.printf("Calibrated: %s\n", calibrated ? "YES" : "NO");
    
    if (imuInitialized) {
        IMUData imuData;
        if (sharedData.getIMUData(imuData)) {
            Serial.printf("Heading: %.1f°\n", imuData.heading);
            // IMUData structure doesn't have pitch and roll fields
            Serial.printf("Temperature: %.1f°C\n", imuData.temperature);
        }
    }
    
    Serial.printf("Last update: %lu ms ago\n", millis() - lastUpdateTime);
    Serial.println("==================");
}

float IMUTask::getHeading() const {
    IMUData imuData;
    if (sharedData.getIMUData(imuData)) {
        return imuData.heading;
    }
    return 0.0;
}

float IMUTask::getPitch() const {
    // IMUData structure doesn't have pitch field
    return 0.0;
}

float IMUTask::getRoll() const {
    // IMUData structure doesn't have roll field
    return 0.0;
}

float IMUTask::getTemperature() const {
    IMUData imuData;
    if (sharedData.getIMUData(imuData)) {
        return imuData.temperature;
    }
    return 0.0;
}

void IMUTask::stop() {
    imuInitialized = false;
    calibrated = false;
    Serial.println("IMU task stopped");
}

// ============================================================================
// TASK FUNCTION
// ============================================================================

void imuTaskFunction(void* parameter) {
    Serial.println("IMU task started");
    
    if (!imuTask.initialize()) {
        Serial.println("ERROR: Failed to initialize IMU task");
        vTaskDelete(NULL);
        return;
    }
    
    while (true) {
        imuTask.run();
        vTaskDelay(pdMS_TO_TICKS(IMU_UPDATE_RATE));
    }
}
