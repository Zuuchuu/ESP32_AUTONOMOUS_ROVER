#ifndef SHARED_DATA_H
#define SHARED_DATA_H

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include "config/config.h"

// ============================================================================
// DATA STRUCTURES
// ============================================================================

// GPS Position structure
struct GPSPosition {
    double latitude;
    double longitude;
    bool isValid;
    unsigned long timestamp;
    
    GPSPosition() : latitude(0.0), longitude(0.0), isValid(false), timestamp(0) {}
};

// BNO055 Calibration Status structure
struct BNO055CalibrationStatus {
    uint8_t system;          // System calibration status (0-3)
    uint8_t gyroscope;       // Gyroscope calibration status (0-3)
    uint8_t accelerometer;   // Accelerometer calibration status (0-3)
    uint8_t magnetometer;    // Magnetometer calibration status (0-3)
    
    BNO055CalibrationStatus() : system(0), gyroscope(0), accelerometer(0), magnetometer(0) {}
    
    bool isFullyCalibrated() const {
        return (system >= 3 && gyroscope >= 3 && accelerometer >= 3 && magnetometer >= 3);
    }
    
    bool isMagnetometerCalibrated() const {
        return magnetometer >= 3;
    }
};

// Enhanced IMU Data structure for BNO055
struct IMUData {
    // Orientation data (primary for rover navigation)
    float heading;           // Compass heading in degrees (0-360, 0=True North, clockwise)
    float roll;              // Roll angle in degrees (aviation convention)
    float pitch;             // Pitch angle in degrees (aviation convention)
    
    // Quaternion data (for advanced navigation)
    float quaternion[4];     // w, x, y, z quaternion components
    
    // Raw sensor data (for diagnostics and advanced processing)
    float acceleration[3];   // X, Y, Z linear acceleration (m/s²)
    float gyroscope[3];      // X, Y, Z angular velocity (rad/s)
    float magnetometer[3];   // X, Y, Z magnetic field (µT)
    
    // Additional BNO055 features
    float linearAccel[3];    // X, Y, Z linear acceleration (gravity removed)
    float gravity[3];        // X, Y, Z gravity vector
    
    // Status and metadata
    BNO055CalibrationStatus calibrationStatus;
    float temperature;       // Temperature in Celsius
    bool isValid;
    unsigned long timestamp;
    
    IMUData() : heading(0.0), roll(0.0), pitch(0.0), temperature(0.0), isValid(false), timestamp(0) {
        for (int i = 0; i < 3; i++) {
            acceleration[i] = 0.0;
            gyroscope[i] = 0.0;
            magnetometer[i] = 0.0;
            linearAccel[i] = 0.0;
            gravity[i] = 0.0;
        }
        for (int i = 0; i < 4; i++) {
            quaternion[i] = 0.0;
        }
        quaternion[0] = 1.0; // Default quaternion identity
    }
};

// Waypoint structure
struct Waypoint {
    double latitude;
    double longitude;
    bool isValid;
    
    Waypoint() : latitude(0.0), longitude(0.0), isValid(false) {}
    Waypoint(double lat, double lon) : latitude(lat), longitude(lon), isValid(true) {}
};

// Path segment structure for mission planning
struct PathSegment {
    double start_lat;
    double start_lon;
    double end_lat;
    double end_lon;
    double distance;     // meters
    double bearing;      // degrees
    double speed;        // m/s
    
    PathSegment() : start_lat(0.0), start_lon(0.0), end_lat(0.0), end_lon(0.0), 
                   distance(0.0), bearing(0.0), speed(1.0) {}
};

// Mission parameters structure
struct MissionParameters {
    double speed_mps;
    double cte_threshold_m;
    uint32_t mission_timeout_s;
    double total_distance_m;
    uint32_t estimated_duration_s;
    
    MissionParameters() : speed_mps(1.0), cte_threshold_m(2.0), mission_timeout_s(3600),
                         total_distance_m(0.0), estimated_duration_s(0) {}
};

// Mission state enumeration
enum MissionState {
    MISSION_IDLE,
    MISSION_PLANNED,
    MISSION_ACTIVE,
    MISSION_PAUSED,
    MISSION_COMPLETED,
    MISSION_ABORTED
};

// Rover State structure
struct RoverState {
    bool isNavigating;
    bool isConnected;
    int currentWaypointIndex;
    int totalWaypoints;
    float currentSpeed;
    unsigned long lastUpdateTime;
    
    // Enhanced mission tracking
    MissionState missionState;
    int currentSegmentIndex;
    int totalSegments;
    double missionProgress;          // 0.0 to 100.0
    double distanceToTarget;
    double totalDistance;
    double crossTrackError;
    unsigned long missionStartTime;
    unsigned long missionElapsedTime;
    double estimatedTimeRemaining;   // seconds
    
    // Hardware Telemetry
    float frontObstacleDistance;     // cm
    long leftEncoderCount;
    long rightEncoderCount;
    float leftMotorRPM;
    float rightMotorRPM;
    
    RoverState() : isNavigating(false), isConnected(false), 
                   currentWaypointIndex(0), totalWaypoints(0), 
                   currentSpeed(0.0), lastUpdateTime(0), missionState(MISSION_IDLE),
                   currentSegmentIndex(0), totalSegments(0), missionProgress(0.0),
                   distanceToTarget(0.0), totalDistance(0.0), crossTrackError(0.0),
                   missionStartTime(0), missionElapsedTime(0), estimatedTimeRemaining(0.0),
                   frontObstacleDistance(-1.0), leftEncoderCount(0), rightEncoderCount(0),
                   leftMotorRPM(0.0), rightMotorRPM(0.0) {}
};

// System Status structure
struct SystemStatus {
    bool wifiConnected;
    bool gpsFix;
    bool imuCalibrated;
    int wifiSignalStrength;
    float batteryVoltage;
    unsigned long uptime;
    
    SystemStatus() : wifiConnected(false), gpsFix(false), imuCalibrated(false),
                     wifiSignalStrength(0), batteryVoltage(0.0), uptime(0) {}
};

// ============================================================================
// SHARED DATA CLASS
// ============================================================================

class SharedData {
private:
    // Mutexes for thread-safe access
    SemaphoreHandle_t positionMutex;
    SemaphoreHandle_t imuMutex;
    SemaphoreHandle_t waypointsMutex;
    SemaphoreHandle_t stateMutex;
    SemaphoreHandle_t statusMutex;
    SemaphoreHandle_t missionMutex;
    SemaphoreHandle_t manualControlMutex;
    
    // Shared data structures
    GPSPosition currentPosition;
    IMUData currentIMUData;
    Waypoint waypoints[MAX_WAYPOINTS];
    RoverState roverState;
    SystemStatus systemStatus;
    
    // Manual control state
    bool manualModeActive;
    bool manualMoving;
    char manualDirection[20];  // "forward", "backward", "left", "right", "stop", "forward_right", etc.
    int manualSpeed;
    
    // Enhanced mission data
    PathSegment pathSegments[MAX_WAYPOINTS - 1];  // N-1 segments for N waypoints
    int segmentCount;
    MissionParameters missionParams;
    char missionId[36];  // Fixed-size mission ID (UUID format)

public:
    // Constructor
    SharedData();
    
    // Destructor
    ~SharedData();
    
    // Initialize mutexes
    bool initialize();
    
    // Position access methods
    bool getPosition(GPSPosition& position);
    bool setPosition(const GPSPosition& position);
    
    // IMU data access methods
    bool getIMUData(IMUData& imuData);
    bool setIMUData(const IMUData& imuData);
    
    // Waypoints access methods
    bool getWaypoint(int index, Waypoint& waypoint);
    bool setWaypoint(int index, const Waypoint& waypoint);
    bool clearWaypoints();
    int getWaypointCount();
    bool addWaypoint(const Waypoint& waypoint);
    
    // Rover state access methods
    bool getRoverState(RoverState& state);
    bool setRoverState(const RoverState& state);
    
    // System status access methods
    bool getSystemStatus(SystemStatus& status);
    bool setSystemStatus(const SystemStatus& status);
    
    // Mission data methods
    void setMissionParameters(const MissionParameters& params);
    MissionParameters getMissionParameters();
    
    // Manual control methods
    bool getManualControlState(bool& active, bool& moving, char* direction, size_t dirLen, int& speed);
    bool setManualControlState(bool active, bool moving, const char* direction, int speed);
    bool isManualModeActive();
    
    void setPathSegments(const PathSegment* segments, int count);
    int getPathSegmentCount();
    PathSegment getPathSegment(int index);
    
    void setMissionId(const char* id);
    const char* getMissionId();
    
    void setMissionState(MissionState state);
    MissionState getMissionState();
    
    void updateMissionProgress(double progress, int segmentIndex, double timeRemaining);
    
    // Utility methods
    bool isPositionValid();
    bool isIMUDataValid();
    bool hasWaypoints();
    
    // Debug methods
    void printStatus();
};

// ============================================================================
// GLOBAL SHARED DATA INSTANCE
// ============================================================================

extern SharedData sharedData;

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// Angle normalization utility
double normalizeAngle(double angle);

// Distance calculation utility (Haversine formula)
double calculateDistance(double lat1, double lon1, double lat2, double lon2);

// Bearing calculation utility
double calculateBearing(double lat1, double lon1, double lat2, double lon2);

#endif // SHARED_DATA_H
