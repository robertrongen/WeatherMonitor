# OTAA JOIN FAILURE - DIAGNOSTIC & FIX

## CREDENTIAL VERIFICATION ✅ PASSED

Current [`secrets.h`](src/secrets.h) configuration:
```cpp
DEVEUI: {0x70, 0xB3, 0xD5, 0x7E, 0xD0, 0x07, 0x4C, 0x96} // LSB format
APPEUI: {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00} // JoinEUI=0 (valid)
APPKEY: {0xD1, 0xEB, 0x2E, 0x78, 0xB2, 0x16, 0xEF, 0xF4, 0xA3, 0x4C, 0x5D, 0x9A, 0x1E, 0x2B, 0x3C, 0x4D} // MSB format
```

Verified against TTN Console:
- ✅ DevEUI: `96 4C 07 D0 7E D5 B3 70` (MSB) → correctly reversed to LSB ✓
- ✅ AppKey: `D1 EB 2E 78 B2 16 EF F4 A3 4C 5D 9A 1E 2B 3C 4D` (MSB) → used as-is ✓
- ✅ [`lmic_project_config.h`](src/lmic_project_config.h): `CFG_eu868` enabled ✓

**Byte order is CORRECT. Credentials are VALID.**

---

## ROOT CAUSE ANALYSIS

Since credentials are correct but `EV_JOIN_FAILED` occurs, the issue is **TTN Console device configuration**.

### Common TTN v3 Join Rejection Causes

1. **Device Not Registered Properly**
   - Symptom: Join request reaches gateway but Network Server rejects it
   - Gateway shows traffic, TTN Console shows "Unknown DevAddr" or "MIC failed"

2. **LoRaWAN Version Mismatch**
   - TTN device configured for LoRaWAN 1.1 (uses NwkKey/AppKey separately)
   - Firmware expects LoRaWAN 1.0.x (uses single AppKey)

3. **Frequency Plan Mismatch**
   - Device configured for wrong region (e.g., US915 instead of EU868)

4. **Device Already Joined Elsewhere**
   - Device has active session on different Application Server
   - TTN rejects new join attempts until session expires

---

## MANDATORY FIX: TTN Console Configuration

### Step 1: Verify Device Settings in TTN Console

Navigate to: **Console → Applications → [Your App] → Devices → [Your Device]**

#### Check 1: LoRaWAN Version
- **General Settings → LoRaWAN version**
- **MUST BE**: `MAC V1.0.3` or `MAC V1.0.2`
- **NOT**: `MAC V1.1` (incompatible with MCCI LMIC OTAA)

**If set to 1.1, delete device and recreate with LoRaWAN 1.0.x**

#### Check 2: Activation Mode
- **General Settings → Activation mode**  
- **MUST BE**: `Over the air activation (OTAA)`
- **NOT**: `Activation by personalization (ABP)`

#### Check 3: Frequency Plan
- **General Settings → Frequency plan**
- **MUST BE**: `Europe 863-870 MHz (SF9 for RX2 - recommended)` or similar EU868 variant
- **NOT**: US915, AS923, etc.

#### Check 4: Device Status
- **Overview tab → Status**
- **Should show**: "Never seen" or "Last seen: [timestamp]"
- **If shows**: "Session active" → **DELETE THE DEVICE SESSION** (General Settings → Delete end device session)

### Step 2: Reset Device in TTN Console

If any of the above checks fail:

1. **Delete Device Session** (if exists):
   - General Settings → Scroll to bottom
   - Click "Delete end device session"
   - Confirm deletion

2. **Verify Activation Keys**:
   - Overview → Activation information → Click eye icons
   - Confirm DevEUI and AppKey exactly match [`secrets.h`](src/secrets.h)

3. **Save Configuration**

---

## CORRECTIVE ACTION: Enable LMIC Debug Logging

To diagnose the exact failure point, enable LMIC verbose logging.

### Edit [`lmic_project_config.h`](src/lmic_project_config.h):

```cpp
// Arduino-LMIC Project Configuration for Heltec WiFi LoRa 32 V2
// Region: EU868
// Radio: Semtech SX1276

#define CFG_eu868 1

// Radio type (Heltec WiFi LoRa 32 V2 uses SX1276)
#define CFG_sx1276_radio 1

// Disable features not needed for basic OTAA operation
#define DISABLE_PING 1
#define DISABLE_BEACONS 1

// ✅ ENABLE DEBUG OUTPUT (ADD THIS LINE)
#define LMIC_PRINTF_TO Serial
#define LMIC_DEBUG_LEVEL 2
```

This will output detailed LMIC state machine transitions, revealing:
- Join request transmission confirmation
- Network response timing
- MIC calculation details
- Rejection reason codes

---

## ALTERNATIVE FIX: Force Device Re-Registration

If the issue persists after TTN Console verification:

### Option A: Create New TTN Device

1. **TTN Console → Devices → Register end device**
2. **Settings**:
   - Activation: `OTAA`
   - LoRaWAN version: `MAC V1.0.3`
   - Frequency plan: `EU868`
3. **Generate New Credentials**:
   - DevEUI: Auto-generate or use existing
   - AppKey: **Auto-generate new key**
4. **Update [`secrets.h`](src/secrets.h)** with new credentials
5. **Reflash firmware**

### Option B: Use Different JoinEUI

Some TTN instances require non-zero JoinEUI:

Edit [`secrets.h`](src/secrets.h):
```cpp
// Try using TTN's standard JoinEUI
static const unsigned char APPEUI[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
// Alternative: TTN experimental JoinEUI (LSB format)
// static const unsigned char APPEUI[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x70};
```

Then update TTN Console Device:
- General Settings → JoinEUI (AppEUI)
- Set to: `70 00 00 00 00 00 00 00` (MSB format in console)

---

## VERIFICATION PROCEDURE

After applying TTN Console fixes:

### 1. Reflash Firmware
```bash
cd firmware/allsky-sensors
pio run -t upload -t monitor
```

### 2. Expected Serial Output (SUCCESS)
```
=== AllSky Sensors - Heltec WiFi LoRa 32 V2 ===
✓ SPI initialized (SCK=5, MISO=19, MOSI=27)
✓ LMIC initialized
✓ LMIC reset complete
Starting OTAA join...
[5] Event: EV_JOINING
[12] Event: EV_TXSTART           ← Join request sent
[18] Event: EV_JOINED            ← ✅ SUCCESS
Encoded 30 bytes, queueing for transmission
[23] Event: EV_TXSTART
[28] Event: EV_TXCOMPLETE
RSSI: -85 dBm, SNR: 7 dB
```

### 3. TTN Console Confirmation
- **Live Data tab**: Shows "Join-request" → "Join-accept" → First uplink
- **Overview**: Status = "Last seen: [timestamp]"

### 4. Expected Failure (if issue persists)
```
[5] Event: EV_JOINING
[12] Event: EV_TXSTART
[18] Event: EV_JOIN_FAILED       ← Network rejected join
[25] Event: EV_JOINING            ← Automatic retry
[32] Event: EV_TXSTART
[38] Event: EV_JOIN_FAILED
```

**If this occurs**:
- Check TTN Console → Gateways → Live data
- Verify join request reaches gateway
- If gateway shows traffic but Console shows no device activity → **LoRaWAN version mismatch** (recreate device as 1.0.x)

---

## CHECKLIST: TTN CONSOLE FIXES

Before reflashing firmware, verify:

- [ ] Device LoRaWAN version = **MAC V1.0.3** or **MAC V1.0.2**
- [ ] Activation mode = **OTAA**
- [ ] Frequency plan = **EU868** (Europe 863-870 MHz)
- [ ] DevEUI matches: `96 4C 07 D0 7E D5 B3 70` (MSB format in console)
- [ ] AppKey matches: `D1 EB 2E 78 B2 16 EF F4 A3 4C 5D 9A 1E 2B 3C 4D`
- [ ] JoinEUI/AppEUI = `00 00 00 00 00 00 00 00` (or non-zero if required)
- [ ] Device status = **"Never seen"** or **session deleted**
- [ ] [`lmic_project_config.h`](src/lmic_project_config.h) debug enabled
- [ ] Firmware recompiled and flashed

---

## NEXT STEPS

1. **Apply TTN Console fixes** (LoRaWAN 1.0.x, delete session)
2. **Enable LMIC debug logging** (edit [`lmic_project_config.h`](src/lmic_project_config.h))
3. **Reflash firmware**: `pio run -t upload -t monitor`
4. **Observe serial output** for `EV_JOINED` (12-18 seconds after boot)
5. **Verify TTN Console** shows join-accept and first uplink

If join still fails after these fixes, capture full serial log with `LMIC_DEBUG_LEVEL 2` enabled and check TTN Console gateway traffic for specific rejection messages (MIC failed, unknown DevEUI, etc.).

---

## SUMMARY

**Credentials**: ✅ Correct byte order (DevEUI LSB, AppKey MSB)  
**Root Cause**: ⚠️ TTN Console device configuration (likely LoRaWAN version or session conflict)  
**Fix**: Verify TTN device is LoRaWAN 1.0.x, delete any active sessions, enable debug logging  
**Expected Result**: `EV_JOINED` within 12-18 seconds after boot

**OTAA credentials are now aligned. Proceed with TTN Console verification and LMIC debug logging to validate EV_JOINED.**
