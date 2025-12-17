# Wi-Fi Fallback Implementation - Change Summary

## Files Modified

### 1. [`src/main.cpp`](src/main.cpp)
**Version**: 1.0.2 → 1.0.3

#### New Includes
- `#include <WiFi.h>` - ESP32 Wi-Fi library
- `#include <WebServer.h>` - HTTP server library

#### New Hardware Pins
- `#define BUTTON_PIN 0` - GPIO0 (PRG button on Heltec V2)

#### New Global Objects
- `WebServer wifiServer(80)` - HTTP server for Wi-Fi fallback mode

#### New State Machine
```cpp
enum SystemMode {
    MODE_LORA_ACTIVE,    // LoRa operational
    MODE_WIFI_FALLBACK,  // Wi-Fi operational
    MODE_SWITCHING       // Transitioning
};
```

#### New State Variables
- `currentMode` - Current system mode
- `wifiFallbackEnabled` - Wi-Fi activation flag
- `wifiConnected` - Wi-Fi connection status
- `consecutiveJoinFails` - Tracks join failures for auto-activation
- Button state tracking variables

#### New Functions Added
1. **`buttonCheck()`** - Button handler with press duration detection
   - Short press (<1s): Force LoRa join
   - Long press (>3s): Enable Wi-Fi fallback
   - Very long press (>8s): Restart device

2. **`handleWifiStatus()`** - HTTP `/status` endpoint handler
   - Returns JSON with sensor data and system status

3. **`wifiFallbackStart()`** - Activate Wi-Fi fallback mode
   - Stops LoRa cleanly
   - Connects to Wi-Fi
   - Starts HTTP server
   - Updates OLED display

4. **`wifiFallbackStop()`** - Return to LoRa mode
   - Stops HTTP server
   - Disconnects Wi-Fi
   - Restarts LoRa join

5. **`wifiFallbackLoop()`** - Wi-Fi mode loop handler
   - Handles HTTP client requests
   - Monitors Wi-Fi connection

6. **`buttonISR()`** - Button interrupt service routine
   - Handles button press/release with debounce

#### Modified Functions

**`setup()`**
- Added button initialization with interrupt
- Version updated to 1.0.3

**`loop()`**
- Added state machine for mode switching
- Button check integrated
- Mode-specific operations (LoRa vs Wi-Fi)
- Conditional `os_runloop_once()` based on mode

**`onEvent()`**
- Added join failure tracking
- Auto-activation of Wi-Fi after 10 failures
- Reset failure counter on successful join

**`fieldTestModeUpdate()`**
- Updated version strings to 1.0.3
- Added button hint on BOOT state

### 2. [`src/secrets_template.h`](src/secrets_template.h)
**New Credentials Added**

```cpp
// Wi-Fi Fallback Credentials (optional)
static const char* WIFI_SSID = "YourWiFiSSID";
static const char* WIFI_PASSWORD = "YourWiFiPassword";
```

## New Documentation

### 3. [`WIFI_FALLBACK_IMPLEMENTATION.md`](WIFI_FALLBACK_IMPLEMENTATION.md)
Complete implementation guide covering:
- Architecture and design principles
- State machine documentation
- Button controls reference
- Wi-Fi fallback features
- Configuration instructions
- Operational flow diagrams
- Testing checklist
- Troubleshooting guide

## Key Configuration Parameters

```cpp
// Auto-activation threshold
const uint8_t AUTO_WIFI_AFTER_N_FAILURES = 10;

// Button press thresholds
const uint32_t SHORT_PRESS_MS = 50;
const uint32_t LONG_PRESS_MS = 3000;
const uint32_t VERY_LONG_PRESS_MS = 8000;

// Wi-Fi connection timeouts
const uint32_t WIFI_CONNECTION_TIMEOUT_MS = 30000;
const uint32_t WIFI_RETRY_INTERVAL_MS = 10000;
```

## Compilation Requirements

No new library dependencies required - uses built-in ESP32 WiFi and WebServer libraries.

## Behavioral Changes

### LoRa Mode (Unchanged)
- Normal OTAA join and uplink behavior preserved
- 60-second transmission interval
- LED feedback on TX and join

### New Wi-Fi Fallback Behavior
1. **Manual Activation**: Long press button (>3s)
2. **Auto-Activation**: After 10 consecutive join failures
3. **Exit**: Very long press (>8s) + automatic restart

### Button Functionality (New)
- **Short Press**: Force immediate LoRa join attempt
- **Long Press**: Enable Wi-Fi fallback mode
- **Very Long Press**: Restart device and disable Wi-Fi

## HTTP API

### Endpoint: `GET /status`

**Response Format**: JSON

**Fields**:
- `uptime_seconds` - System uptime
- `lora_joined` - LoRa join status
- `last_join_attempt` - Last join timestamp
- `join_attempts` - Total join attempts
- `consecutive_fails` - Current failure streak
- `tx_count` - Successful transmissions
- `sensors` - Current sensor readings (or null)

**Example**:
```bash
curl http://192.168.1.100/status
```

## Testing Instructions

### Pre-Deployment
1. Update `src/secrets.h` with Wi-Fi credentials
2. Compile and upload firmware
3. Test button functionality
4. Verify LoRa mode works normally
5. Test Wi-Fi fallback manually
6. Verify HTTP endpoint accessibility

### Field Deployment
1. Monitor OLED for LoRa join status
2. If join fails 10 times, Wi-Fi auto-activates
3. Note IP address on OLED
4. Access `/status` endpoint to verify
5. Long press button to return to LoRa

## Backwards Compatibility

- Existing LoRa functionality unchanged
- No breaking changes to payload format
- No changes to TTN configuration required
- Button is optional - device works without interaction

## Known Limitations

1. LMIC doesn't have explicit shutdown function in some versions
   - Workaround: Stop calling `os_runloop_once()`
2. Wi-Fi mode increases power consumption
   - Not optimized for battery operation yet
3. No MQTT support yet (planned for future)
4. No OTA updates yet (planned for future)

## Migration from v1.0.2

1. Update `src/secrets.h` with Wi-Fi credentials
2. Recompile and upload firmware
3. No TTN reconfiguration needed
4. Test button functionality after deployment

## Rollback Procedure

If issues occur, revert to v1.0.2:
1. Checkout previous version of `main.cpp`
2. Remove Wi-Fi includes and code
3. Recompile and upload
4. LoRa functionality will be restored

## Future Enhancements

- MQTT support for Wi-Fi mode
- OTA firmware updates
- WebSocket for real-time data
- Power optimization for battery operation
- NTP time synchronization
- Web-based configuration UI
