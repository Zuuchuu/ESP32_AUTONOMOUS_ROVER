#ifndef IMU_TASK_H
#define IMU_TASK_H

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_HMC5883_U.h>
#include "core/SharedData.h"

// ============================================================================
// IMU TASK CLASS
// ============================================================================

class IMUTask {
private:
    Adafruit_MPU6050 mpu;
    Adafruit_HMC5883_Unified compass;
    bool imuInitialized;
    unsigned long lastUpdateTime;
    
    // Calibration data
    float magOffsetX, magOffsetY, magOffsetZ;
    float magScaleX, magScaleY, magScaleZ;
    bool calibrated;
    
    // IMU data processing
    void processIMUData();
    void updateIMUData();
    void updateSystemStatus();
    
    // Calibration functions
    void calibrateMagnetometer();
    void calculateHeading();
    
    // Utility functions
    void printIMUInfo();
    float normalizeAngle(float angle);

public:
    IMUTask();
    ~IMUTask();
    
    bool initialize();
    void run();
    void stop();
    
    // Status
    bool isInitialized() const { return imuInitialized; }
    bool getCalibrated() const { return calibrated; }
    unsigned long getLastUpdateTime() const { return lastUpdateTime; }
    
    // IMU data
    float getHeading() const;
    float getPitch() const;
    float getRoll() const;
    float getTemperature() const;
    
    // Calibration
    void startCalibration();
    bool isCalibrated() const { return calibrated; }
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
