#ifndef TELEMETRY_TASK_H
#define TELEMETRY_TASK_H

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/semphr.h>
#include <ArduinoJson.h>
#include "core/SharedData.h"
#include "config/config.h"

// ============================================================================
// TELEMETRY TASK CLASS
// ============================================================================

class TelemetryTask {
private:
    // Telemetry state
    bool isActive;
    unsigned long lastTransmissionTime;
    unsigned long telemetryInterval;
    
    // JSON document for telemetry data (ArduinoJson v7)
    JsonDocument telemetryDoc;
    
    // Pre-allocated output buffer (avoids String heap allocation)
    char telemetryBuffer[1024];
    
    // Callback function for sending telemetry data
    std::function<void(const char*, size_t)> telemetryTransmitter;
    
    // Private methods
    void processTelemetry();
    void buildTelemetryData();
    void sendTelemetryData();
    void printTelemetryInfo();
    bool hasConnectedClients();
    
public:
    // Constructor
    TelemetryTask();
    
    // Destructor
    ~TelemetryTask();
    
    // Initialize telemetry system
    bool initialize();
    
    // Main telemetry loop
    void run();
    
    // Control methods
    bool startTelemetry();
    bool stopTelemetry();
    bool pauseTelemetry();
    bool resumeTelemetry();
    
    // Status methods
    bool isRunning();
    unsigned long getLastTransmissionTime();
    unsigned long getTelemetryInterval();
    
    // Configuration methods
    void setTelemetryInterval(unsigned long interval);
    void setTransmissionEnabled(bool enabled);
    
    // Set telemetry transmission callback
    void setTelemetryTransmitter(std::function<void(const char*, size_t)> transmitter);
    
    // Check if telemetry transmitter is available
    bool hasTelemetryTransmitter() const { return telemetryTransmitter != nullptr; }
};

// ============================================================================
// FREE RTOS TASK FUNCTION
// ============================================================================

void telemetryTaskFunction(void* parameter);

#endif // TELEMETRY_TASK_H
