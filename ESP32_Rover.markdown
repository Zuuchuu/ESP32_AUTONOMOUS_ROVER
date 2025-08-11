# ESP32 Autonomous Rover Development Instruction

## 1. Introduction
This guide provides a comprehensive development instruction for building an autonomous robot rover using the ESP32 30-pin DevKit, tailored for engineers with expertise in embedded systems and robotics. The rover integrates two N20 3.7V DC motors, a TB6612FNG motor driver, a GY-87 10-DOF IMU, and a u-blox M10 GPS module, controlled via a desktop application over WiFi describe in `ControlStationApp.md` guide. Waypoints are sent in JSON format, and the rover navigates autonomously using a PID controller with cross-track error (XTE) correction and Haversine distance calculations. The code uses the Arduino framework with FreeRTOS for real-time task management, ensuring modularity and thread safety. This instruction details hardware setup, software configuration, testing, and troubleshooting, optimized for clarity and practical implementation.

## 2. Hardware Setup

### 2.1 Components
- **ESP32 30-pin DevKit**: Main microcontroller.
- **N20 3.7V DC Motors (x2)**: For differential drive.
- **TB6612FNG Motor Driver**: Controls motor speed and direction.
- **GY-87 10-DOF IMU**: Provides heading via magnetometer and additional sensor data.
- **u-blox M10 GPS**: Supplies latitude and longitude.
- **Power Supply**: LiPo battery or adapter providing 3.7V for motors and 3.3V/5V for ESP32 and sensors.

### 2.2 Pin Connections
Connect the components to the ESP32 as follows:

| Component         | Interface | ESP32 Pins                     | Notes                            |
|-------------------|-----------|--------------------------------|----------------------------------|
| u-blox M10 GPS    | UART      | TX: GPIO17, RX: GPIO16         | Baud rate 9600                   |
| GY-87 IMU         | I2C       | SDA: GPIO21, SCL: GPIO22       | Uses HMC5883L for magnetometer   |
| TB6612FNG (Left)  | GPIO/PWM  | PWMA: GPIO12, AI1: GPIO27, AI2: GPIO14 | PWM channel 0, direction pins |
| TB6612FNG (Right) | GPIO/PWM  | PWMB: GPIO32, BI1: GPIO33, BI2: GPIO25 | PWM channel 1, direction pins |



## 3. Configure WiFi Credentials
Before uploading the code, configure your WiFi network:
1. Open the main sketch (`.ino` file).
2. Locate:
   ```cpp
   #define WIFI_SSID "YourNetwork"
   #define WIFI_PASSWORD "YourPassword"
   ```
3. Replace `"YourNetwork"` and `"YourPassword"` with your WiFi SSID and password.


## 4. Code Structure

### 4.1 Overview
The code is organized into FreeRTOS tasks for concurrent operation, ensuring real-time performance. Tasks handle WiFi communication, GPS data parsing, IMU heading calculation, and navigation with PID control. Shared data (position, heading, waypoints) is protected by mutexes for thread safety.

### 4.2 Files and Responsibilities
- **Main Sketch (e.g., `rover.ino`)**: Initializes components, creates tasks, and starts the FreeRTOS scheduler.
- **Shared Data**: Defined in the main sketch, including:
  - `struct { double lat; double lon; } current_position;`
  - `double current_heading;`
  - `struct Waypoint { double lat; double lon; }; Waypoint waypoints[10]; int num_waypoints;`
  - Mutexes: `SemaphoreHandle_t position_mutex, heading_mutex, waypoints_mutex;`
- **Tasks**:
  - **WiFi Task**: Connects to WiFi, runs a TCP server, and receives waypoints.
  - **GPS Task**: Parses GPS data for position updates.
  - **IMU Task**: Computes heading from magnetometer data.
  - **Navigation Task**: Calculates paths and controls motors using PID.

### 4.3 Task Breakdown

| Task           | Core | Priority | Stack | Description                        |
|----------------|------|----------|-------|------------------------------------|
| WiFi Task      | 0    | 1        | 8192  | Manage TCP server & data parsing   |
| GPS Task       | 0    | 2        | 4096  | Read GPS UART                      |
| IMU Task       | 0    | 2        | 4096  | Read HMC5883L magnetometer         |
| Navigation     | 1    | 3        | 8192  | Handle waypoint nav & motor drive  |
| Telemetry      | 1    | 1        | 4096  | Send telemetry to TCP client(s)    |


### 4.4 Configuration Parameters
Defined in the main sketch:
```cpp
#define WIFI_SSID "YourNetwork"
#define WIFI_PASSWORD "YourPassword"
#define SERVER_PORT 80
#define GPS_BAUD 9600
#define PWM_FREQ 5000
#define PWM_RESOLUTION 8
#define WAYPOINT_THRESHOLD 2.0 // meters
#define BASE_SPEED 100 // PWM 0-255
#define K_XTE 10.0 // degrees per meter
#define KP 0.5 // PID proportional gain
#define KI 0.1 // PID integral gain
#define KD 0.05 // PID derivative gain
#define EARTH_RADIUS 6371000 // meters
```

## 5. Task Implementations

### 5.1 WiFi Task
- **Purpose**: Connects to the WiFi network, runs a TCP server on port 80, and parses JSON waypoints from the control station app.
- **Workflow**:
  - Connect to the specified WiFi network.
  - Print the IP address to Serial Monitor (used by the control app).
  - Accept TCP connections, parse JSON waypoints, and update the shared waypoint list.
- **Code Example**:
```cpp
void wifiTask(void *pvParameters) {
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        vTaskDelay(pdMS_TO_TICKS(500));
    }
    Serial.println("WiFi connected");
    Serial.println(WiFi.localIP());
    WiFiServer server(SERVER_PORT);
    server.begin();
    while (true) {
        WiFiClient client = server.available();
        if (client) {
            String data = client.readStringUntil('\n');
            DynamicJsonDocument doc(1024);
            deserializeJson(doc, data);
            xSemaphoreTake(waypoints_mutex, portMAX_DELAY);
            num_waypoints = 0;
            for (JsonObject wp : doc.as<JsonArray>()) {
                if (num_waypoints < 10) {
                    waypoints[num_waypoints].lat = wp["lat"];
                    waypoints[num_num_waypoints].lon = wp["lon"];
                    num_waypoints++;
                }
            }
            xSemaphoreGive(waypoints_mutex);
            client.stop();
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
```

### 5.2 GPS Task
- **Purpose**: Reads GPS data via UART and updates the current position.
- **Workflow**:
  - Initialize Serial2 for GPS communication.
  - Parse NMEA sentences using TinyGPS++.
  - Update `current_position` with mutex protection, running every 1 second.
- **Code Example**:
```cpp
void gpsTask(void *pvParameters) {
    Serial2.begin(GPS_BAUD, SERIAL_8N1, 16, 17);
    TinyGPSPlus gps;
    while (true) {
        while (Serial2.available()) {
            gps.encode(Serial2.read());
        }
        if (gps.location.isUpdated()) {
            xSemaphoreTake(position_mutex, portMAX_DELAY);
            current_position.lat = gps.location.lat();
            current_position.lon = gps.location.lng();
            xSemaphoreGive(position_mutex);
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
```

### 5.3 IMU Task
- **Purpose**: Reads magnetometer data from the GY-87 to compute heading.
- **Workflow**:
  - Initialize I2C and HMC5883L sensor.
  - Calculate heading from magnetic field data.
  - Update `current_heading` with mutex protection, running every 100ms.
- **Code Example**:
```cpp
void imuTask(void *pvParameters) {
    Adafruit_HMC5883_Unified mag = Adafruit_HMC5883_Unified(12345);
    if (!mag.begin()) {
        Serial.println("IMU initialization failed");
        while (true) vTaskDelay(portMAX_DELAY);
    }
    while (true) {
        sensors_event_t event;
        mag.getEvent(&event);
        float heading = atan2(event.magnetic.y, event.magnetic.x) * 180 / PI;
        xSemaphoreTake(heading_mutex, portMAX_DELAY);
        current_heading = fmod(heading + 360, 360);
        xSemaphoreGive(heading_mutex);
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
```

### 5.4 Navigation Task
- **Purpose**: Calculates paths to waypoints, applies PID control with XTE correction, and sets motor speeds.
- **Workflow**:
  - Read current position and heading.
  - Calculate distance to the target waypoint using TinyGPS++’s Haversine-based `distanceBetween`.
  - If distance < threshold (2m), advance to the next waypoint.
  - Compute XTE as the perpendicular distance to the path.
  - Adjust desired heading: `desired_heading = bearing_to_waypoint - K_XTE * XTE`.
  - Use PID to minimize heading error and set motor speeds.
- **Key Calculations**:
  - **Distance**: `gps.distanceBetween(P_lat, P_lon, B_lat, B_lon)`.
  - **XTE**:
    - `bearing_AB = gps.courseTo(A_lat, A_lon, B_lat, B_lon)`.
    - `bearing_AP = gps.courseTo(A_lat, A_lon, P_lat, P_lon)`.
    - `distance_AP = gps.distanceBetween(A_lat, A_lon, P_lat, P_lon)`.
    - `delta = normalize_angle(bearing_AP - bearing_AB)`.
    - `XTE = distance_AP * sin(radians(delta))`.
  - **PID Input**: `heading_error = normalize_angle(desired_heading - current_heading)`.
- **Code Example**:
```cpp
double normalize_angle(double angle) {
    angle = fmod(angle, 360);
    if (angle > 180) angle -= 360;
    else if (angle <= -180) angle += 360;
    return angle;
}

void setMotorSpeeds(double left, double right) {
    left = constrain(left, 0, 255);
    right = constrain(right, 0, 255);
    digitalWrite(27, left > 0 ? HIGH : LOW);
    digitalWrite(14, left > 0 ? LOW : HIGH);
    ledcWrite(0, left);
    digitalWrite(33, right > 0 ? HIGH : LOW);
    digitalWrite(25, right > 0 ? LOW : HIGH);
    ledcWrite(1, right);
}

void navigationTask(void *pvParameters) {
    double A_lat, A_lon, B_lat, B_lon;
    int current_index = 0;
    bool first_segment = true;
    while (true) {
        xSemaphoreTake(position_mutex, portMAX_DELAY);
        double P_lat = current_position.lat;
        double P_lon = current_position.lon;
        xSemaphoreGive(position_mutex);
        xSemaphoreTake(heading_mutex, portMAX_DELAY);
        double H = current_heading;
        xSemaphoreGive(heading_mutex);
        xSemaphoreTake(waypoints_mutex, portMAX_DELAY);
        if (current_index < num_waypoints) {
            B_lat = waypoints[current_index].lat;
            B_lon = waypoints[current_index].lon;
            double distance = gps.distanceBetween(P_lat, P_lon, B_lat, B_lon);
            if (distance < WAYPOINT_THRESHOLD) {
                current_index++;
                if (current_index < num_waypoints) {
                    A_lat = P_lat;
                    A_lon = P_lon;
                    B_lat = waypoints[current_index].lat;
                    B_lon = waypoints[current_index].lon;
                    first_segment = false;
                } else {
                    setMotorSpeeds(0, 0);
                    xSemaphoreGive(waypoints_mutex);
                    continue;
                }
            }
            double XTE = 0;
            if (!first_segment) {
                double bearing_AB = gps.courseTo(A_lat, A_lon, B_lat, B_lon);
                double bearing_AP = gps.courseTo(A_lat, A_lon, P_lat, P_lon);
                double distance_AP = gps.distanceBetween(A_lat, A_lon, P_lat, P_lon);
                double delta = normalize_angle(bearing_AP - bearing_AB);
                XTE = distance_AP * sin(radians(delta));
            }
            double bearing_to_waypoint = gps.courseTo(P_lat, P_lon, B_lat, B_lon);
            double desired_heading = bearing_to_waypoint - K_XTE * XTE;
            desired_heading = fmod(desired_heading + 360, 360);
            double heading_error = normalize_angle(desired_heading - H);
            Input = heading_error;
            myPID.Compute();
            double steering = Output;
            double left_speed = BASE_SPEED - steering;
            double right_speed = BASE_SPEED + steering;
            setMotorSpeeds(left_speed, right_speed);
        } else {
            setMotorSpeeds(0, 0);
        }
        xSemaphoreGive(waypoints_mutex);
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
```

### 5.5 PID Tuning
- **Initial Values**: Start with `KP=0.5`, `KI=0.1`, `KD=0.05`, `K_XTE=10.0`.
- **Tuning Process**:
  - Increase `KP` for faster response to heading errors.
  - Adjust `KI` to eliminate steady-state error over time.
  - Use `KD` to reduce overshoot and oscillations.
  - Tune `K_XTE` to balance path correction with stability.
- **Testing**: Observe the rover’s path on a test course, adjusting parameters to minimize deviation.

## 6. Main Setup
The `setup()` function initializes components, mutexes, and tasks. The `loop()` function is empty as FreeRTOS tasks handle all operations.

- **Code Example**:
```cpp
#include <WiFi.h>
#include <WiFiServer.h>
#include <ArduinoJson.h>
#include <TinyGPS++.h>
#include <Adafruit_HMC5883_U.h>
#include <PID_v1.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

struct Waypoint { double lat; double lon; };
Waypoint waypoints[10];
int num_waypoints = 0;
struct { double lat; double lon; } current_position;
double current_heading;
SemaphoreHandle_t position_mutex, heading_mutex, waypoints_mutex;
double Input, Output, Setpoint = 0;
PID myPID(&Input, &Output, &Setpoint, KP, KI, KD, DIRECT);
TinyGPSPlus gps;

void setup() {
    Serial.begin(115200);
    position_mutex = xSemaphoreCreateMutex();
    heading_mutex = xSemaphoreCreateMutex();
    waypoints_mutex = xSemaphoreCreateMutex();
    myPID.SetMode(AUTOMATIC);
    myPID.SetOutputLimits(-255, 255);
    pinMode(27, OUTPUT);
    pinMode(14, OUTPUT);
    pinMode(33, OUTPUT);
    pinMode(25, OUTPUT);
    ledcSetup(0, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(12, 0);
    ledcSetup(1, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(32, 1);
    Wire.begin(21, 22);
    xTaskCreatePinnedToCore(wifiTask, "WiFi Task", 4096, NULL, 1, NULL, 0);
    xTaskCreatePinnedToCore(gpsTask, "GPS Task", 4096, NULL, 2, NULL, 0);
    xTaskCreatePinnedToCore(imuTask, "IMU Task", 4096, NULL, 2, NULL, 0);
    xTaskCreatePinnedToCore(navigationTask, "Navigation Task", 4096, NULL, 3, NULL, 0);
}

void loop() {
    // Empty, as FreeRTOS tasks handle all operations
}
```

## 6. Calibrating IMU
- Use the Adafruit HMC5883L calibration example to capture min/max magnetic field values.
- Rotate the rover in all directions to calibrate the magnetometer.
- Update the IMU task with calibration values for accurate heading.
- Verify heading changes correctly as the rover rotates.


## 7. Integration with Control Station App
- The rover’s IP address, printed to Serial Monitor after WiFi connection, is required for the control station app.
- Refer to the separate `ControlStationApp.md` guide for setting up the desktop application to send waypoints and monitor telemetry.

## 8. Troubleshooting
- **GPS Not Getting Fix**:
  - Ensure the antenna is outdoors with a clear sky view.
  - Verify UART connections (TX: GPIO17, RX: GPIO16).
  - Check Serial2 configuration in the code.
- **IMU Heading Incorrect**:
  - Recalibrate the magnetometer using the Adafruit calibration example.
  - Avoid magnetic interference from motors or metal objects.
- **Motors Not Moving**:
  - Verify pin connections and power supply (VM and VCC).
  - Test PWM signals with a multimeter or oscilloscope.
  - Ensure motor driver is properly powered.
- **WiFi Connection Fails**:
  - Double-check SSID and password in the code.
  - Ensure the network is within range and the ESP32 is in station mode.
  - Use Serial Monitor to debug connection issues.
- **Task Stack Overflow**:
  - If errors like “stack overflow” occur, increase the stack size in `xTaskCreatePinnedToCore` (e.g., from 4096 to 8192).
- **Debugging Tips**:
  - Add `Serial.println` statements to print GPS data, IMU readings, motor speeds, etc.
  - Use Serial Monitor at 115200 baud to monitor outputs.
  - Check for mutex-related errors if tasks fail to access shared data.

## 9. Debugging
- **Serial Output**: Insert `Serial.println` statements in tasks to log data like position, heading, or motor speeds.
- **Serial Monitor**: Open at 115200 baud to view debug output and the rover’s IP address.
- **Serial Plotter**: Use Arduino IDE’s Serial Plotter to visualize heading or motor speeds for tuning.
- **Task Monitoring**: If advanced debugging is needed, use FreeRTOS functions like `vTaskList` to check task statuses (requires additional code).

## 10. References
- [Arduino IDE](https://www.arduino.cc/en/software): Official download and installation guide.
- [ESP32 Arduino Core](https://github.com/espressif/arduino-esp32): ESP32 board support for Arduino.
- [TinyGPS++ Library](https://github.com/mikalhart/TinyGPSPlus): GPS data parsing and Haversine calculations.
- [Adafruit HMC5883 Unified Library](https://github.com/adafruit/Adafruit_HMC5883_Unified): Magnetometer support for heading.
- [Arduino PID Library](https://github.com/br3ttb/Arduino-PID-Library): PID controller implementation.
- [Random Nerd Tutorials: ESP32 GPS](https://randomnerdtutorials.com/esp32-gps-module-arduino/): Guide for GPS integration with ESP32.

## 11. Conclusion
This instruction provides a streamlined guide for developing and deploying your ESP32 autonomous rover. By following the steps for hardware setup, software configuration, code uploading, and testing, you can achieve reliable waypoint navigation. For integration with the control station app, ensure the rover’s IP address is noted and refer to the `ControlStationApp.md` guide.