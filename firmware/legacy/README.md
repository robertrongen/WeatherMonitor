# Legacy Firmware (Archived - USB Serial Sensors)

This directory contains the archived firmware for the USB serial sensor boards that were replaced by the ESP32+RFM95 LoRa sensor node.

## Status

**ARCHIVED** - These firmwares are read-only references. They were operational until Phase 4 of the LoRa migration (see [`../../docs/governance/INTEGRATED_EXECUTION_PLAN.md`](../../docs/governance/INTEGRATED_EXECUTION_PLAN.md)).

## Contents

### arduino-nano/
**Original location:** `firmware/skymonitor/`  
**Hardware:** Arduino Nano with USB serial connection to Raspberry Pi  
**Sensors:**
- Hydreon RG-9 rain sensor (analog pin A0)
- RS485 XNQJALCCY wind sensor (interrupt pin 2, pulse counting)

**Output:** JSON via serial (`/dev/ttyUSB1`) every 5 seconds
```json
{"wind_speed": <float>, "rain_intensity": <float>}
```

**Features:**
- Serial-controlled debug mode (DEBUG ON/OFF)
- 5-sample rolling average for rain readings
- Wind speed calculation from pulse count

---

### esp8266/
**Original location:** `firmware/wifi_sensors/`  
**Hardware:** ESP8266 D1 Mini with USB serial connection to Raspberry Pi  
**Sensors:**
- MLX90614 IR temperature sensor (I²C, address 0x5A)
- TSL2591 sky quality meter (I²C,address 0x29)

**Output:** JSON via serial (`/dev/ttyUSB0`) every 30 seconds
```json
{
  "sky_temperature": <float>,
  "ambient_temperature": <float>,
  "sqm_ir": <int>,
  "sqm_full": <int>,
  "sqm_visible": <int>,
  "sqm_lux": <float>
}
```

**Features:**
- Serial-controlled debug mode
- I²C device scanning on startup  
- LED status feedback (solid=healthy, blinking=sensor failure)

---

## Replacement

These firmwares were replaced by the unified ESP32+RFM95 LoRa sensor node:
- **New firmware location:** [`../allsky-sensors/`](../allsky-sensors/)
- **Hardware:** ESP32 DevKit V1 + RFM95W LoRa module
- **Communication:** LoRa to The Things Network (or Chirpstack), no USB serial
- **Data flow:** Sensor node → LoRa → TTN/Chirpstack → HTTP API → Raspberry Pi Safety Monitor

## Historical Reference

These firmwares remain in the repository for:
- Understanding sensor calibration algorithms
- Reference during troubleshooting
- Historical documentation of USB serial approach
- Potential rollback reference if needed during migration

Do not delete this directory unless the LoRa system has been operational for at least 6 months without issues.

## Migration Timeline

- **Phase 0-2:** USB serial sensors operational alongside LoRa for validation
- **Phase 3:** LoRa primary, USB deprecated but connected
- **Phase 4:** USB sensors physically removed, firmware archived here
