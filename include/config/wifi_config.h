#ifndef WIFI_CONFIG_H
#define WIFI_CONFIG_H

// ============================================================================
// WIFI NETWORK CONFIGURATION
// ============================================================================

// WiFi Credentials - UPDATE THESE WITH YOUR NETWORK INFO
#define WIFI_SSID               "TRI AN"
#define WIFI_PASSWORD           "77779999"

// WiFi Connection Settings
#define WIFI_TIMEOUT_MS         100000   // Connection timeout
#define WIFI_RETRY_DELAY_MS     500     // Delay between retry attempts
#define WIFI_MAX_RETRIES        10       // Maximum connection attempts

// ============================================================================
// NETWORK MODE CONFIGURATION
// ============================================================================

// Set to true to enable Access Point mode (rover creates its own network)
#define ENABLE_ACCESS_POINT_MODE false

// Access Point Configuration (if enabled)
#define AP_SSID                 "ESP32_Rover_AP"
#define AP_PASSWORD             "rover12345"
#define AP_CHANNEL              1
#define AP_MAX_CONNECTIONS      1

// ============================================================================
// TCP SERVER CONFIGURATION
// ============================================================================

#define TCP_SERVER_PORT         80
#define TCP_MAX_CLIENTS         1
#define TCP_BUFFER_SIZE         1024
#define TCP_TIMEOUT_MS          5000

// ============================================================================
// NETWORK STATUS INDICATORS
// ============================================================================

// WiFi connection status
enum WiFiStatus {
    WIFI_DISCONNECTED = 0,
    WIFI_CONNECTING,
    WIFI_CONNECTED,
    WIFI_FAILED
};

// TCP server status
enum TCPServerStatus {
    TCP_SERVER_STOPPED = 0,
    TCP_SERVER_STARTING,
    TCP_SERVER_RUNNING,
    TCP_SERVER_ERROR
};

// ============================================================================
// NETWORK UTILITY MACROS
// ============================================================================

#define WIFI_IS_CONNECTED()     (WiFi.status() == WL_CONNECTED)
#define WIFI_GET_IP()           WiFi.localIP().toString()
#define WIFI_GET_RSSI()         WiFi.RSSI()

// ============================================================================
// SECURITY NOTES
// ============================================================================

/*
 * IMPORTANT SECURITY CONSIDERATIONS:
 * 
 * 1. Never commit real WiFi credentials to version control
 * 2. Consider using WiFiManager library for runtime configuration
 * 3. Use WPA2 or WPA3 encryption for production networks
 * 4. Consider implementing OTA updates for credential management
 * 
 * For development, you can use a dedicated test network
 * For production, implement secure credential storage
 */

#endif // WIFI_CONFIG_H
