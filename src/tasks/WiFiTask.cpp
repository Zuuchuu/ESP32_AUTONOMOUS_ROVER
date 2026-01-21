#include "tasks/WiFiTask.h"
#include "tasks/NavigationTask.h"
#include "core/SharedData.h"
#include "config/config.h"
#include "config/wifi_config.h"

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

// Global instance defined in main.cpp
extern NavigationTask navigationTask;

// ============================================================================
// CONSTRUCTOR/DESTRUCTOR
// ============================================================================

WiFiTask::WiFiTask() : server(TCP_SERVER_PORT), clientConnected(false) {
}

WiFiTask::~WiFiTask() {
    stop();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool WiFiTask::initialize() {
    Serial.println("Initializing WiFi task...");
    
    // Start TCP server
    server.begin();
    Serial.printf("TCP server started on port %d\n", TCP_SERVER_PORT);
    
    return true;
}

// ============================================================================
// MAIN RUN LOOP
// ============================================================================

void WiFiTask::run() {
    // Check for new client connections
    WiFiClient newClient = server.available();
    if (newClient) {
        if (clientConnected) {
            // Disconnect existing client
            client.stop();
            clientConnected = false;
            Serial.println("Disconnected previous client");
        }
        
        // Accept new client
        client = newClient;
        clientConnected = true;
        
        // Enable TCP_NODELAY for low-latency transmission (disable Nagle's algorithm)
        client.setNoDelay(true);
        
        Serial.printf("New client connected: %s\n", getClientIP().c_str());
        
        // Send welcome message
        sendResponse("{\"status\":\"connected\",\"message\":\"Rover ready\"}");
    }
    
    // Handle client communication
    if (clientConnected && client.connected()) {
        if (client.available()) {
            String data = client.readStringUntil('\n');
            data.trim();
            
            if (data.length() > 0) {
                Serial.printf("Received: %s\n", data.c_str());
                processCommand(data);
            }
        }
    } else if (clientConnected) {
        // Client disconnected
        client.stop();
        clientConnected = false;
        Serial.println("Client disconnected");
    }
}

// ============================================================================
// COMMAND PROCESSING
// ============================================================================

void WiFiTask::processCommand(const String& command) {
    jsonDoc.clear();
    
    DeserializationError error = deserializeJson(jsonDoc, command);
    if (error) {
        sendError("Invalid JSON format");
        return;
    }
    
    // New mission-first protocol
    if (jsonDoc["command"].is<const char*>()) {
        String cmd = jsonDoc["command"].as<const char*>(); // e.g., upload_mission, start_mission, pause_mission, abort_mission, resume_mission

        // Upload mission - load waypoints but don't start navigation
        if (cmd == "upload_mission") {
            processUploadMission();
            return;
        }
        // Start mission - legacy command that uploads AND starts (for backward compatibility)
        if (cmd == "start_mission") {
            processStartMission();
            return;
        }
        if (cmd == "pause_mission") { processPauseMission(); return; }
        if (cmd == "abort_mission") { processAbortMission(); return; }
        if (cmd == "resume_mission") { processResumeMission(); return; }

        // Backward-compatible legacy controls
        if (cmd == "start") { processStartCommand(); return; }
        if (cmd == "stop") { processStopCommand(); return; }
        if (cmd == "set_speed") {
            if (jsonDoc["speed"].is<int>()) {
                int speed = jsonDoc["speed"].as<int>();
                processSpeedCommand(speed);
                return;
            }
            sendError("Speed value required");
            return;
        }
        if (cmd == "get_status") { sendStatus(); return; }

        // Manual control commands
        if (cmd == "enable_manual") { processEnableManual(); return; }
        if (cmd == "disable_manual") { processDisableManual(); return; }
        if (cmd == "manual_move") { processManualMove(); return; }

        sendError("Unknown command: " + cmd);
        return;
    }

    // Backward-compatible waypoint-only payload
    if (jsonDoc["waypoints"].is<JsonArray>()) {
        JsonArray waypoints = jsonDoc["waypoints"].as<JsonArray>();
        processWaypoints(waypoints);
        return;
    }

    sendError("No command specified");
}

void WiFiTask::processWaypoints(const JsonArray& waypoints) {
    Serial.printf("Processing %d waypoints\n", waypoints.size());
    
    // Clear existing waypoints
    sharedData.clearWaypoints();
    
    // Add new waypoints
    int count = 0;
    for (JsonObject waypoint : waypoints) {
        if (count >= MAX_WAYPOINTS) {
            sendError("Too many waypoints (max " + String(MAX_WAYPOINTS) + ")");
            break;
        }
        
        // Accept either {lat, lng} or {lat, lon}
        const bool hasLatLng = waypoint["lat"].is<double>() && waypoint["lng"].is<double>();
        const bool hasLatLon = waypoint["lat"].is<double>() && waypoint["lon"].is<double>();
        if (hasLatLng || hasLatLon) {
            double lat = waypoint["lat"].as<double>();
            double lng = hasLatLng ? waypoint["lng"].as<double>() : waypoint["lon"].as<double>();
            
            Waypoint wp;
            wp.latitude = lat;
            wp.longitude = lng;
            // Waypoint structure doesn't have an id field
            
            if (sharedData.addWaypoint(wp)) {
                count++;
                Serial.printf("Added waypoint %d: %.6f, %.6f\n", count, lat, lng);
            } else {
                sendError("Failed to add waypoint " + String(count));
                return;
            }
        } else {
            sendError("Invalid waypoint format (missing lat/lon)");
            return;
        }
    }
    
    // Send success response
    String response = "{\"status\":\"success\",\"message\":\"Added " + String(count) + " waypoints\"}";
    sendResponse(response);
}

// ========================= Mission protocol handlers =========================

void WiFiTask::processUploadMission() {
    // Expect mission payload fields: mission_id, waypoints[], parameters{}
    if (!(jsonDoc["mission_id"].is<const char*>() || jsonDoc["mission_id"].is<String>()) ||
        !jsonDoc["waypoints"].is<JsonArray>() ||
        !jsonDoc["parameters"].is<JsonObject>()) {
        sendError("Missing mission fields (mission_id, waypoints, parameters)");
        return;
    }

    // 1) Store mission id
    sharedData.setMissionId(jsonDoc["mission_id"].as<const char*>());

    // 2) Waypoints
    if (jsonDoc["waypoints"].is<JsonArray>()) {
        JsonArray waypoints = jsonDoc["waypoints"].as<JsonArray>();
        processWaypoints(waypoints);
    }

    // 3) Path segments (optional)
    if (jsonDoc["path_segments"].is<JsonArray>()) {
        JsonArray segments = jsonDoc["path_segments"].as<JsonArray>();
        const int maxSeg = min((int)segments.size(), MAX_WAYPOINTS - 1);
        PathSegment segBuf[MAX_WAYPOINTS - 1];
        int segCount = 0;
        for (int i = 0; i < maxSeg; i++) {
            JsonObject s = segments[i];
            PathSegment seg;
            seg.start_lat = s["start_lat"] | 0.0;
            seg.start_lon = s["start_lon"] | 0.0;
            seg.end_lat   = s["end_lat"]   | 0.0;
            seg.end_lon   = s["end_lon"]   | 0.0;
            seg.distance  = s["distance"]  | 0.0;
            seg.bearing   = s["bearing"]   | 0.0;
            seg.speed     = s["speed"]     | 1.0;
            segBuf[segCount++] = seg;
        }
        if (segCount > 0) {
            sharedData.setPathSegments(segBuf, segCount);
        }
    }

    // 4) Mission parameters
    JsonObject params = jsonDoc["parameters"].as<JsonObject>();
    MissionParameters mp;
    mp.speed_mps = params["speed_mps"] | 1.0;
    mp.cte_threshold_m = params["cte_threshold_m"] | 2.0;
    mp.mission_timeout_s = params["mission_timeout_s"] | 3600;
    mp.total_distance_m = params["total_distance_m"] | 0.0;
    mp.estimated_duration_s = params["estimated_duration_s"] | 0;
    sharedData.setMissionParameters(mp);

    // 5) Transition to PLANNED state (ready but not started)
    sharedData.setMissionState(MISSION_PLANNED);

    // NOTE: Do NOT start navigation here - wait for resume_mission command
    Serial.println("[WiFi] Mission uploaded and ready (PLANNED state)");
    sendResponse("{\"status\":\"success\",\"message\":\"Mission uploaded and ready\"}");
}

void WiFiTask::processStartMission() {
    // Expect mission payload fields: mission_id, waypoints[], path_segments[], parameters{}
    if (!(jsonDoc["mission_id"].is<const char*>() || jsonDoc["mission_id"].is<String>()) ||
        !jsonDoc["waypoints"].is<JsonArray>() ||
        !jsonDoc["parameters"].is<JsonObject>()) {
        sendError("Missing mission fields (mission_id, waypoints, parameters)");
        return;
    }

    // 1) Store mission id
    sharedData.setMissionId(jsonDoc["mission_id"].as<const char*>());

    // 2) Waypoints
    if (jsonDoc["waypoints"].is<JsonArray>()) {
        JsonArray waypoints = jsonDoc["waypoints"].as<JsonArray>();
        processWaypoints(waypoints);
    }

    // 3) Path segments (optional)
    if (jsonDoc["path_segments"].is<JsonArray>()) {
        JsonArray segments = jsonDoc["path_segments"].as<JsonArray>();
        const int maxSeg = min((int)segments.size(), MAX_WAYPOINTS - 1);
        PathSegment segBuf[MAX_WAYPOINTS - 1];
        int segCount = 0;
        for (int i = 0; i < maxSeg; i++) {
            JsonObject s = segments[i];
            PathSegment seg;
            seg.start_lat = s["start_lat"] | 0.0;
            seg.start_lon = s["start_lon"] | 0.0;
            seg.end_lat   = s["end_lat"]   | 0.0;
            seg.end_lon   = s["end_lon"]   | 0.0;
            seg.distance  = s["distance"]  | 0.0;
            seg.bearing   = s["bearing"]   | 0.0;
            seg.speed     = s["speed"]     | 1.0;
            segBuf[segCount++] = seg;
        }
        if (segCount > 0) {
            sharedData.setPathSegments(segBuf, segCount);
        }
    }

    // 4) Mission parameters
    JsonObject params = jsonDoc["parameters"].as<JsonObject>();
    MissionParameters mp;
    mp.speed_mps = params["speed_mps"] | 1.0;
    mp.cte_threshold_m = params["cte_threshold_m"] | 2.0;
    mp.mission_timeout_s = params["mission_timeout_s"] | 3600;
    mp.total_distance_m = params["total_distance_m"] | 0.0;
    mp.estimated_duration_s = params["estimated_duration_s"] | 0;
    sharedData.setMissionParameters(mp);

    // 5) Transition to PLANNED state
    sharedData.setMissionState(MISSION_PLANNED);

    // 6) Auto-start navigation (optional, can be changed to explicit start)
    navigationTask.startNavigation();

    sendResponse("{\"status\":\"success\",\"message\":\"Mission loaded and started\"}");
}

void WiFiTask::processPauseMission() {
    sharedData.setMissionState(MISSION_PAUSED);
    RoverState state;
    sharedData.getRoverState(state);
    state.isNavigating = false;
    sharedData.setRoverState(state);
    sendResponse("{\"status\":\"success\",\"message\":\"Mission paused\"}");
}

void WiFiTask::processAbortMission() {
    sharedData.setMissionState(MISSION_ABORTED);
    RoverState state;
    sharedData.getRoverState(state);
    state.isNavigating = false;
    sharedData.setRoverState(state);
    sendResponse("{\"status\":\"success\",\"message\":\"Mission aborted\"}");
}

void WiFiTask::processResumeMission() {
    sharedData.setMissionState(MISSION_ACTIVE);
    RoverState state;
    sharedData.getRoverState(state);
    state.isNavigating = true;
    sharedData.setRoverState(state);
    sendResponse("{\"status\":\"success\",\"message\":\"Mission resumed\"}");
}

void WiFiTask::processStartCommand() {
    Serial.println("Processing start command");
    
    RoverState state;
    if (sharedData.getRoverState(state)) {
        state.isNavigating = true;
        sharedData.setRoverState(state);
        sendResponse("{\"status\":\"success\",\"message\":\"Navigation started\"}");
    } else {
        sendError("Failed to update rover state");
    }
}

void WiFiTask::processStopCommand() {
    Serial.println("Processing stop command");
    
    RoverState state;
    if (sharedData.getRoverState(state)) {
        state.isNavigating = false;
        sharedData.setRoverState(state);
        sendResponse("{\"status\":\"success\",\"message\":\"Navigation stopped\"}");
    } else {
        sendError("Failed to update rover state");
    }
}

void WiFiTask::processSpeedCommand(int speed) {
    Serial.printf("Processing speed command: %d\n", speed);
    
    if (speed < 0 || speed > 100) {
        sendError("Speed must be between 0 and 100");
        return;
    }
    
    RoverState state;
    if (sharedData.getRoverState(state)) {
        state.currentSpeed = speed;
        sharedData.setRoverState(state);
        sendResponse("{\"status\":\"success\",\"message\":\"Speed set to " + String(speed) + "%\"}");
    } else {
        sendError("Failed to update rover state");
    }
}

// ============================================================================
// RESPONSE SENDING
// ============================================================================

void WiFiTask::sendResponse(const String& response) {
    if (clientConnected && client.connected()) {
        client.println(response);
        Serial.printf("Sent: %s\n", response.c_str());
    }
}

void WiFiTask::sendError(const String& error) {
    String response = "{\"status\":\"error\",\"message\":\"" + error + "\"}";
    sendResponse(response);
}

void WiFiTask::sendStatus() {
    // Get current status from shared data
    GPSPosition position;
    IMUData imuData;
    RoverState roverState;
    SystemStatus systemStatus;
    
    sharedData.getPosition(position);
    sharedData.getIMUData(imuData);
    sharedData.getRoverState(roverState);
    sharedData.getSystemStatus(systemStatus);
    
    // Create status JSON
    jsonDoc.clear();
    jsonDoc["status"] = "success";
    jsonDoc["data"]["position"]["lat"] = position.latitude;
    jsonDoc["data"]["position"]["lng"] = position.longitude;
    // GPSPosition doesn't have altitude field
    jsonDoc["data"]["heading"] = imuData.heading;
    jsonDoc["data"]["navigation_active"] = roverState.isNavigating;
    jsonDoc["data"]["target_speed"] = roverState.currentSpeed;
    jsonDoc["data"]["wifi_connected"] = systemStatus.wifiConnected;
    jsonDoc["data"]["wifi_signal"] = systemStatus.wifiSignalStrength;
    jsonDoc["data"]["uptime"] = systemStatus.uptime;
    
    String response;
    serializeJson(jsonDoc, response);
    sendResponse(response);
}

// ============================================================================
// MANUAL CONTROL COMMAND PROCESSING
// ============================================================================

void WiFiTask::processEnableManual() {
    Serial.println("[WiFi] Enabling manual control mode");
    
    // Update shared data
    if (sharedData.setManualControlState(true, false, "", 0)) {
        sendResponse("{\"status\":\"success\",\"message\":\"Manual control mode enabled\"}");
        Serial.println("[WiFi] Manual control mode enabled successfully");
    } else {
        sendError("Failed to enable manual control mode");
    }
}

void WiFiTask::processDisableManual() {
    Serial.println("[WiFi] Disabling manual control mode");
    
    // Update shared data
    if (sharedData.setManualControlState(false, false, "", 0)) {
        sendResponse("{\"status\":\"success\",\"message\":\"Manual control mode disabled\"}");
        Serial.println("[WiFi] Manual control mode disabled successfully");
    } else {
        sendError("Failed to disable manual control mode");
    }
}

void WiFiTask::processManualMove() {
    // Validate required fields
    if (!jsonDoc["direction"].is<const char*>() || !jsonDoc["speed"].is<int>()) {
        sendError("Missing direction or speed field");
        return;
    }
    
    String direction = jsonDoc["direction"].as<const char*>();
    int speed = jsonDoc["speed"].as<int>();
    
    // Validate direction
    if (direction != "forward" && direction != "backward" && 
        direction != "left" && direction != "right" && direction != "stop") {
        sendError("Invalid direction: " + direction);
        return;
    }
    
    // Validate speed (0-100 for percentage)
    if (speed < 0 || speed > 100) {
        sendError("Speed must be between 0 and 100");
        return;
    }
    
    Serial.printf("[WiFi] Manual move command: %s at speed %d\n", direction.c_str(), speed);
    
    // Update shared data with manual control state
    if (sharedData.setManualControlState(true, (direction != "stop"), direction.c_str(), speed)) {
        String response = "{\"status\":\"success\",\"message\":\"Manual move command executed: " + direction + " at speed " + String(speed) + "%\"}";
        sendResponse(response);
        Serial.println("[WiFi] Manual move command processed successfully");
    } else {
        sendError("Failed to process manual move command");
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

void WiFiTask::stop() {
    if (clientConnected) {
        client.stop();
        clientConnected = false;
    }
    server.close();
    Serial.println("WiFi task stopped");
}

String WiFiTask::getClientIP() const {
    if (clientConnected) {
        return client.remoteIP().toString();
    }
    return "None";
}

// ============================================================================
// TASK FUNCTION
// ============================================================================

void wifiTaskFunction(void* parameter) {
    Serial.println("WiFi task started");
    
    if (!wifiTask.initialize()) {
        Serial.println("ERROR: Failed to initialize WiFi task");
        vTaskDelete(NULL);
        return;
    }
    
    while (true) {
        wifiTask.run();
        vTaskDelay(pdMS_TO_TICKS(50)); // 20Hz - balanced between responsiveness and CPU usage
    }
}
