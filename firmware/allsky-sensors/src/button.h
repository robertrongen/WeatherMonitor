/*
 * Button Input Management
 * 
 * Button ISR, debounce, and press duration classification for GPIO0
 */

#ifndef BUTTON_H
#define BUTTON_H

#include <Arduino.h>

// ============================================================================
// BUTTON PIN CONFIGURATION
// ============================================================================

#define BUTTON_PIN 0   // GPIO0 (PRG button on Heltec V2)

// ============================================================================
// BUTTON STATE
// ============================================================================

extern volatile uint32_t buttonPressTime;
extern volatile bool buttonPressed;
extern volatile bool buttonReleased;
extern uint32_t lastButtonDebounce;

// Button press thresholds
extern const uint32_t BUTTON_DEBOUNCE_MS;
extern const uint32_t SHORT_PRESS_MS;       // Minimum debounced press
extern const uint32_t SHORT_PRESS_MAX_MS;   // Maximum for short press (< 1s)
extern const uint32_t LONG_PRESS_MS;        // 3 seconds for Wi-Fi fallback
extern const uint32_t VERY_LONG_PRESS_MS;   // 8 seconds for restart

// ============================================================================
// BUTTON FUNCTIONS
// ============================================================================

// Button ISR (called on button press/release)
void IRAM_ATTR buttonISR();

// Initialize button GPIO and ISR
void buttonInit();

// Check button state and handle actions (called from loop)
void buttonCheck();

#endif // BUTTON_H
