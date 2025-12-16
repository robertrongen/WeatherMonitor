# Legacy Sensor Node Documentation

**Status:** ARCHIVED  
**Date:** 2025-12-16

This directory contains hardware documentation for superseded sensor node designs. These documents are preserved for reference, troubleshooting, and historical context.

---

## Current Baseline (2025-12-16)

**Active Hardware:** Heltec WiFi LoRa 32 V2 (Board #4)  
**Documentation:** [`../board-esp32-lora-display/`](../board-esp32-lora-display/)

- [`ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md`](../board-esp32-lora-display/ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md) - Board specifications and architecture rationale
- [`HARDWARE_WIRING_ESP32_LORA_DISPLAY.md`](../board-esp32-lora-display/HARDWARE_WIRING_ESP32_LORA_DISPLAY.md) - Complete sensor wiring guide with pin definitions

---

## Archived Platforms

### 1. ESP32 DevKit V1 + External RFM95 Module

**File:** [`HARDWARE_WIRING_STRATEGY.md`](HARDWARE_WIRING_STRATEGY.md)  
**Status:** Superseded by integrated board (2025-12-16)  
**Reason for Archival:** Heltec WiFi LoRa 32 V2 provides integrated LoRa radio, eliminating external SPI wiring

**Key Differences from Current Baseline:**
- External RFM95 module requires 8 SPI wires (SCK, MISO, MOSI, CS, RST, DIO0, DIO1, power/ground)
- LoRa SPI pins: GPIO18 (SCK), GPIO19 (MISO), GPIO23 (MOSI), GPIO2 (CS), GPIO4 (DIO0), GPIO5 (DIO1)
- No integrated display (optional external OLED on separate I²C bus)
- Requires breadboard or perfboard assembly
- Higher assembly complexity and failure risk

**When to Use This Reference:**
- Custom builds with specific ESP32 DevKit requirements
- Troubleshooting issues with external RFM95 modules
- Understanding migration path from legacy hardware
- Educational purposes (learning LoRa SPI interfacing)

**Migration Path:**  
See [`ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md`](../board-esp32-lora-display/ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md) Section "Migration from Legacy Hardware" for step-by-step conversion guide.

---

### 2. Arduino Nano + ESP8266 D1 Mini (USB Serial)

**File:** [`ARCHITECTURE_PLAN_V1.md`](ARCHITECTURE_PLAN_V1.md)  
**Status:** Fully deprecated, replaced by LoRa architecture (2025-12-15)  
**Reason for Archival:** USB serial architecture replaced by wireless LoRa transmission

**Key Differences from Current Baseline:**
- Two separate boards: Arduino Nano (rain + wind) and ESP8266 (IR temp + sky quality)
- USB serial communication to Raspberry Pi (not wireless)
- No remote deployment capability (tethered to Raspberry Pi)
- Separate firmware codebases for each board

**Original Configuration:**
```
Arduino Nano (firmware/legacy/arduino-nano/skymonitor.ino):
  - Hydreon RG-9 rain sensor (analog pin A0)
  - RS485 wind sensor (digital pin 2, interrupt)
  - USB serial output: {"wind_speed": X, "rain_intensity": Y}

ESP8266 D1 Mini (firmware/legacy/esp8266/wifi_sensors.ino):
  - MLX90614 IR temperature sensor (I²C 0x5A)
  - TSL2591 sky quality meter (I²C 0x29)
  - USB serial output: {"sky_temperature": X, "ambient_temperature": Y, ...}
```

**When to Use This Reference:**
- Historical context for original system design
- Understanding USB serial protocol if needed for debugging
- Recovering from complete system failure (emergency fallback)

**Migration Path:**  
This architecture was completely replaced by LoRa-based design. No direct migration path exists; requires full hardware replacement.

---

## Comparison Matrix

| Feature | Arduino + ESP8266 (USB) | ESP32 DevKit + RFM95 | Heltec WiFi LoRa 32 V2 |
|---------|------------------------|----------------------|------------------------|
| **Boards** | 2 (Nano + ESP8266) | 2 (DevKit + RFM95 module) | 1 (integrated) |
| **Communication** | USB serial | LoRa wireless | LoRa wireless |
| **Range** | <5m (USB cable) | <5km (depends on SF) | <5km (depends on SF) |
| **Wiring Complexity** | Medium (2 USB cables) | High (8 SPI wires) | **Low (sensors only)** |
| **Enclosure Size** | Large (2 boards) | Medium (2 boards) | **Compact (1 board)** |
| **Diagnostics** | Serial monitor | Serial monitor | **Built-in OLED** |
| **Power** | 2x USB 5V | USB 5V + discrete | **USB 5V OR LiPo** |
| **Failure Points** | 3 (2 boards + USB hub) | 3 (2 boards + wiring) | **1 (single board)** |
| **Status** | DEPRECATED | ARCHIVED | **ACTIVE** |

---

##Documentation Status

| Document | Original Date | Archived Date | Reason |
|----------|--------------|---------------|--------|
| [`HARDWARE_WIRING_STRATEGY.md`](HARDWARE_WIRING_STRATEGY.md) | 2025-12-15 | 2025-12-16 | External RFM95 superseded by integrated board |
| [`ARCHITECTURE_PLAN_V1.md`](ARCHITECTURE_PLAN_V1.md) | 2025-12-15 | 2025-12-16 | USB serial superseded by LoRa wireless |

---

## Related Documentation

- **Current Architecture:** [`../board-esp32-lora-display/ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md`](../board-esp32-lora-display/ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md)  
- **Current Wiring:** [`../board-esp32-lora-display/HARDWARE_WIRING_ESP32_LORA_DISPLAY.md`](../board-esp32-lora-display/HARDWARE_WIRING_ESP32_LORA_DISPLAY.md)  
- **System Architecture:** [`../ARCHITECTURE_PLAN_V2.md`](../ARCHITECTURE_PLAN_V2.md)  
- **Firmware:** [`../../firmware/allsky-sensors/README.md`](../../firmware/allsky-sensors/README.md)

---

**For New Implementations:** Always use the current baseline (Heltec WiFi LoRa 32 V2). These legacy documents are for reference only.
