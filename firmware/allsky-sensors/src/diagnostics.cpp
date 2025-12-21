/*
 * Diagnostics and Logging - Implementation
 */

#include "diagnostics.h"
#include "system_state.h"
#include "display.h"
#include "sensors.h"
#include <lmic.h>

// ============================================================================
// LOOP DIAGNOSTIC COUNTERS
// ============================================================================

uint32_t loopCount = 0;
uint32_t lastLoopLog = 0;
const uint32_t LOOP_LOG_INTERVAL_MS = 5000;  // Log every 5 seconds

// ============================================================================
// FIELD TEST MODE DISPLAY STATE
// ============================================================================

char fieldTestLine1[32] = "";
char fieldTestLine2[32] = "";
char fieldTestLine3[32] = "";
char fieldTestLine4[32] = "";
const uint32_t FIELD_TEST_REFRESH_MS = 500;  // 2Hz refresh rate (500ms)

// ============================================================================
// LED FUNCTIONS
// ============================================================================

void ledInit() {
    pinMode(STATUS_LED, OUTPUT);
    digitalWrite(STATUS_LED, LOW);
    Serial.println("✓ Status LED initialized (GPIO25)");
}

void ledBlink(int duration_ms) {
    digitalWrite(STATUS_LED, HIGH);
    delay(duration_ms);
    digitalWrite(STATUS_LED, LOW);
}

void ledBlinkTx() {
    // Quick double blink for TX
    ledBlink(100);
    delay(50);
    ledBlink(100);
}

void ledBlinkJoined() {
    // Triple blink for successful join
    for (int i = 0; i < 3; i++) {
        ledBlink(150);
        delay(100);
    }
}

// ============================================================================
// FIELD TEST MODE DISPLAY
// ============================================================================

void fieldTestModeUpdate() {
    if (!fieldTestModeActive) return;
    
    // Non-blocking 2Hz refresh
    if (millis() - lastFieldTestUpdate < FIELD_TEST_REFRESH_MS) {
        return;
    }
    lastFieldTestUpdate = millis();
    
    // Update display based on current LoRaWAN state
    switch (currentLoRaState) {
        case STATE_INIT:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "BUILD: 1.0.3");
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "WIFI FALLBACK MODE");
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "Initializing...");
            fieldTestLine4[0] = '\0';
            break;
            
        case STATE_BOOT:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "BUILD: 1.0.3");
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "BOOT OK");
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "Starting LoRaWAN...");
            snprintf(fieldTestLine4, sizeof(fieldTestLine4), "BTN: Force join");
            break;
            
        case STATE_JOINING:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "JOINING (%lu)", joinAttempts);
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "Attempting OTAA...");
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "TTN Network");
            fieldTestLine4[0] = '\0';
            break;
            
        case STATE_JOIN_TX:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "JOIN TX OK");
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "Wait for JOINED");
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "RX Window");
            fieldTestLine4[0] = '\0';
            break;
            
        case STATE_JOINED:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "JOINED!");
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "DevAddr: %08lX", LMIC.devaddr);
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "TX Count: %lu", txCount);
            snprintf(fieldTestLine4, sizeof(fieldTestLine4), "Ready for uplink");
            break;
            
        case STATE_JOIN_FAILED:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "JOIN FAIL");
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "Retry %lu", joinAttempts);
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "Check TTN config");
            fieldTestLine4[0] = '\0';
            break;
            
        case STATE_TX:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "UPLINK #%lu", txCount);
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "TX in progress...");
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "RSSI: %d dBm", sensorData.rssi);
            fieldTestLine4[0] = '\0';
            break;
            
        case STATE_LINK_DEAD:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "LINK DEAD");
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "Reconnecting...");
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "TX Count: %lu", txCount);
            fieldTestLine4[0] = '\0';
            break;
    }
    
    // Update OLED display
    displayUpdate(fieldTestLine1, fieldTestLine2, fieldTestLine3, fieldTestLine4);
}

void fieldTestModeSetState(int newState) {
    currentLoRaState = (LoRaState)newState;
    // Force immediate update on state change
    lastFieldTestUpdate = 0;
}
