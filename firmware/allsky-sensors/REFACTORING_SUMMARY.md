# AllSky Sensors Firmware Refactoring Summary

**Date:** 2025-12-21  
**Version:** 1.0.3 - Wi-Fi Fallback Mode  
**Type:** Pure Code Reorganization (No Behavioral Changes)

## Overview

The AllSky Sensors firmware has been reorganized from a monolithic 1329-line [`main.cpp`](src/main.cpp:1) into logical modules for improved maintainability, debuggability, and future development.

## Critical Constraint: NO BEHAVIORAL CHANGES

⚠️ **This refactoring is purely mechanical:**
- Same globals, same state, same side effects
- Same timing, logic, and state transitions
- Wi-Fi fallback isolation and LMIC gating remain intact
- No "improvements" or logic changes were made

## New Module Structure

```
firmware/allsky-sensors/src/
├── main.cpp                    # Setup + loop orchestration (267 lines)
├── system_state.h / .cpp       # SystemMode enum, currentMode, transitions
├── button.h / .cpp             # GPIO0 ISR, debounce, press classification
├── display.h / .cpp            # OLED init, update, sleep/wake
├── lora.h / .cpp               # LMIC init, onEvent(), send job, stopLoRa()
├── wifi_fallback.h / .cpp      # Wi-Fi fallback start/stop, HTTP server
├── sensors.h / .cpp            # Sensor state + readouts (no transport logic)
└── diagnostics.h / .cpp        # Logging helpers, field test counters
```

## Module Ownership & Responsibilities

### 1. [`system_state.h`](src/system_state.h:1) / [`system_state.cpp`](src/system_state.cpp:1)
**Purpose:** Central state machine for mode switching

**Exports:**
- `SystemMode` enum (MODE_LORA_ACTIVE, MODE_WIFI_FALLBACK, MODE_SWITCHING)
- `currentMode` - current system mode
- `wifiFallbackEnabled`, `wifiConnected` - Wi-Fi state
- `consecutiveCycleFails` - failure counter for auto Wi-Fi activation
- `LoRaState` enum - for field test display
- `currentLoRaState`, `joinAttempts`, `txCount` - LoRa diagnostics

**Key Constraint:** No LMIC calls, no Wi-Fi calls - pure state storage

---

### 2. [`button.h`](src/button.h:1) / [`button.cpp`](src/button.cpp:1)
**Purpose:** Button input handling on GPIO0

**Exports:**
- `buttonInit()` - initialize GPIO and ISR
- `buttonCheck()` - process button presses (called from loop)
- `buttonISR()` - interrupt service routine

**Behavior:**
- Short press (50ms): Force LoRa join (if in LoRa mode)
- Long press (3s): Enable Wi-Fi fallback
- Very long press (8s): Restart device

**Dependencies:** Calls [`displayUpdate()`](src/display.cpp:36), checks [`currentMode`](src/system_state.cpp:10), uses [`LMIC_startJoining()`](src/lora.cpp:378)

---

### 3. [`display.h`](src/display.h:1) / [`display.cpp`](src/display.cpp:1)
**Purpose:** OLED display management

**Exports:**
- `displayInit()` - hardware init, turn on display
- `displayUpdate(line1, line2, line3, line4)` - update content
- `displaySleep()` / `displayWake()` - power management
- `displayCheck()` - auto-timeout handler

**Hardware:**
- OLED_SDA=4, OLED_SCL=15, OLED_RST=16, OLED_ADDR=0x3C
- SSD1306Wire 128x64 OLED on internal I²C bus
- 10-second auto-timeout

**Key Constraint:** No dependencies on other modules (pure display logic)

---

### 4. [`sensors.h`](src/sensors.h:1) / [`sensors.cpp`](src/sensors.cpp:1)
**Purpose:** Sensor I/O (no transport logic)

**Exports:**
- `SensorData` struct - all sensor readings + validity flags
- `sensorData` - global sensor state
- `sensorsInit()` - initialize all sensors
- `sensorsRead()` - acquire sensor data
- `sensorsPrint()` - log to Serial

**Hardware:**
- External I²C bus: GPIO21 (SDA), GPIO22 (SCL)
- MLX90614 IR temperature (0x5A)
- TSL2591 Sky Quality Meter (0x29)
- Rain sensor: GPIO36 (ADC)
- Wind sensor: GPIO32 (interrupt)

**Key Constraint:** No LoRa or Wi-Fi calls - pure sensor acquisition

---

### 5. [`lora.h`](src/lora.h:1) / [`lora.cpp`](src/lora.cpp:1)
**Purpose:** LoRaWAN transport layer

**Exports:**
- `loraInit()` - SPI + LMIC initialization
- `onEvent(ev_t ev)` - LMIC event handler
- `do_send(osjob_t* j)` - read sensors, encode, transmit
- `encodePayload(buffer)` - binary payload encoder
- `stopLoRa()` - quiesce LMIC for Wi-Fi fallback
- `joined`, `transmitting`, `nextTransmissionTime` - LoRa state
- `os_getArtEui()`, `os_getDevEui()`, `os_getDevKey()` - OTAA callbacks

**Key Behaviors:**
- EV_JOINED: set [`joined=true`](src/lora.cpp:54), reset [`consecutiveCycleFails`](src/system_state.cpp:20)
- EV_TXCOMPLETE: increment [`txCount`](src/system_state.cpp:29), capture RSSI/SNR
- EV_TXCANCELED: increment [`consecutiveCycleFails`](src/system_state.cpp:20), trigger auto Wi-Fi fallback
- TX timeout (120s): tracked in [`main.cpp loop()`](src/main.cpp:187)

**Hardware:**
- LoRa pins: CS=18, RST=14, DIO0=26, DIO1=35, DIO2=34
- SPI: SCK=5, MISO=19, MOSI=27

**Key Constraint:** ONLY called when [`currentMode == MODE_LORA_ACTIVE`](src/system_state.cpp:10)

---

### 6. [`wifi_fallback.h`](src/wifi_fallback.h:1) / [`wifi_fallback.cpp`](src/wifi_fallback.cpp:1)
**Purpose:** Wi-Fi HTTP server fallback mode

**Exports:**
- `wifiFallbackStart()` - stop LoRa, connect Wi-Fi, start HTTP server
- `wifiFallbackStop()` - stop Wi-Fi, restart LoRa
- `wifiFallbackLoop()` - handle HTTP requests, check connection
- `handleWifiStatus()` - JSON status endpoint (`/status`)
- `wifiServer` - WebServer instance on port 80

**Key Behaviors:**
- Calls [`stopLoRa()`](src/lora.cpp:432) to quiesce LMIC
- Sets [`currentMode = MODE_SWITCHING`](src/system_state.cpp:10) during transition
- HTTP endpoint returns sensor data + LoRa diagnostics
- Auto-reconnects if Wi-Fi drops

**Key Constraint:** LMIC is fully stopped during Wi-Fi mode

---

### 7. [`diagnostics.h`](src/diagnostics.h:1) / [`diagnostics.cpp`](src/diagnostics.cpp:1)
**Purpose:** Field test mode display + LED indicators

**Exports:**
- `ledInit()`, `ledBlink()`, `ledBlinkTx()`, `ledBlinkJoined()`
- `fieldTestModeUpdate()` - 2Hz non-blocking OLED refresh
- `fieldTestModeSetState(LoRaState)` - update display state
- `loopCount`, `lastLoopLog` - loop health diagnostics

**Display States:**
- STATE_INIT, STATE_BOOT, STATE_JOINING, STATE_JOIN_TX
- STATE_JOINED, STATE_JOIN_FAILED, STATE_TX, STATE_LINK_DEAD

**Hardware:**
- Status LED: GPIO25

**Key Behavior:** Calls [`displayUpdate()`](src/display.cpp:36) with formatted status lines

---

### 8. [`main.cpp`](src/main.cpp:1) (Refactored)
**Purpose:** Orchestration only (setup + loop)

**`setup()` Flow:**
1. Serial init
2. [`ledInit()`](src/diagnostics.cpp:33)
3. [`buttonInit()`](src/button.cpp:52)
4. [`displayInit()`](src/display.cpp:24)
5. [`sensorsInit()`](src/sensors.cpp:41)
6. TTN credential verification (print to Serial)
7. [`loraInit()`](src/lora.cpp:370)

**`loop()` Flow:**
```cpp
// State machine
if (wifiFallbackEnabled && currentMode == MODE_LORA_ACTIVE)
    wifiFallbackStart();

buttonCheck();

// Mode-specific operations
if (currentMode == MODE_LORA_ACTIVE) {
    os_runloop_once();  // LMIC scheduler
    fieldTestModeUpdate();
    // TX timeout tracking
    // Transmission scheduling
} else if (currentMode == MODE_WIFI_FALLBACK) {
    wifiFallbackLoop();
    // Periodic sensor reads (60s)
}

displayCheck();
```

**Key Constraint:** LMIC only serviced when [`currentMode == MODE_LORA_ACTIVE`](src/system_state.cpp:10)

---

## Module Dependencies

```
main.cpp
  ├─ system_state     (state vars)
  ├─ button           (buttonCheck)
  ├─ display          (displayInit, displayCheck)
  ├─ lora             (loraInit, do_send, os_runloop_once)
  ├─ wifi_fallback    (wifiFallbackStart, wifiFallbackLoop)
  ├─ sensors          (sensorsInit, sensorsRead)
  └─ diagnostics      (ledInit, fieldTestModeUpdate)

button.cpp
  ├─ system_state     (currentMode, wifiFallbackEnabled)
  ├─ display          (displayUpdate)
  └─ lora             (joined, LMIC_startJoining)

lora.cpp
  ├─ system_state     (joined, txCount, etc.)
  ├─ display          (displayWake)
  ├─ sensors          (sensorsRead, sensorData)
  └─ diagnostics      (fieldTestModeSetState, ledBlinkJoined)

wifi_fallback.cpp
  ├─ system_state     (currentMode, wifiConnected, etc.)
  ├─ display          (displayUpdate)
  ├─ sensors          (sensorData)
  └─ lora             (joined, stopLoRa, LMIC_reset)

diagnostics.cpp
  ├─ system_state     (currentLoRaState, joinAttempts, txCount)
  ├─ display          (displayUpdate)
  └─ sensors          (sensorData.rssi)

sensors.cpp       (no external dependencies - pure sensor I/O)
display.cpp       (no external dependencies - pure OLED I/O)
system_state.cpp  (no external dependencies - pure state storage)
```

---

## Globals & State Management

### Principle: Explicit Ownership
- Globals moved next to the module that owns them
- Shared state exposed via headers (e.g. [`currentMode`](src/system_state.cpp:10) in system_state)
- No hidden dependencies

### Example: LoRa State
**Before:** All in [`main.cpp`](src/main.cpp:1)  
**After:**
- [`system_state.cpp`](src/system_state.cpp:1): `currentMode`, `joined`, `txCount`, `joinAttempts`
- [`lora.cpp`](src/lora.cpp:1): `sendjob`, `transmitting`, `nextTransmissionTime`
- [`sensors.cpp`](src/sensors.cpp:1): `sensorData`

---

## Assurance: Behavior Unchanged

### 1. **State Transitions**
- Mode switching logic preserved exactly (MODE_LORA_ACTIVE ↔ MODE_WIFI_FALLBACK)
- Button thresholds unchanged (50ms, 3s, 8s)
- Auto Wi-Fi activation after 10 cycle failures - **same threshold**

### 2. **LMIC Integration**
- [`os_runloop_once()`](src/main.cpp:187) only called when [`currentMode == MODE_LORA_ACTIVE`](src/system_state.cpp:10) - **same isolation**
- [`stopLoRa()`](src/lora.cpp:432) calls [`os_clearCallback(&sendjob)`](src/lora.cpp:436) - **same cleanup**
- Event handler logic preserved exactly

### 3. **Wi-Fi Fallback**
- Same connection sequence: stop LoRa → connect Wi-Fi → start HTTP server
- Same 30-second connection timeout
- Same JSON endpoint structure

### 4. **Timing**
- Display refresh: 500ms (2Hz) - **unchanged**
- TX interval: 60 seconds - **unchanged**
- TX timeout: 120 seconds - **unchanged**
- Button debounce: 50ms - **unchanged**

### 5. **Sensor Acquisition**
- Same I2C bus separation (display vs sensors)
- Same validation ranges
- Same averaging (rain: 10 samples)

---

## Testing Checklist

Before deployment, verify:

- [ ] Code compiles (PlatformIO: `pio run`)
- [ ] LoRa join succeeds (check field test display)
- [ ] Button short press triggers join attempt
- [ ] Button long press (3s) enables Wi-Fi fallback
- [ ] Wi-Fi fallback shows IP on display
- [ ] HTTP `/status` endpoint returns valid JSON
- [ ] Button very long press (8s) restarts device
- [ ] 10 consecutive TX failures trigger auto Wi-Fi fallback
- [ ] Display auto-sleeps after 10 seconds
- [ ] Sensor readings match pre-refactor values

---

## Future Benefits

### 1. **Easier Debugging**
- Isolate issues to specific modules (e.g. "LoRa join fails" → check [`lora.cpp`](src/lora.cpp:1))
- ChatGPT can focus on one module at a time

### 2. **Safer Changes**
- Modify display logic without touching LoRa
- Add new sensors without affecting Wi-Fi fallback

### 3. **Clear Interfaces**
- Headers document what each module exposes
- Avoid circular dependencies

### 4. **Testability**
- Mock [`sensorsRead()`](src/sensors.cpp:99) for unit tests
- Test state transitions in [`system_state.cpp`](src/system_state.cpp:1) independently

---

## What Was NOT Changed

❌ No code style improvements  
❌ No variable renaming (except for extraction)  
❌ No logic inlining or abstraction  
❌ No new features  
❌ No "while we're here" fixes  

---

## Compilation

To verify the refactoring:

```bash
cd firmware/allsky-sensors
pio run
```

Expected output: `SUCCESS` with same binary size (±100 bytes due to linker)

---

## File Sizes (Approximate)

| File | Lines | Purpose |
|------|-------|---------|
| [`main.cpp`](src/main.cpp:1) | 267 | Setup + loop orchestration |
| [`system_state.h/.cpp`](src/system_state.h:1) | 40 | State machine definitions |
| [`button.h/.cpp`](src/button.h:1) | 110 | Button input handling |
| [`display.h/.cpp`](src/display.h:1) | 90 | OLED display management |
| [`lora.h/.cpp`](src/lora.h:1) | 440 | LoRaWAN transport layer |
| [`wifi_fallback.h/.cpp`](src/wifi_fallback.h:1) | 210 | Wi-Fi fallback mode |
| [`sensors.h/.cpp`](src/sensors.h:1) | 240 | Sensor acquisition |
| [`diagnostics.h/.cpp`](src/diagnostics.h:1) | 160 | Field test display + LEDs |

**Total:** ~1547 lines (was 1329 lines in monolithic main.cpp)  
**Increase:** +18% due to headers, but each file is now <450 lines

---

## Questions & Support

For issues or questions about this refactoring:
1. Check module headers for interface documentation
2. Review original [`main.cpp`](src/main.cpp:1) in git history (`git log -p`)
3. Compare behavior using field test mode display

**Critical Rule:** If runtime behavior differs from pre-refactor, **revert immediately** and investigate.

---

**END OF REFACTORING SUMMARY**
