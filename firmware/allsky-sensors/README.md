# AllSky Sensors - Heltec WiFi LoRa 32 V2 Sensor Node

**Status:** Pin Definitions Updated for Board #4
**Hardware:** Heltec WiFi LoRa 32 V2 (integrated SX1276 LoRa + OLED display)
**Backend:** The Things Network (TTN) v3 or Chirpstack

## Overview

Standalone LoRa sensor node transmitting environmental data to external backend using **Heltec WiFi LoRa 32 V2** with integrated SX1276 LoRa radio and 0.96" OLED display.

### Integrated Components

- **LoRa Radio:** SX1276 (868 MHz EU / 915 MHz US) - **PRE-WIRED INTERNALLY**
- **Display:** 0.96" OLED (SSD1306, I²C 0x3C) - **PRE-WIRED INTERNALLY**
- **Antenna:** U.FL connector (external antenna required)

**Internal LoRa Connections (factory-integrated):**
- SPI: GPIO5 (SCK), GPIO19 (MISO), GPIO27 (MOSI)
- Control: GPIO18 (CS), GPIO14 (RST), GPIO26 (DIO0), GPIO33 (DIO1)

**Internal Display Connections (factory-integrated):**
- I²C: GPIO4 (SDA), GPIO15 (SCL), GPIO16 (RST)
- Address: 0x3C

### External Sensors

1. **RG-9 Rain Sensor** - Analog input (GPIO36 with voltage divider 5.1kΩ/10kΩ)
2. **RS485 Wind Sensor** - Pulse mode (GPIO34 + optocoupler) OR RS485 mode (UART2 GPIO17/23)
3. **MLX90614 IR Temperature** - I²C (0x5A) on **GPIO21 (SDA) / GPIO22 (SCL)**
4. **TSL2591 Sky Quality Meter** - I²C (0x29) on **GPIO21 (SDA) / GPIO22 (SCL)**

**⚠️ IMPORTANT:** External sensors use a **separate I²C bus** (GPIO21/22) from the display bus (GPIO4/15) for stability and isolation.

### LoRa Configuration

- **Frequency:** 868 MHz (EU) / 915 MHz (US)
- **Radio:** SX1276 (integrated on board)
- **Network:** LoRaWAN OTAA (Over-The-Air Activation)
- **Transmission Interval:** 30-60 seconds
- **Antenna:** External 868/915 MHz antenna required (U.FL connector)

## File Structure

- `platformio.ini` - PlatformIO project configuration
- `src/main.cpp` - Main firmware with LoRaWAN functionality
- `src/secrets_template.h` - TTN credentials template
- `include/` - Header files
- `lib/` - Custom libraries if needed
- `test/` - Firmware unit tests

## Firmware Status

**Status:** ✅ **COMPLETE - Full Sensor Integration Ready for Deployment**

**Firmware Implementation:**
- ✅ Heltec WiFi LoRa 32 V2 pin mappings (integrated SX1276 LoRa)
- ✅ OLED display support (0.96" SSD1306 on GPIO4/15)
- ✅ Sensor I²C bus isolation (separate buses for display and sensors)
- ✅ MLX90614 IR temperature sensor (GPIO21/22 I²C)
- ✅ TSL2591 sky quality meter (GPIO21/22 I²C)
- ✅ RG-9 rain sensor (analog GPIO36, voltage divider)
- ✅ Wind sensor (pulse mode GPIO34, interrupt-driven)
- ✅ LoRaWAN OTAA join and transmission (TTN v3 compatible)
- ✅ Binary payload encoding (30 bytes, all sensors + diagnostics)
- ✅ Signal quality reporting (RSSI, SNR)
- ✅ Display power management (10-second timeout)
- ✅ Periodic transmission (60-second interval)

### Setup Instructions

1. **Install PlatformIO:**
   ```bash
   pip install platformio
   ```

2. **Configure TTN Credentials:**
   ```bash
   cd firmware/allsky-sensors
   cp src/secrets_template.h src/secrets.h
   ```
   
   Edit `src/secrets.h` with your TTN device credentials from:
   - TTN Console: https://console.thethingsnetwork.org/
   - Applications > [Your App] > Devices > [Your Device] > Overview

3. **Build and Upload:**
   ```bash
   pio device list                    # Find ESP32 port
   pio run                           # Compile firmware
   pio device monitor                # Open serial monitor (115200 baud)
   pio run --target upload           # Upload to ESP32
   ```

### Expected Behavior

**Serial Monitor Output:**
```
=== AllSky Sensors - LoRaWAN Firmware (Step 1) ===
ESP32 DevKit V1 + RFM95W LoRa Module
Boot completed at XXX ms
TTN credentials detected - starting LMIC initialization
Initializing LMIC...
LMIC initialization complete
Starting OTAA join procedure...
Event: 14  (EV_JOINING)
EV_JOINING
Event: 15  (EV_JOINED)
EV_JOINED
Starting data transmission...
Packet queued for transmission
Event: 27  (EV_TXCOMPLETE)
EV_TXCOMPLETE
=== Step 1 Complete: Join and Test Uplink Successful ===
Device joined TTN and transmitted test payload
Stopping firmware - Step 1 verification complete
```

**TTN Console Verification:**
- Device shows "Last seen" status
- Data tab shows received uplink packet with 3 bytes: `01 02 03`

## Build System

This firmware uses **PlatformIO**, not Arduino IDE:
```bash
# Install dependencies (automatically handled by platformio.ini)
# Build and upload
pio run
pio run --target upload

# Monitor serial output
pio device monitor
```

## Reference Design

Based on [`stoflamp` project](c:/github/stoflamp/src/main.cpp):
- RFM95 SPI wiring (GPIO 2,4,5,18,19,23)
- LMIC initialization patterns
- FreeRTOS semaphore for bus arbitration

## Implementation Phases

See [`../../docs/governance/INTEGRATED_EXECUTION_PLAN.md`](../../docs/governance/INTEGRATED_EXECUTION_PLAN.md) Section 3 for step-by-step firmware plan.

## Hardware Wiring

See [`../../docs/architecture/board-esp32-lora-display/HARDWARE_WIRING_ESP32_LORA_DISPLAY.md`](../../docs/architecture/board-esp32-lora-display/HARDWARE_WIRING_ESP32_LORA_DISPLAY.md) for complete sensor wiring guide with pin assignments, voltage dividers, and circuit diagrams.

**Legacy wiring** (ESP32 DevKit + external RFM95) has been moved to [`../../docs/architecture/legacy/HARDWARE_WIRING_STRATEGY.md`](../../docs/architecture/legacy/HARDWARE_WIRING_STRATEGY.md) for reference.

### Quick Pin Reference

| Function | GPIO | Notes |
|----------|------|-------|
| **LoRa SPI (Internal)** | GPIO5/19/27 | Pre-wired |
| **LoRa Control (Internal)** | GPIO18/14/26/33 | Pre-wired |
| **Display I²C (Internal)** | GPIO4/15 | Pre-wired, 0x3C |
| **Sensor I²C** | **GPIO21/22** | **External sensors** |
| **Rain Sensor ADC** | GPIO36 | Voltage divider required |
| **Wind Sensor Interrupt** | GPIO34 | Optocoupler required |
| **Wind Sensor UART (Alt)** | GPIO17/23 | MAX485 required |
