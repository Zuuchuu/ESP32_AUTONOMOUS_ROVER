#ifndef IMU_TASK_H
#define IMU_TASK_H

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <Preferences.h>
#include "core/SharedData.h"

// ============================================================================
// BNO055 IMU TASK CLASS
// ============================================================================

class IMUTask {
private:
    Adafruit_BNO055 bno;
    Preferences preferences;
    bool imuInitialized;
    unsigned long lastUpdateTime;
    
    // Calibration management
    bool calibrationDataLoaded;
    bool calibrationInProgress;
    BNO055CalibrationStatus lastCalibrationStatus;
    unsigned long lastCalibrationSaveTime;
    
    // Configuration
    static constexpr float MAGNETIC_DECLINATION = -0.67f;  // Degrees for Ho Chi Minh City (-0° 40')
    static constexpr float HEADING_OFFSET = -90.0f;         // 90 degree East offset adjustment
    static const uint32_t CALIBRATION_SAVE_INTERVAL = 30000; // Save every 30 seconds when calibrated
    static const char* CALIBRATION_NAMESPACE;
    
    // Core IMU processing
    void processIMUData();
    void updateIMUData();
    void updateSystemStatus();
    
    // BNO055 configuration
    bool configureBNO055();
    bool setOperationMode();
    bool setUpdateRate();
    bool configureCoordinateSystem();
    
    // Calibration management
    void checkAndSaveCalibration();
    bool saveCalibrationData();
    bool loadCalibrationData();
    void resetCalibrationData();
    bool isCalibrationComplete() const;
    
    // Utility functions
    void printIMUInfo();
    void printCalibrationStatus();
    float normalizeHeading(float heading);
    void scanI2CDevices();
    
    // Data conversion helpers
    void quaternionToEuler(float qw, float qx, float qy, float qz, float& roll, float& pitch, float& yaw);
    float quaternionToHeading(float qw, float qx, float qy, float qz);

public:
    IMUTask();
    ~IMUTask();
    
    bool initialize();
    void run();
    void stop();
    
    // Status methods
    bool isInitialized() const { return imuInitialized; }
    bool isCalibrated() const;
    unsigned long getLastUpdateTime() const { return lastUpdateTime; }
    
    // Enhanced IMU data access (modern interface)
    float getHeading() const;
    float getPitch() const;
    float getRoll() const;
    float getTemperature() const;
    
    // Advanced data access
    bool getQuaternion(float& w, float& x, float& y, float& z) const;
    bool getEulerAngles(float& roll, float& pitch, float& yaw) const;
    bool getLinearAcceleration(float& x, float& y, float& z) const;
    bool getGravityVector(float& x, float& y, float& z) const;
    
    // Calibration control
    void startCalibration();
    BNO055CalibrationStatus getCalibrationStatus() const;
    bool isFullyCalibrated() const;
    void saveCurrentCalibration();
    void resetCalibration();
};

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

extern IMUTask imuTask;

// ============================================================================
// TASK FUNCTION
// ============================================================================

void imuTaskFunction(void* parameter);

#endif // IMU_TASK_H