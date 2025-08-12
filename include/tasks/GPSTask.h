#ifndef GPS_TASK_H
#define GPS_TASK_H

#include <Arduino.h>
#include <TinyGPSPlus.h>
#include "core/SharedData.h"

// ============================================================================
// GPS TASK CLASS
// ============================================================================

class GPSTask {
private:
    TinyGPSPlus gps;
    bool gpsInitialized;
    unsigned long lastUpdateTime;
    unsigned long lastFixTime;
    
    // GPS data processing
    void processGPSData();
    void updatePosition();
    void updateSystemStatus();
    
    // Utility functions
    bool isValidPosition(double lat, double lng);
    void printGPSInfo();

public:
    GPSTask();
    ~GPSTask();
    
    bool initialize();
    void run();
    void stop();
    
    // Status
    bool isInitialized() const { return gpsInitialized; }
    bool hasFix() const;
    unsigned long getLastFixTime() const { return lastFixTime; }
    unsigned long getLastUpdateTime() const { return lastUpdateTime; }
    
    // GPS info
    int getSatellites();
    float getHDOP();
    float getAltitude();
    float getSpeed();
};

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

extern GPSTask gpsTask;

// ============================================================================
// TASK FUNCTION
// ============================================================================

void gpsTaskFunction(void* parameter);

#endif // GPS_TASK_H
