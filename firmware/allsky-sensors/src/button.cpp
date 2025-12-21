/*
 * Button Input Management - Implementation
 */

#include "button.h"
#include "system_state.h"
#include "display.h"
#include "lora.h"
#include <lmic.h>

// ============================================================================
// BUTTON STATE
// ============================================================================

volatile uint32_t buttonPressTime = 0;
volatile bool buttonPressed = false;
volatile bool buttonReleased = false;
uint32_t lastButtonDebounce = 0;
const uint32_t BUTTON_DEBOUNCE_MS = 50;

// Button press thresholds
const uint32_t SHORT_PRESS_MS = 50;       // Minimum for valid press
const uint32_t LONG_PRESS_MS = 3000;      // 3 seconds for Wi-Fi fallback
const uint32_t VERY_LONG_PRESS_MS = 8000; // 8 seconds for restart

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
        
        // Very long press: Disable Wi-Fi fallback and restart
        if (pressDuration >= VERY_LONG_PRESS_MS) {
            Serial.println("[BUTTON] VERY LONG PRESS - Restart requested");
            displayUpdate("RESTART", "Rebooting...", "Wi-Fi disabled");
            delay(2000);
            ESP.restart();
        }
        // Long press: Enable Wi-Fi fallback mode
        else if (pressDuration >= LONG_PRESS_MS) {
            Serial.println("[BUTTON] LONG PRESS - Enable Wi-Fi fallback");
            if (currentMode != MODE_WIFI_FALLBACK) {
                wifiFallbackEnabled = true;
            } else {
                Serial.println("[BUTTON] Already in Wi-Fi fallback mode");
            }
        }
        // Short press: Force immediate LoRa join attempt
        else if (pressDuration >= SHORT_PRESS_MS) {
            Serial.println("[BUTTON] SHORT PRESS - Force LoRa join");
            if (currentMode == MODE_LORA_ACTIVE && !joined) {
                displayUpdate("BUTTON", "Force LoRa join", "Attempting now...");
                LMIC_startJoining();
            } else if (joined) {
                Serial.println("[BUTTON] Already joined to LoRa");
                displayUpdate("BUTTON", "Already joined!", "No action needed");
            } else {
                Serial.println("[BUTTON] Not in LoRa mode");
            }
        }
        
        buttonPressed = false;
    }
}
