#include "tasks/IMUTask.h"
#include "config/config.h"
#include "config/pins.h"
#include <math.h>

// ============================================================================
// STATIC CONSTANTS
// ============================================================================

const char* IMUTask::CALIBRATION_NAMESPACE = "bno055_cal";

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

// Global instance defined in main.cpp

// ============================================================================
// CONSTRUCTOR/DESTRUCTOR
// ============================================================================

IMUTask::IMUTask() : bno(55, 0x28), imuInitialized(false), lastUpdateTime(0), 
                     calibrationDataLoaded(false), calibrationInProgress(false),
                     lastCalibrationSaveTime(0) {
}

IMUTask::~IMUTask() {
    stop();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool IMUTask::initialize() {
    Serial.println("Initializing BNO055 IMU task...");
    
    // Initialize I2C
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Wire.setClock(400000); // 400kHz for BNO055 (faster than GY-87)
    
    delay(100); // Allow I2C to stabilize
    
    // Scan I2C bus for diagnostics
    scanI2CDevices();
    
    // Initialize BNO055
    if (!bno.begin()) {
        Serial.println("ERROR: Failed to initialize BNO055");
        Serial.println("Check wiring and I2C address (0x28 or 0x29)");
        return false;
    }
    
    Serial.println("BNO055 detected successfully");
    
    // Configure BNO055 for rover navigation
    if (!configureBNO055()) {
        Serial.println("ERROR: Failed to configure BNO055");
        return false;
    }
    
    // Initialize ESP32 preferences for calibration storage
    if (!preferences.begin(CALIBRATION_NAMESPACE, false)) {
        Serial.println("ERROR: Failed to initialize calibration storage");
        return false;
    }
    
    Serial.println("Calibration storage initialized");
    
    // Load saved calibration data if available
    loadCalibrationData();
    
    imuInitialized = true;
    Serial.println("BNO055 IMU initialization complete");
    
    // Print initial status
    printIMUInfo();
    
    return true;
}

// ============================================================================
// BNO055 CONFIGURATION
// ============================================================================

bool IMUTask::configureBNO055() {
    Serial.println("Configuring BNO055 for rover navigation...");
    
    delay(1000); // BNO055 needs time after initialization
    
    // Set crystal use (for better accuracy)
    bno.setExtCrystalUse(true);
    delay(100);
    
    // Configure operation mode
    if (!setOperationMode()) {
        return false;
    }
    
    // Configure coordinate system for rover
    if (!configureCoordinateSystem()) {
        return false;
    }
    
    Serial.println("BNO055 configuration completed successfully");
    return true;
}

bool IMUTask::setOperationMode() {
    Serial.println("Setting BNO055 to NDOF mode...");
    
    // NDOF mode provides absolute orientation from all sensors
    // Best for rover navigation with smooth, stable readings
    bno.setMode(OPERATION_MODE_NDOF);
    delay(100); // Allow mode change to complete
    
    // Verify the mode was set correctly
    if (bno.getMode() != OPERATION_MODE_NDOF) {
        Serial.println("ERROR: Failed to set NDOF mode");
        return false;
    }
    
    Serial.println("BNO055 NDOF mode activated");
    return true;
}

bool IMUTask::setUpdateRate() {
    // BNO055 NDOF mode typically outputs at ~100Hz by default
    // No additional configuration needed for 100Hz
    Serial.println("BNO055 configured for 100Hz update rate");
    return true;
}

bool IMUTask::configureCoordinateSystem() {
    Serial.println("Configuring coordinate system for rover navigation...");
    
    // Configure for rover coordinate system:
    // X = Forward, Y = Left, Z = Up
    // Heading: 0° = North, increases clockwise
    // This matches standard rover navigation conventions
    
    // Set axis mapping (adjust based on your BNO055 mounting orientation)
    // These settings assume BNO055 is mounted horizontally with chip facing up
    // and the silkscreen arrow pointing forward (rover's front)
    
    // Remap for +X forward (north), +Y left (west, flipped to standard +Y east/right)
    bno.setAxisRemap(Adafruit_BNO055::REMAP_CONFIG_P3);
    bno.setAxisSign(Adafruit_BNO055::REMAP_SIGN_P3);
    delay(100); // Allow remap to take effect
    
    Serial.println("Coordinate system configured for rover navigation");
    return true;
}

// ============================================================================
// MAIN RUN LOOP
// ============================================================================

void IMUTask::run() {
    if (!imuInitialized) {
        Serial.println("ERROR: BNO055 not initialized");
        vTaskDelay(pdMS_TO_TICKS(1000));
        return;
    }
    
    // Process IMU data
    processIMUData();
    
    // Check and save calibration if needed
    checkAndSaveCalibration();
    
    lastUpdateTime = millis();
}

// ============================================================================
// IMU DATA PROCESSING
// ============================================================================

void IMUTask::processIMUData() {
    // Update IMU data in shared data structure
    updateIMUData();
    
    // Update system status
    updateSystemStatus();
    
    // Print status periodically (every 5 seconds)
    static unsigned long lastPrintTime = 0;
    if (millis() - lastPrintTime > 5000) {
        printIMUInfo();
        lastPrintTime = millis();
    }
}

void IMUTask::updateIMUData() {
    IMUData imuData;
    
    // Get BNO055 system status
    uint8_t system_status, self_test_result, system_error;
    bno.getSystemStatus(&system_status, &self_test_result, &system_error);
    
    // Get calibration status
    uint8_t sys, gyro, accel, mag = 0;
    bno.getCalibration(&sys, &gyro, &accel, &mag);
    
    imuData.calibrationStatus.system = sys;
    imuData.calibrationStatus.gyroscope = gyro;
    imuData.calibrationStatus.accelerometer = accel;
    imuData.calibrationStatus.magnetometer = mag;
    
    // Get Euler angles directly from library (replaces quaternion conversion)
    imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);
    imuData.heading = euler.x();  // Heading (yaw, 0° magnetic north)
    
    // Swap and Negate Pitch/Roll due to BNO055 mounting (X-Left, Y-Forward)
    // Based on user feedback:
    // Rover Up -> Pitch shown Down (Needs Negation)
    // Rover Tilt Left -> Roll shown Right (Needs Negation)
    // Sensor Z (Pitch) maps to Rover Roll
    // Sensor Y (Roll) maps to Rover Pitch
    imuData.roll = -euler.z();
    imuData.pitch = -euler.y();
    
    // Normalize heading to 0-360° with 0° = North, clockwise positive
    imuData.heading = normalizeHeading(imuData.heading);
    
    // Apply magnetic declination correction and fixed heading offset
    // HEADING_OFFSET compensates for sensor mounting angle relative to North
    imuData.heading = normalizeHeading(imuData.heading + HEADING_OFFSET + MAGNETIC_DECLINATION);
    
    // Get raw sensor data
    imu::Vector<3> accelerometer = bno.getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);
    imu::Vector<3> gyroscope = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
    imu::Vector<3> magnetometer = bno.getVector(Adafruit_BNO055::VECTOR_MAGNETOMETER);
    
    // Store raw data
    imuData.acceleration[0] = accelerometer.x();
    imuData.acceleration[1] = accelerometer.y();
    imuData.acceleration[2] = accelerometer.z();
    
    imuData.gyroscope[0] = gyroscope.x() * DEG_TO_RAD; // Convert to rad/s
    imuData.gyroscope[1] = gyroscope.y() * DEG_TO_RAD;
    imuData.gyroscope[2] = gyroscope.z() * DEG_TO_RAD;
    
    imuData.magnetometer[0] = magnetometer.x();
    imuData.magnetometer[1] = magnetometer.y();
    imuData.magnetometer[2] = magnetometer.z();
    
    // Get linear acceleration (gravity removed) and gravity vector
    imu::Vector<3> linearAccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
    imu::Vector<3> gravity = bno.getVector(Adafruit_BNO055::VECTOR_GRAVITY);
    
    imuData.linearAccel[0] = linearAccel.x();
    imuData.linearAccel[1] = linearAccel.y();
    imuData.linearAccel[2] = linearAccel.z();
    
    imuData.gravity[0] = gravity.x();
    imuData.gravity[1] = gravity.y();
    imuData.gravity[2] = gravity.z();
    
    // Get temperature
    int8_t temp = bno.getTemp();
    imuData.temperature = (float)temp;
    
    // Set metadata
    imuData.isValid = (system_status != 0 || sys > 0); // Valid if system is running or has some calibration
    imuData.timestamp = millis();
    
    // Update shared data
    if (sharedData.setIMUData(imuData)) {
        // Debug output for key values
        if (imuData.calibrationStatus.isFullyCalibrated()) {
            Serial.printf("IMU: Heading=%.1f°, Roll=%.1f°, Pitch=%.1f°, Temp=%.0f°C [CALIBRATED]\n", 
                         imuData.heading, imuData.roll, imuData.pitch, imuData.temperature);
        } else {
            Serial.printf("IMU: Heading=%.1f°, Cal: S=%d G=%d A=%d M=%d, Temp=%.0f°C\n", 
                         imuData.heading, sys, gyro, accel, mag, imuData.temperature);
        }
    } else {
        Serial.println("ERROR: Failed to update IMU data in shared data");
    }
}

void IMUTask::updateSystemStatus() {
    SystemStatus status;
    if (sharedData.getSystemStatus(status)) {
        status.imuCalibrated = isCalibrated();
        sharedData.setSystemStatus(status);
    }
}

// ============================================================================
// CALIBRATION MANAGEMENT
// ============================================================================

void IMUTask::checkAndSaveCalibration() {
    uint8_t sys, gyro, accel, mag = 0;
    bno.getCalibration(&sys, &gyro, &accel, &mag);
    
    BNO055CalibrationStatus currentStatus;
    currentStatus.system = sys;
    currentStatus.gyroscope = gyro;
    currentStatus.accelerometer = accel;
    currentStatus.magnetometer = mag;
    
    // Save calibration data periodically when fully calibrated
    if (currentStatus.isFullyCalibrated() && 
        (millis() - lastCalibrationSaveTime) > CALIBRATION_SAVE_INTERVAL) {
        
        if (!lastCalibrationStatus.isFullyCalibrated()) {
            Serial.println("BNO055 achieved full calibration! Saving calibration data...");
        }
        
        saveCalibrationData();
        lastCalibrationSaveTime = millis();
    }
    
    lastCalibrationStatus = currentStatus;
}

bool IMUTask::saveCalibrationData() {
    Serial.println("Saving BNO055 calibration data to NVS...");
    
    // Get calibration offsets from BNO055
    adafruit_bno055_offsets_t calibrationData;
    if (!bno.getSensorOffsets(calibrationData)) {
        Serial.println("ERROR: Failed to read calibration offsets from BNO055");
        return false;
    }
    
    // Save to ESP32 NVS
    preferences.putBytes("offsets", &calibrationData, sizeof(calibrationData));
    preferences.putULong("timestamp", millis());
    
    Serial.println("Calibration data saved successfully");
    Serial.printf("Accel: (%d, %d, %d) Gyro: (%d, %d, %d) Mag: (%d, %d, %d)\n",
                  calibrationData.accel_offset_x, calibrationData.accel_offset_y, calibrationData.accel_offset_z,
                  calibrationData.gyro_offset_x, calibrationData.gyro_offset_y, calibrationData.gyro_offset_z,
                  calibrationData.mag_offset_x, calibrationData.mag_offset_y, calibrationData.mag_offset_z);
    
    return true;
}

bool IMUTask::loadCalibrationData() {
    Serial.println("Loading BNO055 calibration data from NVS...");
    
    if (!preferences.isKey("offsets")) {
        Serial.println("No saved calibration data found");
        return false;
    }
    
    adafruit_bno055_offsets_t calibrationData;
    size_t dataSize = preferences.getBytesLength("offsets");
    
    if (dataSize != sizeof(calibrationData)) {
        Serial.println("WARNING: Calibration data size mismatch, ignoring saved data");
        return false;
    }
    
    preferences.getBytes("offsets", &calibrationData, sizeof(calibrationData));
    unsigned long saveTimestamp = preferences.getULong("timestamp", 0);
    
    // Apply calibration data to BNO055
    bno.setSensorOffsets(calibrationData);
    delay(100); // Allow time for offsets to be applied
    
    calibrationDataLoaded = true;
    
    Serial.println("Calibration data loaded and applied successfully");
    Serial.printf("Data saved %lu ms ago\n", millis() - saveTimestamp);
    Serial.printf("Accel: (%d, %d, %d) Gyro: (%d, %d, %d) Mag: (%d, %d, %d)\n",
                  calibrationData.accel_offset_x, calibrationData.accel_offset_y, calibrationData.accel_offset_z,
                  calibrationData.gyro_offset_x, calibrationData.gyro_offset_y, calibrationData.gyro_offset_z,
                  calibrationData.mag_offset_x, calibrationData.mag_offset_y, calibrationData.mag_offset_z);
    
    return true;
}

void IMUTask::resetCalibrationData() {
    Serial.println("Resetting BNO055 calibration data...");
    preferences.clear();
    calibrationDataLoaded = false;
    Serial.println("Calibration data reset complete");
}

// ============================================================================
// DATA CONVERSION HELPERS
// ============================================================================

void IMUTask::quaternionToEuler(float qw, float qx, float qy, float qz, float& roll, float& pitch, float& yaw) {
    // Convert quaternion to Euler angles (in degrees)
    // Roll (x-axis rotation)
    float sinr_cosp = 2 * (qw * qx + qy * qz);
    float cosr_cosp = 1 - 2 * (qx * qx + qy * qy);
    roll = atan2(sinr_cosp, cosr_cosp) * RAD_TO_DEG;
    
    // Pitch (y-axis rotation)
    float sinp = 2 * (qw * qy - qz * qx);
    if (abs(sinp) >= 1) {
        pitch = copysign(PI / 2, sinp) * RAD_TO_DEG; // Use 90 degrees if out of range
    } else {
        pitch = asin(sinp) * RAD_TO_DEG;
    }
    
    // Yaw (z-axis rotation) - this becomes our heading
    float siny_cosp = 2 * (qw * qz + qx * qy);
    float cosy_cosp = 1 - 2 * (qy * qy + qz * qz);
    yaw = atan2(siny_cosp, cosy_cosp) * RAD_TO_DEG;
}

float IMUTask::quaternionToHeading(float qw, float qx, float qy, float qz) {
    // Extract heading directly from quaternion
    float heading = atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz)) * RAD_TO_DEG;
    return normalizeHeading(heading);
}

float IMUTask::normalizeHeading(float heading) {
    // Convert to 0-360° range with 0° = North, clockwise positive
    while (heading < 0) heading += 360.0f;
    while (heading >= 360.0f) heading -= 360.0f;
    return heading;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

void IMUTask::scanI2CDevices() {
    Serial.println("Scanning I2C bus for devices...");
    int deviceCount = 0;
    
    for (int address = 1; address < 127; address++) {
        Wire.beginTransmission(address);
        int error = Wire.endTransmission();
        
        if (error == 0) {
            Serial.printf("I2C device found at address 0x%02X", address);
            deviceCount++;
            
            if (address == 0x28 || address == 0x29) {
                Serial.println(" (BNO055)");
            } else {
                Serial.println(" (Unknown)");
            }
        }
    }
    
    if (deviceCount == 0) {
        Serial.println("No I2C devices found");
    } else {
        Serial.printf("Found %d I2C device(s)\n", deviceCount);
    }
}

void IMUTask::printIMUInfo() {
    Serial.println("=== BNO055 IMU Status ===");
    Serial.printf("Initialized: %s\n", imuInitialized ? "YES" : "NO");
    
    if (imuInitialized) {
        IMUData imuData;
        if (sharedData.getIMUData(imuData)) {
            Serial.printf("Heading: %.1f° (True North, Clockwise)\n", imuData.heading);
            Serial.printf("Roll: %.1f°, Pitch: %.1f°\n", imuData.roll, imuData.pitch);
            Serial.printf("Temperature: %.0f°C\n", imuData.temperature);
            
            printCalibrationStatus();
        }
    }
    
    Serial.printf("Last update: %lu ms ago\n", millis() - lastUpdateTime);
    Serial.println("========================");
}

void IMUTask::printCalibrationStatus() {
    uint8_t sys, gyro, accel, mag = 0;
    bno.getCalibration(&sys, &gyro, &accel, &mag);
    
    Serial.printf("Calibration Status: System=%d, Gyro=%d, Accel=%d, Mag=%d\n", sys, gyro, accel, mag);
    
    if (sys >= 3 && gyro >= 3 && accel >= 3 && mag >= 3) {
        Serial.println("✓ FULLY CALIBRATED");
    } else {
        Serial.println("⚠ CALIBRATION IN PROGRESS");
        if (mag < 3) Serial.println("  → Move in figure-8 pattern to calibrate magnetometer");
        if (gyro < 3) Serial.println("  → Keep device still to calibrate gyroscope");
        if (accel < 3) Serial.println("  → Move device in various orientations to calibrate accelerometer");
    }
}

// ============================================================================
// PUBLIC INTERFACE METHODS
// ============================================================================

bool IMUTask::isCalibrated() const {
    uint8_t sys, gyro, accel, mag = 0;
    if (!imuInitialized) return false;
    
    // Cast away const for BNO055 library compatibility
    const_cast<Adafruit_BNO055&>(bno).getCalibration(&sys, &gyro, &accel, &mag);
    return (mag >= 3); // Magnetometer calibration is most critical for heading accuracy
}

bool IMUTask::isFullyCalibrated() const {
    uint8_t sys, gyro, accel, mag = 0;
    if (!imuInitialized) return false;
    
    // Cast away const for BNO055 library compatibility
    const_cast<Adafruit_BNO055&>(bno).getCalibration(&sys, &gyro, &accel, &mag);
    return (sys >= 3 && gyro >= 3 && accel >= 3 && mag >= 3);
}

float IMUTask::getHeading() const {
    IMUData imuData;
    if (sharedData.getIMUData(imuData)) {
        return imuData.heading;
    }
    return 0.0f;
}

float IMUTask::getPitch() const {
    IMUData imuData;
    if (sharedData.getIMUData(imuData)) {
        return imuData.pitch;
    }
    return 0.0f;
}

float IMUTask::getRoll() const {
    IMUData imuData;
    if (sharedData.getIMUData(imuData)) {
        return imuData.roll;
    }
    return 0.0f;
}

float IMUTask::getTemperature() const {
    IMUData imuData;
    if (sharedData.getIMUData(imuData)) {
        return imuData.temperature;
    }
    return 0.0f;
}

bool IMUTask::getQuaternion(float& w, float& x, float& y, float& z) const {
    IMUData imuData;
    if (sharedData.getIMUData(imuData)) {
        w = imuData.quaternion[0];
        x = imuData.quaternion[1];
        y = imuData.quaternion[2];
        z = imuData.quaternion[3];
        return true;
    }
    return false;
}

bool IMUTask::getEulerAngles(float& roll, float& pitch, float& yaw) const {
    IMUData imuData;
    if (sharedData.getIMUData(imuData)) {
        roll = imuData.roll;
        pitch = imuData.pitch;
        yaw = imuData.heading; // Heading is yaw in rover navigation
        return true;
    }
    return false;
}

BNO055CalibrationStatus IMUTask::getCalibrationStatus() const {
    IMUData imuData;
    if (sharedData.getIMUData(imuData)) {
        return imuData.calibrationStatus;
    }
    return BNO055CalibrationStatus();
}

void IMUTask::startCalibration() {
    Serial.println("Starting BNO055 calibration process...");
    calibrationInProgress = true;
    
    // Reset any existing calibration
    resetCalibrationData();
    
    Serial.println("Please perform calibration movements:");
    Serial.println("1. Magnetometer: Move rover in figure-8 patterns");
    Serial.println("2. Accelerometer: Move rover in various orientations");
    Serial.println("3. Gyroscope: Keep rover stationary for a few seconds");
    Serial.println("Watch calibration status - all values should reach 3 for full calibration");
}

void IMUTask::saveCurrentCalibration() {
    if (isFullyCalibrated()) {
        saveCalibrationData();
        Serial.println("Current calibration saved successfully");
    } else {
        Serial.println("Cannot save calibration - device not fully calibrated yet");
        printCalibrationStatus();
    }
}

void IMUTask::resetCalibration() {
    resetCalibrationData();
}

void IMUTask::stop() {
    imuInitialized = false;
    calibrationInProgress = false;
    preferences.end();
    Serial.println("BNO055 IMU task stopped");
}

// ============================================================================
// TASK FUNCTION
// ============================================================================

void imuTaskFunction(void* parameter) {
    Serial.println("BNO055 IMU task started");
    
    if (!imuTask.initialize()) {
        Serial.println("ERROR: Failed to initialize BNO055 IMU task");
        vTaskDelete(NULL);
        return;
    }
    
    // Reset calibration to clear NVS and force fresh offsets post-remap
    imuTask.resetCalibration();  // Call once here; comment out after first upload if persistent

    while (true) {
        imuTask.run();
        vTaskDelay(pdMS_TO_TICKS(IMU_UPDATE_RATE)); // 10ms for ~100Hz
    }
}