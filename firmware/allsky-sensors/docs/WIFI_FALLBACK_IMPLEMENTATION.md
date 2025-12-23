# Wi-Fi Fallback Mode Implementation

## Overview
This document describes the Wi-Fi fallback mode implementation for the Heltec WiFi LoRa 32 V2 board. The system provides operational resilience by allowing fallback to Wi-Fi when LoRa connectivity fails.

## Build Version
**1.0.3 - Wi-Fi Fallback Mode**

## Architecture

### Design Principles
1. **LoRa is PRIMARY** - Always preferred when available
2. **Wi-Fi is SECONDARY** - Fallback only, never concurrent with LoRa
3. **Mutual Exclusion** - LoRa and Wi-Fi NEVER active simultaneously
4. **Button-Controlled** - User can manually trigger mode changes
5. **Auto-Activation** - Automatic fallback after repeated LoRa failures

### State Machine

```
System Modes:
- MODE_LORA_ACTIVE      → LoRa operational, Wi-Fi off
- MODE_WIFI_FALLBACK    → Wi-Fi operational, LoRa stopped
- MODE_SWITCHING        → Transitioning between modes
```

### LoRa States (unchanged)
- STATE_INIT, STATE_BOOT, STATE_JOINING
- STATE_JOIN_TX, STATE_JOINED, STATE_JOIN_FAILED
- STATE_TX, STATE_LINK_DEAD

## Button Controls (GPIO0 / PRG Button)

### Button Press Actions

| Press Duration | Action | Description |
|---------------|--------|-------------|
| < 1s (Short) | Force LoRa Join | Immediately triggers OTAA join attempt |
| > 3s (Long) | Enable Wi-Fi Fallback | Activates Wi-Fi fallback mode |
| > 8s (Very Long) | Restart Device | Disables Wi-Fi and reboots ESP32 |

### Implementation Details
- Button is active-low with internal pull-up
- Hardware debounce: 50ms
- Interrupt-driven with CHANGE trigger
- Thread-safe ISR handling

## Wi-Fi Fallback Mode

### Activation Triggers

1. **Manual Activation**
   - Long press (>3s) on Button User
   - Immediate transition to Wi-Fi mode

2. **Auto-Activation**
   - After 10 consecutive LoRa join failures
   - Configurable threshold: `AUTO_WIFI_AFTER_N_FAILURES`
   - Prevents endless join loops in dead zones

### Wi-Fi Features

#### HTTP Server
- **Port**: 80
- **Endpoint**: `/status`
- **Format**: JSON

#### Status Endpoint Response
```json
{
  "uptime_seconds": 12345,
  "lora_joined": false,
  "last_join_attempt": 12340,
  "join_attempts": 15,
  "consecutive_fails": 10,
  "tx_count": 0,
  "sensors": {
    "sky_temp_c": -12.34,
    "ambient_temp_c": 18.56,
    "sqm_lux": 0.05,
    "sqm_ir": 123,
    "sqm_full": 456,
    "rain_intensity": 1023,
    "wind_speed_ms": 3.45
  }
}
```

**Note**: Sensor values are `null` if sensor is invalid/offline.

### OLED Display in Wi-Fi Mode

**During Connection:**
```
Line 1: WI-FI FALLBACK
Line 2: Connecting to [SSID]
```

**After Connected:**
```
Line 1: WIFI FALLBACK
Line 2: Connected to [SSID]
Line 3: 192.168.1.123 (IP address)
Line 4: Hold 8s to exit
```

Display stays on continuously in Wi-Fi mode for monitoring.

### Exiting Wi-Fi Fallback

1. **Very Long Button Press** (>8s)
   - Stops Wi-Fi server
   - Disconnects from Wi-Fi
   - Resets LMIC and restarts LoRa join
   - Reboots device

2. **Automatic Reconnection**
   - If Wi-Fi connection lost, attempts reconnect
   - After timeout, falls back to LoRa mode

## Configuration

### secrets.h Updates

Add Wi-Fi credentials to your `secrets.h` file:

```cpp
// Wi-Fi Fallback Credentials (optional)
static const char* WIFI_SSID = "YourWiFiSSID";
static const char* WIFI_PASSWORD = "YourWiFiPassword";
```

### Tunable Parameters

```cpp
// Auto-activation threshold
const uint8_t AUTO_WIFI_AFTER_N_FAILURES = 10;

// Button timing (milliseconds)
const uint32_t SHORT_PRESS_MS = 50;
const uint32_t LONG_PRESS_MS = 3000;
const uint32_t VERY_LONG_PRESS_MS = 8000;

// Wi-Fi connection
const uint32_t WIFI_CONNECTION_TIMEOUT_MS = 30000;
const uint32_t WIFI_RETRY_INTERVAL_MS = 10000;
```

## Operational Flow

### Normal Operation (LoRa Mode)
```
1. Device boots → STATE_INIT
2. Initialize sensors → STATE_BOOT
3. Start OTAA join → STATE_JOINING
4. Join succeeds → STATE_JOINED (consecutiveJoinFails = 0)
5. Transmit data every 60s → STATE_TX
```

### Join Failure → Auto Wi-Fi Fallback
```
1. Join attempt fails → EV_JOIN_FAILED (consecutiveJoinFails++)
2. Repeats until consecutiveJoinFails >= 10
3. Auto-enable Wi-Fi fallback (wifiFallbackEnabled = true)
4. Next loop() iteration → wifiFallbackStart()
5. Stop LoRa → Connect Wi-Fi → Start HTTP server
6. Display IP on OLED
```

### Manual Wi-Fi Activation
```
1. User holds button >3s
2. buttonISR() detects long press
3. wifiFallbackEnabled = true
4. Next loop() → wifiFallbackStart()
5. Transitions to MODE_WIFI_FALLBACK
```

### Return to LoRa Mode
```
1. User holds button >8s
2. wifiFallbackStop() called
3. HTTP server stopped
4. Wi-Fi disconnected
5. LMIC_reset() + LMIC_startJoining()
6. Device reboots
```

## Safety Features

### Mutual Exclusion
- `os_runloop_once()` only called in `MODE_LORA_ACTIVE`
- `wifiServer.handleClient()` only called in `MODE_WIFI_FALLBACK`
- Explicit state transitions via `currentMode` enum

### Timing Guarantees
- No blocking delays in main loop
- LMIC scheduler runs continuously in LoRa mode
- Button ISR is non-blocking with debounce

### Error Handling
- Wi-Fi connection timeout → return to LoRa
- Wi-Fi disconnection → reconnect attempt
- Invalid sensor reads → null values in JSON

## Testing Checklist

### LoRa Mode Tests
- [ ] Device boots and joins TTN
- [ ] Successful uplinks every 60s
- [ ] Short button press triggers immediate join
- [ ] LED blinks on TX (double blink)
- [ ] LED triple blinks on successful join
- [ ] OLED shows join state and TX count

### Wi-Fi Fallback Tests
- [ ] Long button press (>3s) activates Wi-Fi
- [ ] OLED displays IP address
- [ ] HTTP `/status` endpoint returns valid JSON
- [ ] Sensor values correct or null if offline
- [ ] Very long press (>8s) exits Wi-Fi and restarts

### Auto-Activation Tests
- [ ] 10 consecutive join failures triggers Wi-Fi
- [ ] OLED shows failure count before fallback
- [ ] Wi-Fi activates without button press

### Safety Tests
- [ ] LoRa and Wi-Fi never active together
- [ ] Sensor readings work in both modes
- [ ] Button works throughout all states

## Troubleshooting

### Issue: Wi-Fi doesn't connect
**Solution**: Check `WIFI_SSID` and `WIFI_PASSWORD` in `secrets.h`

### Issue: Button doesn't respond
**Solution**: Check GPIO0 is not used for other purposes, verify pull-up

### Issue: Auto-activation happens too quickly
**Solution**: Increase `AUTO_WIFI_AFTER_N_FAILURES` (e.g., to 15 or 20)

### Issue: Can't exit Wi-Fi mode
**Solution**: Hold button for full 8+ seconds, check Serial output

### Issue: HTTP server unreachable
**Solution**: Check firewall, verify IP on OLED, test with `curl http://<IP>/status`

## Code Structure

### New Functions
- `buttonCheck()` - Button handler with press duration detection
- `handleWifiStatus()` - HTTP endpoint handler
- `wifiFallbackStart()` - Transition to Wi-Fi mode
- `wifiFallbackStop()` - Return to LoRa mode
- `wifiFallbackLoop()` - Wi-Fi server handler

### Modified Functions
- `setup()` - Added button initialization
- `loop()` - Added state machine and mode switching
- `onEvent()` - Added join failure tracking

### New State Variables
- `currentMode` - System mode enum
- `wifiFallbackEnabled` - Flag to trigger Wi-Fi activation
- `consecutiveJoinFails` - Join failure counter
- Button state tracking variables

## Performance Considerations

### Memory
- WebServer adds ~20KB to program size
- No significant RAM increase
- JSON response < 1KB

### Timing
- LMIC timing unaffected in LoRa mode
- Wi-Fi mode uses yield() for responsiveness
- No blocking operations in main loop

### Power
- Wi-Fi mode consumes more power than LoRa
- Not optimized for battery operation yet
- Future: Add sleep modes for battery efficiency

## Future Enhancements

- [ ] MQTT support for Wi-Fi mode
- [ ] WebSocket for real-time sensor updates
- [ ] OTA firmware updates via Wi-Fi
- [ ] Power optimization with Wi-Fi sleep modes
- [ ] NTP time sync for accurate timestamps
- [ ] Web UI for configuration
- [ ] Data buffering during Wi-Fi mode

## Version History

### v1.0.3 - Wi-Fi Fallback Mode
- Added button-controlled mode switching
- Implemented Wi-Fi fallback with HTTP server
- Auto-activation after 10 join failures
- Mutual exclusion state machine

### v1.0.2 - Field Test Mode
- Serial-free operation
- OLED diagnostic display
- LED visual feedback

### v1.0.1 - OTAA Join Fix
- Resolved join issues with TTN
- Pin mapping corrections

### v1.0.0 - Initial Release
- Basic LoRa OTAA functionality
- Multi-sensor support
