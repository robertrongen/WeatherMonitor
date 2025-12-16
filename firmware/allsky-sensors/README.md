# AllSky Sensors - ESP32 + RFM95 LoRa Sensor Node

**Status:** Skeleton - Ready for Implementation  
**Hardware:** ESP32 DevKit V1 + RFM95W LoRa Module  
**Backend:** The Things Network (TTN) v3 or Chirpstack

## Overview

Standalone LoRa sensor node transmitting environmental data to external backend.

### Sensors

1. **RG-9 Rain Sensor** - Analog input (GPIO36 with voltage divider)
2. **RS485 Wind Sensor** - Pulse mode (GPIO34 with optocoupler) OR RS485 mode (UART2)
3. **MLX90614 IR Temperature** - I²C (0x5A) on GPIO21/22
4. **TSL2591 Sky Quality Meter** - I²C (0x29) on GPIO21/22

### LoRa Configuration

- **Frequency:** 868 MHz (EU) / 915 MHz (US)
- **Module:** RFM95W (SX1276 chipset)
- **Pins:** See [`../../docs/architecture/HARDWARE_WIRING_STRATEGY.md`](../../docs/architecture/HARDWARE_WIRING_STRATEGY.md)
- **Network:** LoRaWAN OTAA (Over-The-Air Activation)
- **Transmission Interval:** 30-60 seconds

## File Structure

- `platformio.ini` - PlatformIO project configuration
- `src/main.cpp` - Main firmware with LoRaWAN functionality
- `src/secrets_template.h` - TTN credentials template
- `include/` - Header files
- `lib/` - Custom libraries if needed
- `test/` - Firmware unit tests

## Step 1: Minimal LoRaWAN Implementation

**Status:** ✅ **IMPLEMENTED** - Ready for testing

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

See [docs/architecture/HARDWARE_WIRING_STRATEGY.md`](../../docs/architecture/HARDWARE_WIRING_STRATEGY.md) for complete pin allocations and component requirements.
