# Cycle Failure Tracking Patch

## Summary
This patch adds proper transmission cycle failure tracking to activate Wi-Fi fallback after 10 failed transmission cycles.

## Changes Required

### 1. In do_send() function (around line 1063)

**ADD** after `LMIC_setTxData2(1, payload, payloadLen, 0);`:

```cpp
// Track transmission cycle for failure counting
static bool awaitingTXComplete = false;
awaitingTXComplete = true;  // Mark that we're awaiting TX completion
```

### 2. In EV_TXCOMPLETE event handler (around line 973)

**ADD** after `transmitting = false;`:

```cpp
// Track transmission cycle success
static bool awaitingTXComplete = false;
if (awaitingTXComplete) {
    // Successfully completed transmission cycle
    Serial.println("[LORA] Transmission cycle completed successfully");
    consecutiveCycleFails = 0;  // Reset failure counter
    awaitingTXComplete = false;
} else {
    // Unexpected TX complete without pending cycle
    Serial.println("[LORA] TX complete without pending cycle");
}
```

### 3. In EV_TXCANCELED event handler (around line 1040)

**ADD** after the event:

```cpp
case EV_TXCANCELED:
    Serial.println("EV_TXCANCELED");
    if (joined) {
        fieldTestModeSetState(STATE_JOINED);
    }
    
    // Track transmission cycle failure
    Serial.println("[LORA] Transmission cycle failed - TX canceled");
    consecutiveCycleFails++;
    Serial.printf("[LORA] Consecutive transmission failures: %u / %u\n", 
                 consecutiveCycleFails, AUTO_WIFI_AFTER_N_CYCLE_FAILURES);
    
    // Auto-activate Wi-Fi fallback after N cycle failures
    if (consecutiveCycleFails >= AUTO_WIFI_AFTER_N_CYCLE_FAILURES && !wifiFallbackEnabled) {
        Serial.println("[LORA] Too many transmission failures - auto-enabling Wi-Fi fallback");
        wifiFallbackEnabled = true;
    }
    break;
```

### 4. Add timeout tracking for lost transmissions

**ADD** in main loop (around line 1264, inside `if (currentMode == MODE_LORA_ACTIVE)`):

```cpp
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
```

## How It Works

1. **Cycle Start**: `do_send()` marks `awaitingTXComplete = true`
2. **Success**: `EV_TXCOMPLETE` resets `consecutiveCycleFails = 0`
3. **Failure**: `EV_TXCANCELED` or timeout increments `consecutiveCycleFails`
4. **Auto-Activate**: After 10 consecutive failures, Wi-Fi fallback enabled

## Button Control (Already Implemented)

- **Short press (<1s)**: Force LoRa join
- **Long press (>3s)**: Enable Wi-Fi fallback  
- **Very long press (>8s)**: Restart device

## Expected Behavior

1. Device joins TTN successfully
2. Sends data every 60 seconds
3. If transmission fails (canceled or timeout), count increases
4. After 10 consecutive transmission failures, Wi-Fi activates
5. Long press button can trigger Wi-Fi immediately
6. Successful transmissions reset the failure counter

This approach tracks **transmission cycle failures** rather than just join failures, which is what you requested.
