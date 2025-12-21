/*
 * Wi-Fi Fallback Mode - Implementation
 */

#include "wifi_fallback.h"
#include "system_state.h"
#include "display.h"
#include "sensors.h"
#include "lora.h"
#include "secrets.h"

// ============================================================================
// WIFI CONFIGURATION
// ============================================================================

const uint32_t WIFI_RETRY_INTERVAL_MS = 10000;  // 10 seconds between retries
const uint32_t WIFI_CONNECTION_TIMEOUT_MS = 30000;  // 30 seconds to connect

// ============================================================================
// WIFI WEB SERVER
// ============================================================================

// Wi-Fi Fallback Web Server (only active in fallback mode)
WebServer wifiServer(80);

// ============================================================================
// WIFI HTTP STATUS ENDPOINT HANDLER
// ============================================================================

void handleWifiStatus() {
    String json = "{\n";
    json += "  \"uptime_seconds\": " + String(millis() / 1000) + ",\n";
    json += "  \"lora_joined\": " + String(joined ? "true" : "false") + ",\n";
    json += "  \"last_join_attempt\": " + String(lastJoinAttempt / 1000) + ",\n";
    json += "  \"join_attempts\": " + String(joinAttempts) + ",\n";
    json += "  \"consecutive_cycle_fails\": " + String(consecutiveCycleFails) + ",\n";
    json += "  \"tx_count\": " + String(txCount) + ",\n";
    json += "  \"sensors\": {\n";
    
    if (sensorData.mlx_valid) {
        json += "    \"sky_temp_c\": " + String(sensorData.sky_temperature, 2) + ",\n";
        json += "    \"ambient_temp_c\": " + String(sensorData.ambient_temperature, 2) + ",\n";
    } else {
        json += "    \"sky_temp_c\": null,\n";
        json += "    \"ambient_temp_c\": null,\n";
    }
    
    if (sensorData.tsl_valid) {
        json += "    \"sqm_lux\": " + String(sensorData.sqm_lux, 2) + ",\n";
        json += "    \"sqm_ir\": " + String(sensorData.sqm_ir) + ",\n";
        json += "    \"sqm_full\": " + String(sensorData.sqm_full) + ",\n";
    } else {
        json += "    \"sqm_lux\": null,\n";
        json += "    \"sqm_ir\": null,\n";
        json += "    \"sqm_full\": null,\n";
    }
    
    if (sensorData.rain_valid) {
        json += "    \"rain_intensity\": " + String(sensorData.rain_intensity) + ",\n";
    } else {
        json += "    \"rain_intensity\": null,\n";
    }
    
    if (sensorData.wind_valid) {
        json += "    \"wind_speed_ms\": " + String(sensorData.wind_speed, 2) + "\n";
    } else {
        json += "    \"wind_speed_ms\": null\n";
    }
    
    json += "  }\n";
    json += "}\n";
    
    wifiServer.send(200, "application/json", json);
}

// ============================================================================
// START WI-FI FALLBACK MODE
// ============================================================================

void wifiFallbackStart() {
    Serial.println("\n=== STARTING WI-FI FALLBACK MODE ===");
    
    // Set mode to switching
    currentMode = MODE_SWITCHING;
    displayUpdate("WI-FI FALLBACK", "Stopping LoRa...");
    
    // Stop LoRa cleanly if active
    if (joined) {
        Serial.println("[WIFI] Shutting down LoRa session...");
        // LMIC doesn't have explicit shutdown, but we can stop scheduling
        joined = false;
        transmitting = false;
    }
    
    // Stop LMIC scheduler
    stopLoRa();
    
    // Give LoRa time to settle
    delay(500);
    
    // Start Wi-Fi
    Serial.printf("[WIFI] Connecting to Wi-Fi: %s\n", WIFI_SSID);
    char connectMsg[32];
    snprintf(connectMsg, sizeof(connectMsg), "Connecting to %s", WIFI_SSID);
    displayUpdate("WI-FI FALLBACK", connectMsg);
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    wifiConnectionAttempt = millis();
    
    // Wait for connection (non-blocking in loop will handle timeout)
    uint32_t connectStart = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - connectStart < WIFI_CONNECTION_TIMEOUT_MS) {
        delay(500);
        Serial.print(".");
    }
    Serial.println();
    
    if (WiFi.status() == WL_CONNECTED) {
        wifiConnected = true;
        currentMode = MODE_WIFI_FALLBACK;
        
        Serial.printf("[WIFI] Connected to %s on %s\n", WIFI_SSID, WiFi.localIP().toString().c_str());
        
        // Start HTTP server
        wifiServer.on("/status", handleWifiStatus);
        wifiServer.begin();
        
        Serial.println("[WIFI] HTTP server started on port 80");
        Serial.println("[WIFI] Access /status endpoint for sensor data");
        
        // Update display with connection info
        char connectedMsg[32];
        snprintf(connectedMsg, sizeof(connectedMsg), "Connected to %s", WIFI_SSID);
        displayUpdate("WIFI FALLBACK",
                     connectedMsg,
                     WiFi.localIP().toString().c_str(),
                     "Hold 8s to exit");
        displayOn = true;  // Keep display on in Wi-Fi mode
    } else {
        Serial.println("[WIFI] Connection FAILED");
        displayUpdate("WIFI FAILED", "Check credentials", "Retrying LoRa...");
        wifiFallbackEnabled = false;
        currentMode = MODE_LORA_ACTIVE;
        delay(3000);
        
        // Restart LoRa
        LMIC_reset();
        LMIC_startJoining();
    }
}

// ============================================================================
// STOP WI-FI FALLBACK MODE
// ============================================================================

void wifiFallbackStop() {
    Serial.println("\n=== STOPPING WI-FI FALLBACK MODE ===");
    
    currentMode = MODE_SWITCHING;
    displayUpdate("SWITCHING", "Stopping Wi-Fi...");
    
    // Stop HTTP server
    wifiServer.stop();
    Serial.println("[WIFI] HTTP server stopped");
    
    // Disconnect Wi-Fi
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
    delay(500);
    
    wifiConnected = false;
    wifiFallbackEnabled = false;
    
    Serial.println("[WIFI] Wi-Fi stopped");
    
    // Restart LoRa
    currentMode = MODE_LORA_ACTIVE;
    displayUpdate("LORA MODE", "Restarting LoRa...");
    
    LMIC_reset();
    LMIC_startJoining();
    consecutiveCycleFails = 0;  // Reset failure counter
    
    Serial.println("[LORA] Resumed LoRa operation");
}

// ============================================================================
// WI-FI FALLBACK LOOP HANDLER
// ============================================================================

void wifiFallbackLoop() {
    if (currentMode == MODE_WIFI_FALLBACK && wifiConnected) {
        wifiServer.handleClient();
        
        // Check for connection loss
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("[WIFI] Connection lost, attempting reconnect...");
            wifiConnected = false;
            wifiFallbackStart();  // Try to reconnect
        }
    }
}
