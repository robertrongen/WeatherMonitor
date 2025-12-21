/*
 * System State Management
 * 
 * System-level state machine for LoRa vs Wi-Fi fallback mode switching
 */

#ifndef SYSTEM_STATE_H
#define SYSTEM_STATE_H

#include <Arduino.h>

// ============================================================================
// SYSTEM STATE MACHINE (LoRa vs Wi-Fi Fallback)
// ============================================================================

// System-level state machine (separate from LoRaWAN state)
enum SystemMode {
    MODE_LORA_ACTIVE,      // LoRa is primary transport (normal mode)
    MODE_WIFI_FALLBACK,    // Wi-Fi fallback is active (LoRa stopped)
    MODE_SWITCHING         // Transitioning between modes
};

// Current system mode
extern SystemMode currentMode;

// Wi-Fi Fallback State
extern bool wifiFallbackEnabled;
extern bool wifiConnected;
extern uint32_t wifiConnectionAttempt;
extern uint32_t lastWifiAttemptTime;

// Auto-activation threshold for Wi-Fi fallback (10 failed transmission cycles)
extern const uint8_t AUTO_WIFI_AFTER_N_CYCLE_FAILURES;
extern uint8_t consecutiveCycleFails;

// ============================================================================
// LORA STATE (Field Test Mode)
// ============================================================================

// Current LoRaWAN state for field test display
enum LoRaState {
    STATE_INIT,
    STATE_BOOT,
    STATE_JOINING,
    STATE_JOIN_TX,
    STATE_JOINED,
    STATE_JOIN_FAILED,
    STATE_TX,
    STATE_LINK_DEAD
};

extern LoRaState currentLoRaState;

// Field test mode counters
extern uint32_t joinAttempts;
extern uint32_t txCount;
extern uint32_t lastJoinAttempt;

// Field test mode state
extern bool fieldTestModeActive;
extern uint32_t lastFieldTestUpdate;

#endif // SYSTEM_STATE_H
