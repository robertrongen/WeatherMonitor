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
const uint32_t WIFI_CONNECTION_TIMEOUT_MS = 60000;  // 60 seconds to connect (increased)

// Wi-Fi connection state tracking
static bool wifiConnecting = false;
static uint32_t wifiConnectStartTime = 0;
static bool httpServerStarted = false;

// ============================================================================
// WIFI WEB SERVER
// ============================================================================

// Wi-Fi Fallback Web Server (only active in fallback mode)
WebServer wifiServer(80);

// ============================================================================
// WIFI HTTP STATUS ENDPOINT HANDLER
// ============================================================================

void handleWifiStatus() {
    // Pre-allocate String to reduce fragmentation
    String json;
    json.reserve(512);  // Reserve enough space for typical response
    
    json = "{\n";
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
    
    // Verify LMIC is not mid-operation before stopping
    if (LMIC.opmode & OP_TXRXPEND) {
        Serial.println("[WIFI] WARNING: LoRa operation in progress - waiting for completion");
        displayUpdate("SWITCHING", "Wait for LoRa...");
        // Don't force switch - let it complete naturally
        // This prevents corruption but may delay switch
        uint32_t waitStart = millis();
        while ((LMIC.opmode & OP_TXRXPEND) && millis() - waitStart < 5000) {
            os_runloop_once();  // Allow LMIC to complete
            delay(10);
        }
        if (LMIC.opmode & OP_TXRXPEND) {
            Serial.println("[WIFI] LoRa still busy after wait - forcing stop");
        }
    }
    
    // Stop LoRa cleanly if active
    if (joined) {
        Serial.println("[WIFI] Shutting down LoRa session...");
        joined = false;
        transmitting = false;
    }
    
    // Stop LMIC scheduler
    stopLoRa();
    
    // Start Wi-Fi connection (BLOCKING until success or timeout)
    Serial.printf("[WIFI] Connecting to Wi-Fi: %s\n", WIFI_SSID);
    char connectMsg[32];
    snprintf(connectMsg, sizeof(connectMsg), "Connecting to %s", WIFI_SSID);
    displayWake();
    displayUpdate("WI-FI FALLBACK", connectMsg, "Please wait...");
    displayTimeout = UINT32_MAX;  // Keep display on during connection
    
    // WiFi hardware diagnostic
    Serial.println("[WIFI] Running WiFi hardware diagnostics...");
    
    // Check WiFi mode
    Serial.printf("[WIFI] WiFi mode before init: %d\n", WiFi.getMode());
    
    // Initialize WiFi
    WiFi.mode(WIFI_OFF);
    delay(100);
    WiFi.mode(WIFI_STA);
    delay(100);
    
    Serial.printf("[WIFI] WiFi mode after init: %d\n", WiFi.getMode());
    Serial.printf("[WIFI] WiFi status: %d\n", WiFi.status());
    
    // Try multiple scan attempts
    Serial.println("[WIFI] Attempting network scan...");
    int n = WiFi.scanNetworks(true);  // async scan first
    
    // Wait for scan with timeout
    uint32_t scanStart = millis();
    while (WiFi.scanComplete() == -1 && millis() - scanStart < 5000) {
        delay(100);
    }
    
    n = WiFi.scanComplete();
    
    if (n == 0) {
        Serial.println("[WIFI] No networks found in first scan, trying again...");
        delay(2000);
        n = WiFi.scanNetworks();
        Serial.printf("[WIFI] Second scan result: %d networks\n", n);
    }
    
    Serial.printf("[WIFI] Found %d networks:\n", n);
    
    if (n == 0) {
        Serial.println("[WIFI] ERROR: No WiFi networks detected!");
        Serial.println("[WIFI] Possible causes:");
        Serial.println("  - WiFi hardware not initialized");
        Serial.println("  - WiFi antenna disconnected");
        Serial.println("  - Hardware fault");
        Serial.println("  - Interference");
        
        displayUpdate("WIFI ERROR", "No networks found!", "Hardware issue?");
        delay(5000);
        wifiFallbackEnabled = false;
        currentMode = MODE_LORA_ACTIVE;
        return;
    }
    
    bool targetFound = false;
    for (int i = 0; i < n; i++) {
        Serial.printf("  %d: %s (RSSI: %d dBm, Ch: %d, Enc: %s)\n",
                     i + 1,
                     WiFi.SSID(i).c_str(),
                     WiFi.RSSI(i),
                     WiFi.channel(i),
                     WiFi.encryptionType(i) == WIFI_AUTH_OPEN ? "Open" : "Encrypted");
        
        if (WiFi.SSID(i) == String(WIFI_SSID)) {
            targetFound = true;
            Serial.printf("  ^^^ Target SSID '%s' found! RSSI: %d dBm\n", WIFI_SSID, WiFi.RSSI(i));
        }
    }
    
    if (!targetFound) {
        Serial.printf("[WIFI] WARNING: Target SSID '%s' NOT found in scan!\n", WIFI_SSID);
        displayUpdate("WIFI ERROR", "SSID not found!", "Check network");
        delay(3000);
        wifiFallbackEnabled = false;
        currentMode = MODE_LORA_ACTIVE;
        LMIC_reset();
        delay(100);
        LMIC_setLinkCheckMode(0);
        LMIC.dn2Dr = DR_SF9;
        LMIC_setDrTxpow(DR_SF7, 14);
        LMIC_startJoining();
        return;
    }
    
    Serial.println("[WIFI] Starting connection...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    // Give WiFi stack time to scan and prepare
    Serial.println("[WIFI] Waiting for WiFi stack to initialize...");
    delay(2000);  // 2 second wait for scan
    
    // Blocking wait for connection with periodic status updates
    uint32_t startTime = millis();
    uint32_t lastStatusUpdate = 0;
    
    while (WiFi.status() != WL_CONNECTED && millis() - startTime < WIFI_CONNECTION_TIMEOUT_MS) {
        delay(200);  // Give WiFi stack more time to process (increased from 100ms)
        
        // Update status every 2 seconds
        if (millis() - lastStatusUpdate > 2000) {
            wl_status_t status = WiFi.status();
            uint32_t elapsed = (millis() - startTime) / 1000;
            char elapsedStr[16];
            snprintf(elapsedStr, sizeof(elapsedStr), "%lu s elapsed", elapsed);
            
            Serial.printf("[WIFI] Connection attempt: %lu seconds elapsed\n", elapsed);
            Serial.printf("[WIFI] WiFi.status() = %d: ", status);
            
            switch (status) {
                case WL_IDLE_STATUS:
                    Serial.println("WL_IDLE_STATUS");
                    displayUpdate("WI-FI FALLBACK", "Idle...", elapsedStr);
                    break;
                case WL_NO_SSID_AVAIL:
                    Serial.println("WL_NO_SSID_AVAIL - SSID not found!");
                    displayUpdate("WIFI ERROR", "SSID not found!", "Check credentials");
                    break;
                case WL_SCAN_COMPLETED:
                    Serial.println("WL_SCAN_COMPLETED");
                    displayUpdate("WI-FI FALLBACK", "Scan complete...", elapsedStr);
                    break;
                case WL_CONNECTED:
                    Serial.println("WL_CONNECTED");
                    break;
                case WL_CONNECT_FAILED:
                    Serial.println("WL_CONNECT_FAILED - Wrong password or auth failure!");
                    displayUpdate("WIFI ERROR", "Connect failed!", "Check password");
                    break;
                case WL_CONNECTION_LOST:
                    Serial.println("WL_CONNECTION_LOST");
                    displayUpdate("WIFI ERROR", "Connection lost!", "Retrying...");
                    break;
                case WL_DISCONNECTED:
                    Serial.println("WL_DISCONNECTED");
                    displayUpdate("WI-FI FALLBACK", "Connecting...", elapsedStr);
                    break;
                default:
                    Serial.printf("Unknown status: %d\n", status);
                    displayUpdate("WI-FI FALLBACK", "Connecting...", elapsedStr);
                    break;
            }
            
            // Print WiFi diagnostic info
            Serial.printf("[WIFI] SSID: %s\n", WIFI_SSID);
            Serial.printf("[WIFI] MAC: %s\n", WiFi.macAddress().c_str());
            Serial.printf("[WIFI] RSSI: %d dBm\n", WiFi.RSSI());
            
            lastStatusUpdate = millis();
        }
    }
    
    // Check final result
    if (WiFi.status() == WL_CONNECTED) {
        wifiConnected = true;
        wifiConnecting = false;
        currentMode = MODE_WIFI_FALLBACK;
        
        Serial.printf("[WIFI] Connected to %s on %s\n", WIFI_SSID, WiFi.localIP().toString().c_str());
        
        // Start HTTP server
        if (!httpServerStarted) {
            wifiServer.on("/status", handleWifiStatus);
            wifiServer.begin();
            httpServerStarted = true;
            
            Serial.println("[WIFI] HTTP server started on port 80");
            Serial.println("[WIFI] Access /status endpoint for sensor data");
        }
        
        // Update display with connection info
        char connectedMsg[32];
        snprintf(connectedMsg, sizeof(connectedMsg), "Connected to %s", WIFI_SSID);
        displayWake();
        displayUpdate("WIFI FALLBACK",
                     connectedMsg,
                     WiFi.localIP().toString().c_str(),
                     "Hold 8s to exit");
        displayTimeout = UINT32_MAX;  // Keep display on indefinitely
    } else {
        Serial.println("[WIFI] Connection FAILED after timeout");
        Serial.printf("[WIFI] Final status: %d\n", WiFi.status());
        wifiConnecting = false;
        
        displayUpdate("WIFI FAILED", "Timeout after 30s", "Check credentials");
        wifiFallbackEnabled = false;
        currentMode = MODE_LORA_ACTIVE;
        delay(5000);  // Show error longer
        
        // Restart LoRa
        LMIC_reset();
        delay(100);
        LMIC_setLinkCheckMode(0);
        LMIC.dn2Dr = DR_SF9;
        LMIC_setDrTxpow(DR_SF7, 14);
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
    if (httpServerStarted) {
        wifiServer.stop();
        httpServerStarted = false;
        Serial.println("[WIFI] HTTP server stopped");
    }
    
    // Disconnect Wi-Fi
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
    
    wifiConnected = false;
    wifiFallbackEnabled = false;
    wifiConnecting = false;
    
    Serial.println("[WIFI] Wi-Fi stopped");
    
    // Restart LoRa (with verification delay)
    currentMode = MODE_LORA_ACTIVE;
    displayUpdate("LORA MODE", "Restarting LoRa...");
    
    delay(200);  // Brief settle time for Wi-Fi shutdown
    
    LMIC_reset();
    delay(100);  // Allow reset to complete
    
    LMIC_setLinkCheckMode(0);
    LMIC.dn2Dr = DR_SF9;
    LMIC_setDrTxpow(DR_SF7, 14);
    LMIC_startJoining();
    consecutiveCycleFails = 0;  // Reset failure counter
    
    Serial.println("[LORA] Resumed LoRa operation");
}

// ============================================================================
// WI-FI FALLBACK LOOP HANDLER
// ============================================================================

void wifiFallbackLoop() {
    // Handle HTTP requests when connected
    if (currentMode == MODE_WIFI_FALLBACK && wifiConnected) {
        wifiServer.handleClient();
        
        // Check for connection loss and reconnect
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("[WIFI] Connection lost, attempting reconnect...");
            wifiConnected = false;
            httpServerStarted = false;
            
            // Reconnect with blocking call
            displayWake();
            displayUpdate("WIFI FALLBACK", "Reconnecting...", "Please wait...");
            displayTimeout = UINT32_MAX;
            
            uint32_t startTime = millis();
            while (WiFi.status() != WL_CONNECTED && millis() - startTime < WIFI_CONNECTION_TIMEOUT_MS) {
                delay(300);  // Give WiFi stack more time (increased from 500ms)
                if (millis() - startTime > 5000 && millis() - startTime < 5100) {
                    Serial.printf("[WIFI] Reconnect status: %d\n", WiFi.status());
                }
            }
            
            if (WiFi.status() == WL_CONNECTED) {
                Serial.println("[WIFI] Reconnected successfully");
                wifiConnected = true;
                wifiServer.on("/status", handleWifiStatus);
                wifiServer.begin();
                httpServerStarted = true;
                
                char connectedMsg[32];
                snprintf(connectedMsg, sizeof(connectedMsg), "Connected to %s", WIFI_SSID);
                displayWake();
                displayUpdate("WIFI FALLBACK",
                             connectedMsg,
                             WiFi.localIP().toString().c_str(),
                             "Hold 8s to exit");
                displayTimeout = UINT32_MAX;
            } else {
                Serial.println("[WIFI] Reconnect failed, returning to LoRa");
                displayUpdate("WIFI FAILED", "Reconnect failed", "Returning to LoRa...");
                wifiFallbackEnabled = false;
                currentMode = MODE_LORA_ACTIVE;
                delay(3000);
                
                LMIC_reset();
                delay(100);
                LMIC_setLinkCheckMode(0);
                LMIC.dn2Dr = DR_SF9;
                LMIC_setDrTxpow(DR_SF7, 14);
                LMIC_startJoining();
            }
        }
    }
}

// ============================================================================
// WI-FI CONNECTION TEST (Diagnostic)
// ============================================================================

void wifiTestConnection() {
    Serial.println("\n=== WI-FI CONNECTION TEST ===");
    Serial.printf("[TEST] SSID: %s\n", WIFI_SSID);
    
    // Initialize WiFi
    Serial.println("[TEST] Initializing WiFi...");
    WiFi.mode(WIFI_OFF);
    delay(100);
    WiFi.mode(WIFI_STA);
    delay(100);
    
    Serial.printf("[TEST] WiFi mode: %d, status: %d\n", WiFi.getMode(), WiFi.status());
    
    // Scan for networks with retry
    Serial.println("[TEST] Scanning for networks (attempt 1)...");
    int n = WiFi.scanNetworks();
    Serial.printf("[TEST] Found %d networks\n", n);
    
    if (n == 0) {
        Serial.println("[TEST] No networks found, waiting and retrying...");
        delay(3000);
        n = WiFi.scanNetworks();
        Serial.printf("[TEST] Retry result: %d networks\n", n);
    }
    
    Serial.println("[TEST] Available networks:");
    bool ssidFound = false;
    for (int i = 0; i < n; i++) {
        Serial.printf("  %d: %s (%d dBm, Ch:%d, %s)\n",
                     i + 1,
                     WiFi.SSID(i).c_str(),
                     WiFi.RSSI(i),
                     WiFi.channel(i),
                     WiFi.encryptionType(i) == WIFI_AUTH_OPEN ? "Open" : "Enc");
        
        if (WiFi.SSID(i) == String(WIFI_SSID)) {
            ssidFound = true;
            Serial.printf("  >>> Target '%s' FOUND! Signal: %d dBm\n", WIFI_SSID, WiFi.RSSI(i));
        }
    }
    
    if (!ssidFound) {
        Serial.printf("[TEST] Target SSID '%s' not in list\n", WIFI_SSID);
        displayUpdate("WI-FI TEST", "SSID not in list", "Check name");
        WiFi.mode(WIFI_OFF);
        return;
    }
    
    // Try connecting
    Serial.println("[TEST] Attempting connection...");
    displayUpdate("WI-FI TEST", "Connecting...", WIFI_SSID);
    
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    uint32_t startTime = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startTime < 30000) {
        delay(500);
        
        if (millis() - startTime % 2000 < 500) {
            Serial.printf(".");
        }
        
        if (millis() - startTime > 5000 && millis() - startTime < 5100) {
            Serial.printf("\n[TEST] Status: %d (elapsed %lu s)\n", WiFi.status(), (millis()-startTime)/1000);
        }
    }
    Serial.println();
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("[TEST] SUCCESS!");
        Serial.printf("[TEST] IP: %s, MAC: %s, RSSI: %d dBm\n",
                     WiFi.localIP().toString().c_str(),
                     WiFi.macAddress().c_str(),
                     WiFi.RSSI());
        displayUpdate("WI-FI TEST", "SUCCESS!", WiFi.localIP().toString().c_str());
    } else {
        Serial.printf("[TEST] FAILED (status: %d)\n", WiFi.status());
        displayUpdate("WI-FI TEST", "FAILED", "Check password");
    }
    
    WiFi.mode(WIFI_OFF);
    Serial.println("=== TEST COMPLETE ===\n");
}
