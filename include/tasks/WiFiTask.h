#ifndef WIFI_TASK_H
#define WIFI_TASK_H

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiServer.h>
#include <ArduinoJson.h>
#include "core/SharedData.h"

// ============================================================================
// WIFI TASK CLASS
// ============================================================================

class WiFiTask {
private:
    WiFiServer server;
    WiFiClient client;
    bool clientConnected;
    // JSON document for command parsing (ArduinoJson v7)
    JsonDocument jsonDoc;
    
    // Command processing
    void processCommand(const String& command);
    void processWaypoints(const JsonArray& waypoints);
    void processStartCommand();
    void processStopCommand();
    void processSpeedCommand(int speed);
    
    // Mission planning/execution commands (new protocol)
    void processStartMission();
    void processPauseMission();
    void processAbortMission();
    void processResumeMission();
    
    // Response sending
    void sendResponse(const String& response);
    void sendError(const String& error);
    void sendStatus();

public:
    WiFiTask();
    ~WiFiTask();
    
    bool initialize();
    void run();
    void stop();
    
    // Status
    bool isClientConnected() const { return clientConnected; }
    String getClientIP() const;

    // Allow other tasks (e.g., TelemetryTask) to stream data to client
    void sendRaw(const String& data) { if (clientConnected && client.connected()) client.println(data); }
};

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

extern WiFiTask wifiTask;

// ============================================================================
// TASK FUNCTION
// ============================================================================

void wifiTaskFunction(void* parameter);

#endif // WIFI_TASK_H
