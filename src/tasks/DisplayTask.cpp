#include "tasks/DisplayTask.h"
#include "config/wifi_config.h"
#include <WiFi.h>

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

// Global instance declared in main.cpp

// ============================================================================
// CONSTRUCTOR/DESTRUCTOR
// ============================================================================

DisplayTask::DisplayTask() 
    : display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET),
      isInitialized(false), 
      lastUpdateTime(0) {
}

DisplayTask::~DisplayTask() {
    stop();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool DisplayTask::initialize() {
    Serial.println("[Display] Initializing OLED display...");
    
    if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
        Serial.println("[Display] ERROR: SSD1306 allocation failed");
        return false;
    }

    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.display();
    
    isInitialized = true;
    Serial.println("[Display] Initialization successful");
    return true;
}

// ============================================================================
// MAIN RUN LOOP
// ============================================================================

void DisplayTask::run() {
    if (!isInitialized) return;

    unsigned long now = millis();
    if (now - lastUpdateTime < updateInterval) return;
    lastUpdateTime = now;

    // Fetch data from SharedData
    SystemStatus status;
    RoverState state;
    MissionState missionState;

    if (!sharedData.getSystemStatus(status) || 
        !sharedData.getRoverState(state)) {
        return;
    }
    missionState = sharedData.getMissionState();

    display.clearDisplay();
    
    drawHeader(status);
    drawMissionInfo(state, missionState, status);

    display.display();
}

// ============================================================================
// DISPLAY HELPERS
// ============================================================================

void DisplayTask::drawHeader(const SystemStatus& status) {
    display.setTextSize(1);
    display.setCursor(0, 0);
    
    // WiFi Status with IP:Port
    if (status.wifiConnected) {
        display.print(F("W:"));
        display.print(WiFi.localIP().toString());
        display.print(F(":"));
        display.print(TCP_SERVER_PORT);
    } else {
        display.print(F("W:Off"));
    }
    
    display.drawLine(0, 8, SCREEN_WIDTH, 8, SSD1306_WHITE);
}

void DisplayTask::drawMissionInfo(const RoverState& state, const MissionState& missionState, const SystemStatus& status) {
    display.setCursor(0, 10);
    
    // Mission State
    display.print(F("State: "));
    display.println(getMissionStateString(missionState));

    // IMU Calibration
    IMUData imu;
    sharedData.getIMUData(imu);
    display.print(F("IMU: "));
    display.print(imu.calibrationStatus.system);
    display.print(F(" "));
    display.print(imu.calibrationStatus.accelerometer);
    display.print(F(" "));
    display.print(imu.calibrationStatus.gyroscope);
    display.print(F(" "));
    display.println(imu.calibrationStatus.magnetometer);

    // GPS Status
    display.print(F("GPS Fix: "));
    display.println(status.gpsFix ? F("YES") : F("NO"));

    // Heading
    display.print(F("Heading: "));
    display.print(imu.heading, 0);
    display.println(F(" deg"));

    // Waypoints
    display.print(F("WP: "));
    display.print(state.currentWaypointIndex);
    display.print(F("/"));
    display.print(state.totalWaypoints);
    display.print(F(" Dist: "));
    display.println(state.distanceToTarget, 1);
}

String DisplayTask::getMissionStateString(MissionState state) {
    switch(state) {
        case MISSION_IDLE: return "IDLE";
        case MISSION_PLANNED: return "READY";
        case MISSION_ACTIVE: return "RUN";
        case MISSION_PAUSED: return "PAUSE";
        case MISSION_COMPLETED: return "DONE";
        case MISSION_ABORTED: return "ABORT";
        default: return "UNK";
    }
}

// ============================================================================
// PUBLIC METHODS
// ============================================================================

void DisplayTask::showSplash(const String& version) {
    if (!isInitialized) return;
    
    display.clearDisplay();
    display.setTextSize(2);
    display.setCursor(10, 10);
    display.println(F("ESP32"));
    display.setCursor(10, 30);
    display.println(F("ROVER"));
    display.setTextSize(1);
    display.setCursor(10, 50);
    display.print(F("v"));
    display.println(version);
    display.display();
}

void DisplayTask::showError(const String& msg) {
    if (!isInitialized) return;

    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println(F("ERROR:"));
    display.println(msg);
    display.display();
}

void DisplayTask::stop() {
    isInitialized = false;
    Serial.println("[Display] Task stopped");
}

// ============================================================================
// TASK FUNCTION
// ============================================================================

void displayTaskFunction(void* parameter) {
    Serial.println("[Display] Task started");
    
    if (!displayTask.initialize()) {
        Serial.println("[Display] ERROR: Failed to initialize task");
        vTaskDelete(NULL);
        return;
    }
    
    // Show splash on startup
    displayTask.showSplash("1.0");
    vTaskDelay(pdMS_TO_TICKS(2000));
    
    while(true) {
        displayTask.run();
        vTaskDelay(pdMS_TO_TICKS(DISPLAY_UPDATE_RATE));
    }
}
