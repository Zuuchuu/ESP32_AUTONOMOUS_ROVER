#include "core/SharedData.h"
#include <math.h>

// ============================================================================
// GLOBAL SHARED DATA INSTANCE
// ============================================================================

SharedData sharedData;

// ============================================================================
// SHARED DATA CLASS IMPLEMENTATION
// ============================================================================

SharedData::SharedData() {
    positionMutex = NULL;
    imuMutex = NULL;
    waypointsMutex = NULL;
    stateMutex = NULL;
    statusMutex = NULL;
    missionMutex = NULL;
    
    // Initialize mission data
    segmentCount = 0;
    missionId = "";
}

SharedData::~SharedData() {
    if (positionMutex) vSemaphoreDelete(positionMutex);
    if (imuMutex) vSemaphoreDelete(imuMutex);
    if (waypointsMutex) vSemaphoreDelete(waypointsMutex);
    if (stateMutex) vSemaphoreDelete(stateMutex);
    if (statusMutex) vSemaphoreDelete(statusMutex);
    if (missionMutex) vSemaphoreDelete(missionMutex);
}

bool SharedData::initialize() {
    // Create mutexes
    positionMutex = xSemaphoreCreateMutex();
    imuMutex = xSemaphoreCreateMutex();
    waypointsMutex = xSemaphoreCreateMutex();
    stateMutex = xSemaphoreCreateMutex();
    statusMutex = xSemaphoreCreateMutex();
    missionMutex = xSemaphoreCreateMutex();
    
    // Check if all mutexes were created successfully
    if (!positionMutex || !imuMutex || !waypointsMutex || !stateMutex || !statusMutex || !missionMutex) {
        Serial.println("ERROR: Failed to create mutexes");
        return false;
    }
    
    // Initialize waypoints array
    clearWaypoints();
    
    Serial.println("SharedData initialized successfully");
    return true;
}

// ============================================================================
// POSITION ACCESS METHODS
// ============================================================================

bool SharedData::getPosition(GPSPosition& position) {
    if (xSemaphoreTake(positionMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        position = currentPosition;
        xSemaphoreGive(positionMutex);
        return true;
    }
    return false;
}

bool SharedData::setPosition(const GPSPosition& position) {
    if (xSemaphoreTake(positionMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        currentPosition = position;
        xSemaphoreGive(positionMutex);
        return true;
    }
    return false;
}

// ============================================================================
// IMU DATA ACCESS METHODS
// ============================================================================

bool SharedData::getIMUData(IMUData& imuData) {
    if (xSemaphoreTake(imuMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        imuData = currentIMUData;
        xSemaphoreGive(imuMutex);
        return true;
    }
    return false;
}

bool SharedData::setIMUData(const IMUData& imuData) {
    if (xSemaphoreTake(imuMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        currentIMUData = imuData;
        xSemaphoreGive(imuMutex);
        return true;
    }
    return false;
}

// ============================================================================
// WAYPOINTS ACCESS METHODS
// ============================================================================

bool SharedData::getWaypoint(int index, Waypoint& waypoint) {
    if (index < 0 || index >= MAX_WAYPOINTS) return false;
    
    if (xSemaphoreTake(waypointsMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        waypoint = waypoints[index];
        xSemaphoreGive(waypointsMutex);
        return true;
    }
    return false;
}

bool SharedData::setWaypoint(int index, const Waypoint& waypoint) {
    if (index < 0 || index >= MAX_WAYPOINTS) return false;
    
    if (xSemaphoreTake(waypointsMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        waypoints[index] = waypoint;
        xSemaphoreGive(waypointsMutex);
        return true;
    }
    return false;
}

bool SharedData::clearWaypoints() {
    if (xSemaphoreTake(waypointsMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        for (int i = 0; i < MAX_WAYPOINTS; i++) {
            waypoints[i] = Waypoint();
        }
        xSemaphoreGive(waypointsMutex);
        return true;
    }
    return false;
}

int SharedData::getWaypointCount() {
    int count = 0;
    if (xSemaphoreTake(waypointsMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        for (int i = 0; i < MAX_WAYPOINTS; i++) {
            if (waypoints[i].isValid) count++;
        }
        xSemaphoreGive(waypointsMutex);
    }
    return count;
}

bool SharedData::addWaypoint(const Waypoint& waypoint) {
    if (xSemaphoreTake(waypointsMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        int count = getWaypointCount();
        if (count < MAX_WAYPOINTS) {
            waypoints[count] = waypoint;
            xSemaphoreGive(waypointsMutex);
            return true;
        }
        xSemaphoreGive(waypointsMutex);
    }
    return false;
}

// ============================================================================
// ROVER STATE ACCESS METHODS
// ============================================================================

bool SharedData::getRoverState(RoverState& state) {
    if (xSemaphoreTake(stateMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        state = roverState;
        xSemaphoreGive(stateMutex);
        return true;
    }
    return false;
}

bool SharedData::setRoverState(const RoverState& state) {
    if (xSemaphoreTake(stateMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        roverState = state;
        xSemaphoreGive(stateMutex);
        return true;
    }
    return false;
}

// ============================================================================
// SYSTEM STATUS ACCESS METHODS
// ============================================================================

bool SharedData::getSystemStatus(SystemStatus& status) {
    if (xSemaphoreTake(statusMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        status = systemStatus;
        xSemaphoreGive(statusMutex);
        return true;
    }
    return false;
}

bool SharedData::setSystemStatus(const SystemStatus& status) {
    if (xSemaphoreTake(statusMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        systemStatus = status;
        xSemaphoreGive(statusMutex);
        return true;
    }
    return false;
}

// ============================================================================
// UTILITY METHODS
// ============================================================================

bool SharedData::isPositionValid() {
    GPSPosition pos;
    if (getPosition(pos)) {
        return pos.isValid;
    }
    return false;
}

bool SharedData::isIMUDataValid() {
    IMUData imu;
    if (getIMUData(imu)) {
        return imu.isValid;
    }
    return false;
}

bool SharedData::hasWaypoints() {
    return getWaypointCount() > 0;
}

void SharedData::printStatus() {
    Serial.println("=== SHARED DATA STATUS ===");
    
    GPSPosition pos;
    if (getPosition(pos)) {
        Serial.printf("Position: %.6f, %.6f (Valid: %s)\n", 
                     pos.latitude, pos.longitude, pos.isValid ? "Yes" : "No");
    }
    
    IMUData imu;
    if (getIMUData(imu)) {
        Serial.printf("IMU Heading: %.2f° (Valid: %s)\n", 
                     imu.heading, imu.isValid ? "Yes" : "No");
    }
    
    Serial.printf("Waypoints: %d/%d\n", getWaypointCount(), MAX_WAYPOINTS);
    
    RoverState state;
    if (getRoverState(state)) {
        Serial.printf("Navigation: %s, Speed: %.1f%%\n", 
                     state.isNavigating ? "Active" : "Inactive", state.currentSpeed);
    }
    
    SystemStatus status;
    if (getSystemStatus(status)) {
        Serial.printf("WiFi: %s, GPS: %s, Uptime: %lu ms\n", 
                     status.wifiConnected ? "Connected" : "Disconnected",
                     status.gpsFix ? "Fix" : "No Fix",
                     status.uptime);
    }
    
    Serial.println("==========================");
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

double normalizeAngle(double angle) {
    angle = fmod(angle, 360.0);
    if (angle > 180.0) angle -= 360.0;
    else if (angle <= -180.0) angle += 360.0;
    return angle;
}

double calculateDistance(double lat1, double lon1, double lat2, double lon2) {
    const double R = EARTH_RADIUS; // Earth's radius in meters
    
    double lat1Rad = lat1 * M_PI / 180.0;
    double lat2Rad = lat2 * M_PI / 180.0;
    double deltaLat = (lat2 - lat1) * M_PI / 180.0;
    double deltaLon = (lon2 - lon1) * M_PI / 180.0;
    
    double a = sin(deltaLat / 2) * sin(deltaLat / 2) +
               cos(lat1Rad) * cos(lat2Rad) *
               sin(deltaLon / 2) * sin(deltaLon / 2);
    double c = 2 * atan2(sqrt(a), sqrt(1 - a));
    
    return R * c;
}

double calculateBearing(double lat1, double lon1, double lat2, double lon2) {
    double lat1Rad = lat1 * M_PI / 180.0;
    double lat2Rad = lat2 * M_PI / 180.0;
    double deltaLon = (lon2 - lon1) * M_PI / 180.0;
    
    double y = sin(deltaLon) * cos(lat2Rad);
    double x = cos(lat1Rad) * sin(lat2Rad) -
               sin(lat1Rad) * cos(lat2Rad) * cos(deltaLon);
    
    double bearing = atan2(y, x) * 180.0 / M_PI;
    return normalizeAngle(bearing);
}

// ============================================================================
// MISSION DATA METHODS IMPLEMENTATION
// ============================================================================

void SharedData::setMissionParameters(const MissionParameters& params) {
    if (xSemaphoreTake(missionMutex, portMAX_DELAY) == pdTRUE) {
        missionParams = params;
        xSemaphoreGive(missionMutex);
    }
}

MissionParameters SharedData::getMissionParameters() {
    MissionParameters params;
    if (xSemaphoreTake(missionMutex, portMAX_DELAY) == pdTRUE) {
        params = missionParams;
        xSemaphoreGive(missionMutex);
    }
    return params;
}

void SharedData::setPathSegments(const PathSegment* segments, int count) {
    if (xSemaphoreTake(missionMutex, portMAX_DELAY) == pdTRUE) {
        segmentCount = min(count, MAX_WAYPOINTS - 1);
        for (int i = 0; i < segmentCount; i++) {
            pathSegments[i] = segments[i];
        }
        xSemaphoreGive(missionMutex);
    }
}

int SharedData::getPathSegmentCount() {
    int count = 0;
    if (xSemaphoreTake(missionMutex, portMAX_DELAY) == pdTRUE) {
        count = segmentCount;
        xSemaphoreGive(missionMutex);
    }
    return count;
}

PathSegment SharedData::getPathSegment(int index) {
    PathSegment segment;
    if (index >= 0 && index < MAX_WAYPOINTS - 1) {
        if (xSemaphoreTake(missionMutex, portMAX_DELAY) == pdTRUE) {
            if (index < segmentCount) {
                segment = pathSegments[index];
            }
            xSemaphoreGive(missionMutex);
        }
    }
    return segment;
}

void SharedData::setMissionId(const String& id) {
    if (xSemaphoreTake(missionMutex, portMAX_DELAY) == pdTRUE) {
        missionId = id;
        xSemaphoreGive(missionMutex);
    }
}

String SharedData::getMissionId() {
    String id;
    if (xSemaphoreTake(missionMutex, portMAX_DELAY) == pdTRUE) {
        id = missionId;
        xSemaphoreGive(missionMutex);
    }
    return id;
}

void SharedData::setMissionState(MissionState state) {
    if (xSemaphoreTake(stateMutex, portMAX_DELAY) == pdTRUE) {
        roverState.missionState = state;
        xSemaphoreGive(stateMutex);
    }
}

MissionState SharedData::getMissionState() {
    MissionState state = MISSION_IDLE;
    if (xSemaphoreTake(stateMutex, portMAX_DELAY) == pdTRUE) {
        state = roverState.missionState;
        xSemaphoreGive(stateMutex);
    }
    return state;
}

void SharedData::updateMissionProgress(double progress, int segmentIndex, double timeRemaining) {
    if (xSemaphoreTake(stateMutex, portMAX_DELAY) == pdTRUE) {
        roverState.missionProgress = progress;
        roverState.currentSegmentIndex = segmentIndex;
        roverState.estimatedTimeRemaining = timeRemaining;
        roverState.missionElapsedTime = millis() - roverState.missionStartTime;
        xSemaphoreGive(stateMutex);
    }
}
