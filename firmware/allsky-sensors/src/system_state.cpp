/*
 * System State Management - Implementation
 */

#include "system_state.h"

// ============================================================================
// SYSTEM STATE MACHINE
// ============================================================================

// Default mode: Wi-Fi fallback (LoRa only activates on explicit trigger)
SystemMode currentMode = MODE_WIFI_FALLBACK;

// Wi-Fi Fallback State
bool wifiFallbackEnabled = false;
bool wifiConnected = false;
uint32_t wifiConnectionAttempt = 0;
uint32_t lastWifiAttemptTime = 0;
const uint32_t WIFI_RETRY_INTERVAL_MS = 10000;  // 10 seconds between retries
const uint32_t WIFI_CONNECTION_TIMEOUT_MS = 30000;  // 30 seconds to connect

// Auto-activation threshold for Wi-Fi fallback (10 failed transmission cycles)
const uint8_t AUTO_WIFI_AFTER_N_CYCLE_FAILURES = 10;
uint8_t consecutiveCycleFails = 0;

// ============================================================================
// LORA STATE (Field Test Mode)
// ============================================================================

LoRaState currentLoRaState = STATE_INIT;

// Field test mode counters
uint32_t joinAttempts = 0;
uint32_t txCount = 0;
uint32_t lastJoinAttempt = 0;

// Field test mode state
bool fieldTestModeActive = true;
uint32_t lastFieldTestUpdate = 0;
const uint32_t FIELD_TEST_REFRESH_MS = 500;  // 2Hz refresh rate (500ms)
