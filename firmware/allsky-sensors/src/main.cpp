/*
 * AllSky Sensors - Heltec WiFi LoRa 32 V2 Firmware
 * BUILD VERSION: 1.0.3 - WI-FI FALLBACK MODE
 *
 * Hardware: Heltec WiFi LoRa 32 V2 (ESP32-PICO-D4 + SX1276 LoRa + OLED)
 * Backend: The Things Network (TTN) v3 or Chirpstack
 * Fallback: Wi-Fi HTTP server with JSON status endpoint
 *
 * Integrated Components (Pre-wired):
 * - LoRa Radio: SX1276 (868/915 MHz) internally connected via SPI
 * - OLED Display: 0.96" SSD1306 (I²C 0x3C) for field diagnostics
 * - Status LED: GPIO25 (for field test mode visual feedback)
 *
 * External Sensors (GPIO21/22 I²C bus - separate from display):
 * - MLX90614 IR Temperature Sensor (I²C 0x5A)
 * - TSL2591 Sky Quality Meter (I²C 0x29)
 * - RG-9 Rain Sensor (Analog GPIO36 with voltage divider)
 * - Wind Sensor (Pulse mode GPIO32 with optocoupler - moved from GPIO34 to avoid LoRa DIO conflict)
 *
 * Pin Mappings (Heltec WiFi LoRa 32 V2):
 * LoRa SPI (internal):    GPIO5 (SCK), GPIO19 (MISO), GPIO27 (MOSI)
 * LoRa Control (internal): GPIO18 (CS), GPIO14 (RST), GPIO26 (DIO0), GPIO33 (DIO1)
 * Display I²C (internal):  GPIO4 (SDA), GPIO15 (SCL), GPIO16 (RST)
 * Sensor I²C (external):   GPIO21 (SDA), GPIO22 (SCL)
 * Rain ADC:                GPIO36 (ADC1_CH0) with 5.1kΩ/10kΩ divider
 * Wind Pulse:              GPIO32 (interrupt, moved from GPIO34 to avoid DIO2 conflict)
 * Status LED:              GPIO25 (for field test mode)
 * Button User:             GPIO0 (PRG button, for mode control)
 *
 * Architecture: docs/architecture/board-esp32-lora-display/ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md
 * Wiring: docs/architecture/board-esp32-lora-display/HARDWARE_WIRING_ESP32_LORA_DISPLAY.md
 */

#include <Arduino.h>
#include <lmic.h>
#include <SPI.h>
#include "secrets.h"

// Module includes
#include "system_state.h"
#include "button.h"
#include "display.h"
#include "lora.h"
#include "wifi_fallback.h"
#include "sensors.h"
#include "diagnostics.h"

// ============================================================================
// SETUP
// ============================================================================

void setup() {
    // Initialize serial
    Serial.begin(115200);
    delay(500);
    
    Serial.println("\n\n=== AllSky Sensors - Heltec WiFi LoRa 32 V2 ===");
    Serial.println("BUILD VERSION: 1.0.3 - WI-FI FALLBACK MODE");
    Serial.println("Hardware: ESP32-PICO-D4 + SX1276 LoRa + OLED");
    Serial.println("Features: LoRa OTAA + Wi-Fi Fallback + Button Control");
    Serial.printf("Boot completed at %lu ms\n\n", millis());
    
    // Initialize status LED for field test mode
    ledInit();
    
    // Initialize button (PRG button on GPIO0)
    buttonInit();
    
    // Initialize display
    displayInit();
    fieldTestModeSetState(STATE_INIT);
    delay(1000);
    
    // Initialize sensors
    sensorsInit();
    delay(1000);
    
    // Set boot state
    fieldTestModeSetState(STATE_BOOT);
    delay(1000);
    
    // Check TTN credentials
    bool configured = false;
    for (int i = 0; i < 8; i++) {
        if (DEVEUI[i] != 0x00 || APPEUI[i] != 0x00) {
            configured = true;
            break;
        }
    }
    for (int i = 0; i < 16; i++) {
        if (APPKEY[i] != 0x00) {
            configured = true;
            break;
        }
    }
    
    if (!configured) {
        Serial.println("\n⚠️  WARNING: TTN credentials not configured!");
        Serial.println("Please update src/secrets.h with your TTN device credentials");
        displayUpdate("ERROR", "No TTN Config", "Check secrets.h");
        while(1) {
            delay(1000);
        }
    }
    
    Serial.println("TTN credentials detected");
    
    // Print credentials for TTN verification BEFORE join
    Serial.println("\n=== TTN CREDENTIAL VERIFICATION ===");
    Serial.println("Compare these values with your TTN Console:\n");
    
    // DevEUI - LMIC expects LSB format, TTN shows both formats
    Serial.print("DevEUI (LSB->MSB as stored): ");
    for (int i = 0; i < 8; i++) {
        Serial.printf("%02X", DEVEUI[i]);
        if (i < 7) Serial.print("-");
    }
    Serial.println();
    
    Serial.print("DevEUI (MSB->LSB reversed):   ");
    for (int i = 7; i >= 0; i--) {
        Serial.printf("%02X", DEVEUI[i]);
        if (i > 0) Serial.print("-");
    }
    Serial.println(" ← Use this if TTN shows MSB format\n");
    
    // AppEUI/JoinEUI - LMIC expects LSB format
    Serial.print("AppEUI (LSB->MSB as stored): ");
    for (int i = 0; i < 8; i++) {
        Serial.printf("%02X", APPEUI[i]);
        if (i < 7) Serial.print("-");
    }
    Serial.println();
    
    Serial.print("AppEUI (MSB->LSB reversed):   ");
    for (int i = 7; i >= 0; i--) {
        Serial.printf("%02X", APPEUI[i]);
        if (i > 0) Serial.print("-");
    }
    Serial.println(" ← Use this if TTN shows MSB format\n");
    
    // AppKey - MSB format (NOT reversed)
    Serial.print("AppKey (MSB as-is):          ");
    for (int i = 0; i < 16; i++) {
        Serial.printf("%02X", APPKEY[i]);
        if (i < 15) Serial.print("-");
    }
    Serial.println(" ← Must match TTN exactly\n");
    
    Serial.println("TTN Console Notes:");
    Serial.println("- DevEUI & AppEUI: Toggle 'LSB' in TTN Console, copy-paste to secrets.h");
    Serial.println("- AppKey: Use default MSB format from TTN Console");
    Serial.println("- If join fails, verify byte order and check TTN Live Data tab");
    Serial.println("===================================\n");
    
    // Initialize LoRa hardware but don't start OTAA join
    // LoRa will only activate on explicit button press or trigger
    Serial.println("Initializing LoRa hardware (quiescent)...");
    
    // Initialize SPI for LoRa hardware
    SPI.begin(5, 19, 27);
    Serial.println("✓ SPI initialized (SCK=5, MISO=19, MOSI=27)");
    
    // Initialize LMIC but don't join
    os_init();
    Serial.println("✓ LMIC initialized (quiescent)");
    LMIC_reset();
    
    // Configure LMIC defaults (but don't start joining)
    LMIC_setLinkCheckMode(0);
    LMIC.dn2Dr = DR_SF9;
    LMIC_setDrTxpow(DR_SF7, 14);
    
    Serial.println("\n=== BOOT COMPLETE ===");
    Serial.println("Default Mode: Wi-Fi Fallback (idle)");
    Serial.println("Button: Short press (< 1s) to force LoRa join");
    Serial.println("Button: Long press (>= 3s) to enable Wi-Fi");
    Serial.println("=======================\n");
    
    // Update display to show ready state
    displayUpdate("READY", "Wi-Fi Fallback Mode", "Press BTN for LoRa", "Hold 3s for Wi-Fi");
    
    // Run WiFi test to check network availability
    delay(2000);  // Brief delay before test
    wifiTestConnection();
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
    // Increment loop counter for diagnostics
    // loopCount++;
    
    // // Periodic loop execution confirmation
    // if (millis() - lastLoopLog >= LOOP_LOG_INTERVAL_MS) {
    //     Serial.printf("[LOOP] Running normally - %lu iterations in last %lu ms\n",
    //                   loopCount, millis() - lastLoopLog);
    //     loopCount = 0;
    //     lastLoopLog = millis();
    // }
    
    // ============================================================================
    // STATE MACHINE: Handle mode switching between LoRa and Wi-Fi
    // ============================================================================
    
    // Check if Wi-Fi fallback should be activated
    // This handles both: switching from LoRa mode, or activating from idle WiFi mode
    static bool wifiActivating = false;

    if (wifiFallbackEnabled && !wifiActivating &&  !wifiConnected) {
        wifiActivating = true;  // Prevent re-entry
        if (currentMode == MODE_LORA_ACTIVE) {
            // Switching from LoRa to Wi-Fi
            Serial.println("[MAIN] Switching from LoRa to Wi-Fi fallback");
        } else {
            // Activating Wi-Fi from idle state
            Serial.println("[MAIN] Activating Wi-Fi from idle state");
        }
        wifiFallbackStart();
        wifiActivating = false;
    }
    
    // Check button presses
    buttonCheck();
    
    // ============================================================================
    // MODE-SPECIFIC OPERATIONS
    // ============================================================================
    
    if (currentMode == MODE_LORA_ACTIVE) {
        // LoRa mode: Run LMIC scheduler (time-critical, must not be blocked)
        // ONLY service LMIC when in LoRa mode to ensure full quiesce in Wi-Fi mode
        os_runloop_once();
        
        // Handle join retry with exponential backoff
        loraHandleJoinRetry();
        
        // Update field test mode display (non-blocking 2Hz refresh)
        fieldTestModeUpdate();
        
        // Track transmission timeouts (failed cycles)
        static uint32_t lastTXStartTime = 0;
        if (transmitting && lastTXStartTime == 0) {
            lastTXStartTime = millis();  // Mark TX start
        }
        if (!transmitting) {
            lastTXStartTime = 0;  // Clear when TX completes
        }
        
        // Check for TX timeout (no response for 120 seconds)
        if (transmitting && lastTXStartTime > 0 && 
            millis() - lastTXStartTime > 120000) {  // 2 minute timeout
            Serial.println("[LORA] TX timeout - transmission cycle failed");
            transmitting = false;
            consecutiveCycleFails++;
            Serial.printf("[LORA] Consecutive transmission failures: %u / %u\n", 
                         consecutiveCycleFails, AUTO_WIFI_AFTER_N_CYCLE_FAILURES);
            lastTXStartTime = 0;
            
            // Auto-activate Wi-Fi fallback after N cycle failures
            if (consecutiveCycleFails >= AUTO_WIFI_AFTER_N_CYCLE_FAILURES && !wifiFallbackEnabled) {
                Serial.println("[LORA] Too many transmission failures - auto-enabling Wi-Fi fallback");
                wifiFallbackEnabled = true;
            }
        }
        
        // Transmission scheduling
        if (joined && !transmitting && millis() >= nextTransmissionTime) {
            do_send(&sendjob);
        }
        
    } else if (currentMode == MODE_WIFI_FALLBACK) {
        // Wi-Fi fallback mode: Handle HTTP server
        wifiFallbackLoop();
        
        // Optionally read sensors and update display periodically in Wi-Fi mode
        static uint32_t lastWifiSensorRead = 0;
        if (millis() - lastWifiSensorRead > 60000) {  // Every 60 seconds
            sensorsRead();
            lastWifiSensorRead = millis();
        }
        
        // Small delay to allow HTTP server to process
        delay(5);  // 5ms delay for HTTP responsiveness
    }
    
    // Check display timeout (common to both modes)
    displayCheck();
    
    // No delay - LMIC requires continuous servicing for RX windows in LoRa mode
    // Watchdog is automatically handled by yield() inside os_runloop_once()
}
