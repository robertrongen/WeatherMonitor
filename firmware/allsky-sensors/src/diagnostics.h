/*
 * Diagnostics and Logging
 * 
 * Field test mode display, LED indicators, and loop diagnostics
 */

#ifndef DIAGNOSTICS_H
#define DIAGNOSTICS_H

#include <Arduino.h>

// ============================================================================
// STATUS LED
// ============================================================================

#define STATUS_LED 25  // GPIO25 (Heltec V2 onboard LED)

// ============================================================================
// LOOP DIAGNOSTIC COUNTERS
// ============================================================================

extern uint32_t loopCount;
extern uint32_t lastLoopLog;
extern const uint32_t LOOP_LOG_INTERVAL_MS;

// ============================================================================
// FIELD TEST MODE DISPLAY STATE
// ============================================================================

extern char fieldTestLine1[32];
extern char fieldTestLine2[32];
extern char fieldTestLine3[32];
extern char fieldTestLine4[32];
extern const uint32_t FIELD_TEST_REFRESH_MS;

// ============================================================================
// LED FUNCTIONS
// ============================================================================

// Initialize status LED
void ledInit();

// Basic LED blink
void ledBlink(int duration_ms = 200);

// Quick double blink for TX
void ledBlinkTx();

// Triple blink for successful join
void ledBlinkJoined();

// ============================================================================
// FIELD TEST MODE FUNCTIONS
// ============================================================================

// Update field test mode display (non-blocking 2Hz refresh)
void fieldTestModeUpdate();

// Set LoRa state and force display update
void fieldTestModeSetState(int newState);  // Takes LoRaState enum value

#endif // DIAGNOSTICS_H
