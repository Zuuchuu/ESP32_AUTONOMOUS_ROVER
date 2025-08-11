#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include <Arduino.h>
#include <TinyGPSPlus.h>
#include <Adafruit_MPU6050.h>
#include <Wire.h>
#include "config/pins.h"

// ============================================================================
// SENSOR DATA STRUCTURES
// ============================================================================

struct GPSData {
    double latitude;
    double longitude;
    double altitude;
    double speed;
    double course;
    bool isValid;
    unsigned long timestamp;
    int satellites;
    float hdop;
};

struct IMUData {
    float acceleration[3];  // x, y, z in m/s²
    float gyroscope[3];     // x, y, z in rad/s
    float magnetometer[3];  // x, y, z in uT
    float temperature;      // in Celsius
    float heading;          // compass heading in degrees (0-360)
    float pitch;           // pitch angle in degrees
    float roll;            // roll angle in degrees
    bool isValid;
    unsigned long timestamp;
};

// ============================================================================
// SENSOR MANAGER CLASS
// ============================================================================

class SensorManager {
private:
    // Sensor instances
    TinyGPSPlus gps;
    Adafruit_MPU6050 mpu;
    
    // Sensor state
    bool gpsInitialized;
    bool imuInitialized;
    bool magnetometerInitialized;
    
    // Calibration data
    float magnetometerCalibration[3][3];  // Soft iron correction matrix
    float magnetometerOffset[3];          // Hard iron offset
    
    // Private methods
    bool initializeGPS();
    bool initializeIMU();
    bool initializeMagnetometer();
    void calibrateMagnetometer();
    float calculateHeading(float mx, float my, float mz);
    float normalizeAngle(float angle);
    
public:
    // Constructor
    SensorManager();
    
    // Destructor
    ~SensorManager();
    
    // Initialize all sensors
    bool initialize();
    
    // GPS methods
    bool readGPSData(GPSData& data);
    bool isGPSValid() const;
    int getGPSSatellites();
    float getGPSHDOP();
    
    // IMU methods
    bool readIMUData(IMUData& data);
    bool isIMUValid() const;
    float getHeading() const;
    float getTemperature() const;
    
    // Calibration methods
    void startMagnetometerCalibration();
    bool isMagnetometerCalibrated() const;
    void getMagnetometerCalibration(float calibration[3][3], float offset[3]);
    
    // Status methods
    bool isGPSInitialized() const { return gpsInitialized; }
    bool isIMUInitialized() const { return imuInitialized; }
    bool isMagnetometerInitialized() const { return magnetometerInitialized; }
    
    // Utility methods
    void printSensorStatus();
    void resetCalibration();
};

#endif // SENSOR_MANAGER_H
