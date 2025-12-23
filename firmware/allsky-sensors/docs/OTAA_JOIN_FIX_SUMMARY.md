# OTAA Join Fix - Implementation Summary

**BUILD VERSION: 1.0.1 - OTAA Join Diagnostic**  
**Date: 2025-12-17**

## Changes Applied to main.cpp

### 1. Build Version Identification
- Added build version string to boot output
- Version: `1.0.1 - OTAA Join Diagnostic`
- This confirms the correct firmware is flashed

### 2. Event Decoding Improvements
Fixed "Unknown event: 20" by adding missing LMIC event cases:
- `EV_TXCANCELED` - TX was cancelled
- `EV_RXSTART` - RX window started  
- `EV_JOIN_TXCOMPLETE` - Join request transmission complete (this is likely event 20)

All join-related events now properly identified:
- `EV_JOINING` - Join process started
- `EV_JOIN_TXCOMPLETE` - Join request transmitted
- `EV_TXSTART` - Radio TX started
- `EV_JOINED` - Join accepted (success)
- `EV_JOIN_FAILED` - Join rejected (failure)

### 3. TTN Credential Debugging
Added comprehensive credential printout before `LMIC_startJoining()`:

**DevEUI** (printed in both formats):
- LSB→MSB (as stored in array)
- MSB→LSB (reversed for TTN comparison)

**AppEUI/JoinEUI** (printed in both formats):
- LSB→MSB (as stored in array)
- MSB→LSB (reversed for TTN comparison)

**AppKey** (printed as-is):
- MSB format (must match TTN exactly, NO reversal)

### 4. Expected Serial Output

```
=== AllSky Sensors - Heltec WiFi LoRa 32 V2 ===
BUILD VERSION: 1.0.1 - OTAA Join Diagnostic
Hardware: ESP32-PICO-D4 + SX1276 LoRa + OLED

=== TTN CREDENTIAL VERIFICATION ===
Compare these values with your TTN Console:

DevEUI (LSB->MSB as stored): XX-XX-XX-XX-XX-XX-XX-XX
DevEUI (MSB->LSB reversed):   XX-XX-XX-XX-XX-XX-XX-XX ← Use this if TTN shows MSB format

AppEUI (LSB->MSB as stored): XX-XX-XX-XX-XX-XX-XX-XX
AppEUI (MSB->LSB reversed):   XX-XX-XX-XX-XX-XX-XX-XX ← Use this if TTN shows MSB format

AppKey (MSB as-is):          XX-XX-XX-XX-XX-XX-XX-XX-XX-XX-XX-XX-XX-XX-XX-XX ← Must match TTN exactly

TTN Console Notes:
- DevEUI & AppEUI: Toggle 'LSB' in TTN Console, copy-paste to secrets.h
- AppKey: Use default MSB format from TTN Console
- If join fails, verify byte order and check TTN Live Data tab
===================================

[Join attempt sequence:]
EV_JOINING
EV_TXSTART
EV_JOIN_TXCOMPLETE
[Wait for response...]
EV_JOINED (success) or EV_JOIN_FAILED (retry)
```

## Validation Steps for User

### Flash and Test
1. Build and upload firmware:
   ```bash
   cd firmware/allsky-sensors
   pio run -t upload && pio device monitor
   ```

2. Verify boot shows:
   - `BUILD VERSION: 1.0.1 - OTAA Join Diagnostic`
   - Credential printout section

3. Compare printed credentials with TTN Console:
   - Open TTN Console → Applications → Devices → [Your Device]
   - Check "General settings" tab for DevEUI and AppEUI
   - Check "Overview" for AppKey
   - **Important**: Use the byte order toggle button (MSB/LSB) in TTN Console

4. Check TTN Live Data tab:
   - Should show "Join-request" packets arriving
   - If join succeeds, will show "Join-accept" response
   - If join fails, check MIC (Message Integrity Code) errors

### Common Issues & Fixes

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Event 20 appears | EV_JOIN_TXCOMPLETE | Now properly decoded |
| MIC failure in TTN | AppKey mismatch | Verify AppKey is exact MSB match |
| No packets in TTN | Wrong DevEUI | Check DevEUI byte order (try reversed) |
| Join-request ignored | Wrong AppEUI | Verify AppEUI matches (or is all zeros) |

### TTN Credential Order Quick Reference

**In secrets.h (LMIC format):**
```cpp
// DEVEUI - LSB format (little-endian)
static const uint8_t DEVEUI[8] = { 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00, 0x11 };

// APPEUI - LSB format (little-endian) 
static const uint8_t APPEUI[8] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };

// APPKEY - MSB format (big-endian, NOT reversed)
static const uint8_t APPKEY[16] = { 0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
                                     0xFE, 0xDC, 0xBA, 0x98, 0x76, 0x54, 0x32, 0x10 };
```

**In TTN Console:**
- Toggle DevEUI to **LSB** before copying → paste to DEVEUI
- Toggle AppEUI to **LSB** before copying → paste to APPEUI  
- Copy AppKey in **MSB** (default) → paste to APPKEY

## Next Steps After EV_JOINED

Once join succeeds and you see `EV_JOINED` in serial output:

1. ✅ OTAA join is working
2. ✅ Radio TX/RX confirmed
3. Next phase: First uplink validation
   - Wait 5 seconds after join
   - Device will send first sensor data packet
   - Check for `EV_TXSTART` → `EV_TXCOMPLETE`
   - Verify payload appears in TTN

## Deliverable

**Action Required from User:**
- Flash the updated firmware
- Paste complete serial output showing:
  - Build version confirmation
  - Credential printout
  - Join event sequence
- Paste TTN Live Data showing:
  - Join-request packets
  - Join-accept (if successful)
  - Any error messages (MIC failure, etc.)

This data will confirm:
- Correct firmware is running
- Credentials are configured correctly
- Join process is working (or identify exact failure point)
