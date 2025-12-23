/*
 * Button Input Management - Implementation
 */

#include "button.h"
#include "system_state.h"
#include "display.h"
#include "lora.h"
#include "wifi_fallback.h"
#include <lmic.h>

// ============================================================================
// BUTTON STATE
// ============================================================================

volatile uint32_t buttonPressTime = 0;
volatile bool buttonPressed = false;
volatile bool buttonReleased = false;
uint32_t lastButtonDebounce = 0;
const uint32_t BUTTON_DEBOUNCE_MS = 50;

// Button press thresholds (contract-compliant)
const uint32_t SHORT_PRESS_MS = 100;      // Minimum debounced press
const uint32_t SHORT_PRESS_MAX_MS = 999;  // < 1s for Force LoRa Join
const uint32_t LONG_PRESS_MS = 3000;      // >= 3s for Wi-Fi fallback
const uint32_t VERY_LONG_PRESS_MS = 8000; // >= 8s for restart

// ============================================================================
// BUTTON ISR
// ============================================================================

void IRAM_ATTR buttonISR() {
    uint32_t now = millis();
    if (now - lastButtonDebounce < BUTTON_DEBOUNCE_MS) {
        return;  // Ignore bounces
    }
    lastButtonDebounce = now;
    
    if (digitalRead(BUTTON_PIN) == LOW) {
        // Button pressed (active low)
        buttonPressed = true;
        buttonPressTime = now;
    } else {
        // Button released
        buttonReleased = true;
    }
}

// ============================================================================
// BUTTON INITIALIZATION
// ============================================================================

void buttonInit() {
    pinMode(BUTTON_PIN, INPUT_PULLUP);  // Internal pull-up, button is active low
    attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), buttonISR, CHANGE);
    Serial.println("✓ Button initialized (GPIO0/PRG)");
}

// ============================================================================
// BUTTON HANDLER
// ============================================================================

void buttonCheck() {
    // Check if button was released
    if (buttonReleased) {
        buttonReleased = false;
        uint32_t pressDuration = millis() - buttonPressTime;
        
        Serial.printf("[BUTTON] Released after %lu ms\n", pressDuration);
        
        // Wake display for all button actions
        displayWake();
        
        // Very long press: Restart system
        if (pressDuration >= VERY_LONG_PRESS_MS) {
            Serial.println("[BUTTON] VERY LONG PRESS - Restart requested");
            displayUpdate("RESTART", "Rebooting...");
            delay(2000);
            ESP.restart();
        }
        // Long press: Enable Wi-Fi fallback mode (>= 3s)
        else if (pressDuration >= LONG_PRESS_MS) {
            Serial.println("[BUTTON] LONG PRESS - Enable Wi-Fi fallback");
            if (currentMode != MODE_WIFI_FALLBACK && !wifiFallbackEnabled) {
                wifiFallbackEnabled = true;
                displayUpdate("BUTTON", "Wi-Fi fallback", "Activating...");
            } else {
                Serial.println("[BUTTON] Wi-Fi fallback already active/enabled");
                displayUpdate("BUTTON", "Wi-Fi fallback", "Already active");
            }
        }
        // Short press: Force LoRa join (< 1s)
        else if (pressDuration >= SHORT_PRESS_MS && pressDuration <= SHORT_PRESS_MAX_MS) {
            Serial.println("[BUTTON] SHORT PRESS - Force LoRa join");
            
            // If already joined, inform user
            if (joined) {
                Serial.println("[BUTTON] Already joined to LoRa");
                displayUpdate("BUTTON", "Already joined!", "LoRa active");
            }
            // If in Wi-Fi mode (active or idle), switch to LoRa and join
            else if (currentMode == MODE_WIFI_FALLBACK) {
                Serial.println("[BUTTON] Activating LoRa mode from Wi-Fi fallback");
                displayUpdate("BUTTON", "Activating LoRa", "Starting join...");
                
                // Stop Wi-Fi if active
                if (wifiFallbackEnabled) {
                    wifiFallbackStop();
                    delay(200);
                }
                
                // Switch to LoRa mode
                currentMode = MODE_LORA_ACTIVE;
                
                // Start LoRa join
                LMIC_reset();
                delay(100);
                LMIC_setLinkCheckMode(0);
                LMIC.dn2Dr = DR_SF9;
                LMIC_setDrTxpow(DR_SF7, 14);
                LMIC_startJoining();
                
                Serial.println("[BUTTON] LoRa mode activated, joining...");
            }
            // If in LoRa mode but not joined, force join now
            else if (currentMode == MODE_LORA_ACTIVE && !joined) {
                displayUpdate("BUTTON", "Force LoRa join", "Attempting now...");
                LMIC_startJoining();
            }
        }
        
        buttonPressed = false;
    }
}
