# AllSky Sensors - Heltec WiFi LoRa 32 V2 Architecture

**Board:** Heltec WiFi LoRa 32 V2 (Board #4)  
**Status:** CANONICAL HARDWARE BASELINE  
**Date:** 2025-12-16  
**Supersedes:** ESP32 DevKit V1 + External RFM95 Module

---

## Overview

The **Heltec WiFi LoRa 32 V2** is an

 all-in-one ESP32 development board with integrated SX1276 LoRa radio (868/915 MHz) and 0.96" OLED display. This board serves as the canonical hardware baseline for the AllSky Sensors node, replacing the previous generic ESP32 + external RFM95 design.

### Key Specifications

| Component | Specification |
|-----------|---------------|
| **MCU** | ESP32-PICO-D4 (dual-core Xtensa LX6, 240 MHz) |
| **Flash** | 4 MB |
| **SRAM** | 520 KB |
| **LoRa Radio** | SX1276 (integrated, 868 MHz EU / 915 MHz US) |
| **Display** | 0.96" OLED, 128×64 pixels, SSD1306, I²C |
| **Power** | USB 5V OR 3.7V LiPo (onboard charging circuit) |
| **Antenna** | U.FL connector (external antenna required) |
| **Dimensions** | ~50mm × 25mm × 10mm |

### Product Link
- [Heltec Official Store](https://heltec.org/project/wifi-lora-32/)
- Widely available from distributors (AliExpress, Amazon, Adafruit, etc.)

---

## Integrated Components

### 1. LoRa Radio (SX1276)

The SX1276 LoRa transceiver is factory-integrated and pre-wired internally to the ESP32 via SPI. This eliminates the need for external breadboard wiring, reduces assembly errors, and ensures a factory-tested RF path.

**Internal Connections (pre-wired on board):**
```
ESP32 GPIO    SX1276 Pin    Signal      Notes
-----------   -----------   ------      -----
GPIO5         SCK           SPI Clock   VSPI bus
GPIO19        MISO          SPI Data In VSPI bus
GPIO27        MOSI          SPI Data Out VSPI bus
GPIO18        NSS/CS        Chip Select SPI slave select
GPIO14        RST           Reset       Hardware reset
GPIO26        DIO0          Interrupt   TX/RX done
GPIO33        DIO1          Interrupt   RX timeout
```

**Antenna:**
- U.FL connector on board edge
- **External antenna required** (868 MHz or 915 MHz depending on region)
- Recommended: Quarter-wave wire antenna (86mm for 868 MHz, 82mm for 915 MHz)
- Avoid operating without antenna (can damage RF frontend)

**Power:**
- 3.3V supply from onboard regulator
- 100 µF decoupling capacitor pre-installed
- Typical current: ~100mA during transmission

### 2. OLED Display (SSD1306)

The 0.96" OLED display is factory-integrated and pre-wired via I²C. Useful for field diagnostics without serial cable.

**Internal Connections (pre-wired on board):**
```
ESP32 GPIO    Display Pin   Signal      Notes
-----------   -----------   ------      -----
GPIO4         SDA           I²C Data    Display I²C bus
GPIO15        SCL           I²C Clock   Display I²C bus
GPIO16        RST           Reset       Hardware reset
VCC           3.3V          Power       From onboard regulator
GND           GND           Ground      Common ground
```

**I²C Address:** 0x3C (fixed, not configurable)

**Power Consumption:**
- Active: ~20 mA
- Sleep: <1 mA (display off)

**Display Usage Model:**
- **Default state:** OFF (to conserve power)
- **Activation:** Button press OR error condition OR transmission event
- **Timeout:** Auto-sleep after 10 seconds of inactivity
- **Content:** Node status, sensor readings summary, signal quality, error codes

---

## Architecture Rationale

### Why Integrated Board vs. ESP32 DevKit + External RFM95?

| Criterion | Heltec WiFi LoRa 32 V2 (Integrated) | ESP32 DevKit + External RFM95 |
|-----------|-------------------------------------|-------------------------------|
| **Wiring Complexity** | ✅ **None** - LoRa pre-wired | ❌ 8 wires (SPI + control) |
| **Assembly Risk** | ✅ **Low** - Factory-tested | ❌ High - Breadboard/perfboard required |
| **RF Path Quality** | ✅ **Optimized** - Factory impedance matching | ⚠️ Variable - Depends on assembly |
| **Enclosure Size** | ✅ **Compact** - Single board ~50mm × 25mm | ❌ Larger - Two boards + wiring |
| **Diagnostic Access** | ✅ **Built-in OLED** - Field diagnostics | ❌ Serial cable required |
| **Cost** | ~$25 USD | ~$15 (ESP32) + $10 (RFM95) = $25 USD |
| **Power Management** | ✅ **Integrated** - LiPo charging circuit | ⚠️ External charger required |
| **Failure Points** | ✅ **1 board** | ❌ 2 boards + connections |
| **Availability** | ✅ **Commodity** - Widely available | ⚠️ RFM95 supply variable |

**Conclusion:** The integrated board provides equivalent cost with significantly lower assembly complexity, better reliability, and built-in diagnostics. This makes it the superior choice for a production sensor node.

---

## I²C Architecture Decision

### Separate I²C Buses for Display and Sensors

**CRITICAL DESIGN DECISION:**  
The Heltec board has a display pre-wired to **GPIO4 (SDA) / GPIO15 (SCL)** at I²C address **0x3C**. 

**This design intentionally uses a SEPARATE I²C bus for external sensors:**
- **Sensor I²C Bus:** **GPIO21 (SDA) / GPIO22 (SCL)** ← **FIXED, NOT CONFIGURABLE**
- **Display I²C Bus:** GPIO4 (SDA) / GPIO15 (SCL) ← Pre-wired internally

### Rationale for Separate Buses

#### Option A (REJECTED): Share display I²C bus (GPIO4/15)
**Advantages:**
- Fewer wires (reuse display bus)
- Simpler firmware initialization

**Disadvantages (critical):**
- ❌ **Address conflict risk:** If sensor address changes to 0x3C, system fails
- ❌ **Bus contention:** Display communication errors can block sensor reads
- ❌ **Debugging complexity:** Cannot isolate sensor I²C issues from display issues
- ❌ **Unpredictable behavior:** Display refresh during sensor read can cause timing issues

#### Option B (SELECTED): Separate sensor I²C bus (GPIO21/22)
**Advantages:**
- ✅ **Address isolation:** No risk of conflicts, even if addresses change
- ✅ **Bus stability:** Display errors do not affect sensor data acquisition
- ✅ **Independent debugging:** Can test sensor I²C without display interference
- ✅ **Best practice:** Industry standard to separate critical sensors from peripherals
- ✅ **Predictable timing:** Sensor reads not affected by display refresh cycles

**Disadvantages:**
- ⚠️ Requires 2 additional wires for sensor I²C
- ⚠️ Slightly more complex firmware initialization (minimal effort)

**Decision:** The reliability and debugging benefits of separate buses far outweigh the minor wiring overhead. **GPIO21/22 is locked in as the sensor I²C bus.**

---

## Pin Availability Analysis

After LoRa radio and display allocation, the following GPIOs are available for external sensors:

### Available GPIO Pins

| GPIO | Type | Suitable For | Notes |
|------|------|--------------|-------|
| **21** | I/O | **I²C SDA (Sensors)** | **RESERVED FOR SENSORS** |
| **22** | I/O | **I²C SCL (Sensors)** | **RESERVED FOR SENSORS** |
| **34** | Input-only | Interrupt, ADC | No pull-up, interrupt-capable |
| **36** | Input-only | ADC | VP pin, 12-bit ADC |
| **37** | Input-only | ADC | Not broken out on board |
| **38** | Input-only | ADC | Not broken out on board |
| **39** | Input-only | ADC | VN pin, 12-bit ADC |
| **13** | I/O | General GPIO | |
| **12** | I/O | General GPIO | ⚠️ Strapping pin, use with caution |
| **17** | I/O | UART2 RX | |
| **23** | I/O | UART2 TX | |
| **25** | I/O | General GPIO, DAC | |
| **32** | I/O | General GPIO, ADC2 | |
| **2** | I/O | General GPIO | ⚠️ Onboard LED, strapping pin |
| **0** | I/O | General GPIO | ⚠️ Boot mode, strapping pin |

### Reserved/Unavailable GPIO Pins

| GPIO | Function | Reserved For |
|------|----------|--------------|
| 5, 19, 27 | SPI | LoRa radio (SCK, MISO, MOSI) |
| 18, 14, 26, 33 | SPI + Control | LoRa radio (CS, RST, DIO0, DIO1) |
| 4, 15, 16 | I²C + Control | OLED display (SDA, SCL, RST) |
| 1, 3 | UART | USB serial (TX, RX) - avoid use |

---

## Power Management

### Power Options

**Option 1: USB 5V (Recommended for Development)**
- USB-C or Micro-USB connector
- 5V → 3.3V onboard regulator (800 mA max)
- **Advantage:** Simple, reliable, good for bench testing
- **Disadvantage:** Requires USB cable to enclosure

**Option 2: 3.7V LiPo Battery (for Remote Deployment)**
- JST-PH 2.0mm connector (standard LiPo plug)
- Onboard TP4054 charging circuit (500 mA charge current)
- **Advantage:** Portable, untethered operation
- **Disadvantage:** Requires solar panel or periodic charging

**Option 3: Hybrid (USB + Battery)**
- Battery connected while USB powered
- Automatic switchover when USB disconnected
- **Advantage:** Uninterruptible operation during power failures
- **Recommended for production deployment**

### Power Consumption Estimates

| State | Current Draw | Duration | Energy |
|-------|-------------|----------|--------|
| **Deep Sleep** | ~20 µA | 55 seconds | 0.3 µAh |
| **Sensor Read** | ~100 mA | 2 seconds | 55 µAh |
| **LoRa TX (SF7)** | ~120 mA | 1 second | 33 µAh |
| **Display On** | ~20 mA | 10 seconds | 55 µAh |
| **Total per cycle (60s)** | — | 60 seconds | **143 µAh** |

**Battery Life Estimate:**
- 3000 mAh LiPo battery
- 60-second transmission interval
- Deep sleep between transmissions
- **Expected runtime:** ~20 days without solar

**With Solar Panel:**
- 5W solar panel
- 50% efficiency (variable weather)
- **Sustained indefinite operation** in most climates

---

## Display Usage Recommendations

### Default State: OFF (Power Conservation)

The OLED display draws ~20 mA when active. To maximize battery life, the display should remain **OFF by default** and only activate on-demand.

### Activation Triggers

1. **Physical Button Press** (GPIO0 with pull-up)
   - Display wakes for 10 seconds
   - Shows current sensor readings and node status
   - Auto-sleeps after timeout

2. **Error Condition**
   - I²C sensor failure
   - LoRa join failure
   - Low battery (<3.3V)
   - Display shows error code and stays on until acknowledged

3. **Transmission Event** (Firmware Option)
   - Briefly flash display during LoRa transmission
   - Show TX status (queued, sent, confirmed)
   - Auto-sleep after 3 seconds

### Display Content Layout

```
┌─────────────────────┐
│ AllSky Node #01     │  ← Node ID
│ JOINED | 12:34:56   │  ← Status | Timestamp
├─────────────────────┤
│ Sky: -12.3°C        │  ← MLX90614 IR temp
│ Amb:  18.5°C        │  ← MLX90614 ambient
│ Rain: 892 (dry)     │  ← RG-9 reading
│ Wind: 2.4 m/s       │  ← Wind speed
├─────────────────────┤
│ RSSI: -78 SNR: 9.2  │  ← Signal quality
│ Batt: 3.8V (85%)    │  ← Battery level
└─────────────────────┘
```

### Firmware Configuration

```cpp
#define DISPLAY_TIMEOUT_MS 10000  // 10 seconds
#define DISPLAY_ON_ERROR true      // Show display on error
#define DISPLAY_ON_TX false        // Don't flash during TX
#define BUTTON_PIN 0               // GPIO0 for wake
```

---

## Advantages Over External RFM95 Design

### 1. Simplified Assembly
- **Before:** 8 wires (SPI + control) soldered between ESP32 and RFM95
- **After:** Zero LoRa wiring required

### 2. Improved Reliability
- **Before:** Loose breadboard connections, potential cold solder joints
- **After:** Factory-tested RF path with impedance-matched antenna connection

### 3. Better RF Performance
- **Before:** Variable signal quality depending on assembly quality
- **After:** Consistent, optimized RF performance (factory calibration)

### 4. Faster Prototyping
- **Before:** 2-3 hours to wire and test LoRa connectivity
- **After:** <30 minutes to flash firmware and test

### 5. Built-in Diagnostics
- **Before:** Requires serial cable for status monitoring
- **After:** OLED display shows status in the field

### 6. Smaller Footprint
- **Before:** Two boards + spacing for wiring = ~80mm × 50mm
- **After:** Single board = ~50mm × 25mm

### 7. Lower Failure Modes
- **Before:** 3 failure points (ESP32, RFM95, wiring)
- **After:** 1 failure point (integrated board)

---

## Migration from Legacy Hardware

### From ESP32 DevKit V1 + External RFM95

**Hardware Changes:**
1. Replace ESP32 DevKit V1 + RFM95 module with Heltec board
2. Move all LoRa-related wiring to ignore (handled internally)
3. Update sensor I²C connections to GPIO21/22 (instead of sharing with any existing bus)
4. Add external antenna to U.FL connector

**Firmware Changes:**
1. Update LoRa SPI pin definitions (GPIO5/19/27 instead of GPIO18/19/23)
2. Update LoRa control pins (GPIO18/14/26/33 instead of GPIO2/4/5)
3. Initialize display on GPIO4/15 (new code)
4. Update sensor I²C to GPIO21/22 (new pins)

**See [`../../legacy/HARDWARE_WIRING_STRATEGY.md`](../../legacy/HARDWARE_WIRING_STRATEGY.md) for original RFM95 wiring reference.**

---

## Procurement Information

### Recommended Purchase Configuration

**Board:**
- Heltec WiFi LoRa 32 V2 (868 MHz for EU, 915 MHz for US)
- Verify SX1276 chipset (not SX1262 - different firmware required)
- **Cost:** ~$20-30 USD depending on source

**Antenna:**
- 868 MHz or 915 MHz external antenna with U.FL/IPEX connector
- Quarter-wave wire antenna (DIY) OR commercial stub antenna
- **Cost:** ~$2-5 USD

**Optional:**
- 3.7V LiPo battery (3000-5000 mAh recommended)
- Solar panel (5W, 5V output)
- Weatherproof enclosure (IP65+)

### Suppliers

- **Heltec Official Store** (AliExpress): Most reliable, but slower shipping
- **Amazon:** Faster shipping, slightly higher cost
- **Adafruit/SparkFun:** Premium pricing, excellent support

---

## Related Documentation

- **Wiring Guide:** [`HARDWARE_WIRING_ESP32_LORA_DISPLAY.md`](HARDWARE_WIRING_ESP32_LORA_DISPLAY.md)  
- **Architecture Plan:** [`../ARCHITECTURE_PLAN_V2.md`](../ARCHITECTURE_PLAN_V2.md)  
- **Legacy Hardware:** [`../legacy/HARDWARE_WIRING_STRATEGY.md`](../legacy/HARDWARE_WIRING_STRATEGY.md)  
- **Firmware README:** [`../../firmware/allsky-sensors/README.md`](../../firmware/allsky-sensors/README.md)

---

**Document Status:** CANONICAL BASELINE  
**Last Updated:** 2025-12-16  
**Review Date:** 2026-06-01  
