#ifndef DISPLAY_TASK_H
#define DISPLAY_TASK_H

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>
#include "config/config.h"
#include "config/pins.h"
#include "core/SharedData.h"

// ============================================================================
// CONSTANTS
// ============================================================================

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C
#define DISPLAY_UPDATE_RATE 200 // 5Hz

// ============================================================================
// DISPLAY TASK CLASS
// ============================================================================

class DisplayTask {
private:
    Adafruit_SSD1306 display;
    bool isInitialized;
    unsigned long lastUpdateTime;
    static const unsigned long updateInterval = 500; // 500ms

    // Drawing helpers
    void drawHeader(const SystemStatus& status);
    void drawMissionInfo(const RoverState& state, const MissionState& missionState);
    String getMissionStateString(MissionState state);

public:
    DisplayTask();
    ~DisplayTask();
    
    // Lifecycle methods
    bool initialize();
    void run();
    void stop();
    
    // Display control
    void showSplash(const String& version);
    void showError(const String& msg);
    
    // Status
    bool isReady() const { return isInitialized; }
};

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

extern DisplayTask displayTask;

// ============================================================================
// TASK FUNCTION
// ============================================================================

void displayTaskFunction(void* parameter);

#endif // DISPLAY_TASK_H
