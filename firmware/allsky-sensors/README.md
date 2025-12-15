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

- `platformio.ini` - PlatformIO project configuration (to be created)
- `src/main.cpp` - Main firmware (to be implemented)
- `include/` - Header files
- `lib/` - Custom libraries if needed
- `test/` - Firmware unit tests

## Build System

This firmware uses **PlatformIO**, not Arduino IDE:
```bash
pio init --board esp32doit-devkit-v1
pio lib install "MCCI LoRaWAN LMIC library" "Adafruit TSL2591 Library" "SparkFun MLX90614 Arduino Library"
pio run
pio run --target upload
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
