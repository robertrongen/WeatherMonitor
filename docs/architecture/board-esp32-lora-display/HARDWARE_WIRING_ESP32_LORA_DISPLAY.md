# AllSky Sensors - Heltec WiFi LoRa 32 V2 Wiring Guide

**Board:** Heltec WiFi LoRa 32 V2  
**Status:** CANONICAL HARDWARE WIRING REFERENCE  
**Date:** 2025-12-16  

---

## Quick Reference: Pin Assignments

### Integrated Components (Pre-Wired Internally)

```
┌───────────────────────────────────────────────────────────────────┐
│ HELTEC WIFI LORA 32 V2 - FACTORY-INTEGRATED CONNECTIONS           │
├───────────────────────────────────────────────────────────────────┤
│ LoRa Radio (SX1276) - 868/915 MHz                                 │
│   SPI Bus:                                                        │
│     SCK:  GPIO5                                                   │
│     MISO: GPIO19                                                  │
│     MOSI: GPIO27                                                  │
│   Control:                                                        │
│     CS:   GPIO18                                                  │
│     RST:  GPIO14                                                  │
│     DIO0: GPIO26  (TX/RX done interrupt)                          │
│     DIO1: GPIO33  (RX timeout interrupt)                          │
│   Antenna: U.FL connector (external antenna required)             │
├───────────────────────────────────────────────────────────────────┤
│ OLED Display (SSD1306) - 0.96" 128×64                             │
│   I²C Bus:                                                        │
│     SDA:  GPIO4                                                   │
│     SCL:  GPIO15                                                  │
│     RST:  GPIO16                                                  │
│   I²C Address: 0x3C (fixed)                                       │
└───────────────────────────────────────────────────────────────────┘
```

### External Sensor Connections (To Be Wired)

```
┌───────────────────────────────────────────────────────────────────┐
│ EXTERNAL SENSORS - MANUAL WIRING REQUIRED                         │
├───────────────────────────────────────────────────────────────────┤
│ I²C Sensors (MLX90614 + TSL2591):                                 │
│   SDA: GPIO21   ← SENSOR I²C BUS (SEPARATE FROM DISPLAY)          │
│   SCL: GPIO22   ← SENSOR I²C BUS (SEPARATE FROM DISPLAY)          │
│   Addresses:                                                      │
│     MLX90614: 0x5A (IR temperature sensor)                        │
│     TSL2591:  0x29 (sky quality meter)                            │
│     Display:  0x3C (on GPIO4/15, NOT shared)                      │
├───────────────────────────────────────────────────────────────────┤
│ Rain Sensor (Hydreon RG-9):                                       │
│   GPIO36 (ADC1_CH0, input-only)                                   │
│   Voltage divider: 5V → 3.3V (R1=5.1kΩ, R2=10kΩ)                  │
├───────────────────────────────────────────────────────────────────┤
│ Wind Sensor (RS485 XNQJALCCY) - OPTION 1: Pulse Mode              │
│   GPIO34 (input-only, interrupt-capable)                          │
│   4N35 optocoupler + 10kΩ pull-up (10-30V → 3.3V)                 │
├───────────────────────────────────────────────────────────────────┤
│ Wind Sensor (RS485 XNQJALCCY) - OPTION 2: RS485 Mode (ALT)        │
│   UART2 RX: GPIO17                                                │
│   UART2 TX: GPIO23                                                │
│   MAX485 transceiver module required                              │
│   Direction control: GPIO25 (optional, or tie to GND for RX-only) │
└───────────────────────────────────────────────────────────────────┘
```

---

## Critical Design Decision: Separate I²C Buses

### ⚠️ IMPORTANT: Sensors Use Dedicated I²C Bus

**The Heltec board has a display pre-wired to GPIO4 (SDA) / GPIO15 (SCL) at I²C address 0x3C.**

**This design intentionally uses a SEPARATE I²C bus for external sensors:**

| Bus | SDA | SCL | Devices | Notes |
|-----|-----|-----|---------|-------|
| **Display Bus** | GPIO4 | GPIO15 | OLED (0x3C) | Internal, pre-wired |
| **Sensor Bus** | **GPIO21** | **GPIO22** | MLX90614 (0x5A), TSL2591 (0x29) | **EXTERNAL, LOCKED** |

### Why Separate Buses?

**Option A (REJECTED): Share display I²C bus**
- ❌ **Address conflict risk** - If sensor address changes to 0x3C, system fails
- ❌ **Bus contention** - Display refresh can block sensor reads
- ❌ **Debugging complexity** - Cannot isolate sensor vs display issues
- ❌ **Timing unpredictability** - Display operations interfere with sensor timing

**Option B (SELECTED): Separate sensor I²C bus on GPIO21/22**
- ✅ **Address isolation** - No conflicts possible
- ✅ **Bus stability** - Display errors don't affect sensors
- ✅ **Independent debugging** - Test sensor I²C without display
- ✅ **Best practice** - Industry standard for critical sensors
- ✅ **Predictable behavior** - No timing interference

**Trade-off:** Requires 2 additional wires, but reliability benefits far outweigh this minor overhead.

---

## Complete Pin Allocation Table

| GPIO | Type | Function | Connected To | Voltage | Notes |
|------|------|----------|--------------|---------|-------|
| **Integrated LoRa (SX1276)** ||||||
| 5 | Output | SPI SCK | LoRa radio | 3.3V | Internal |
| 19 | Input | SPI MISO | LoRa radio | 3.3V | Internal |
| 27 | Output | SPI MOSI | LoRa radio | 3.3V | Internal |
| 18 | Output | SPI CS | LoRa radio | 3.3V | Internal |
| 14 | Output | LoRa RST | LoRa radio | 3.3V | Internal |
| 26 | Input | LoRa DIO0 | LoRa radio | 3.3V | Internal, interrupt |
| 33 | Input | LoRa DIO1 | LoRa radio | 3.3V | Internal, interrupt |
| **Integrated Display (SSD1306)** ||||||
| 4 | I/O | I²C SDA | OLED display | 3.3V | Internal, addr 0x3C |
| 15 | Output | I²C SCL | OLED display | 3.3V | Internal |
| 16 | Output | Display RST | OLED display | 3.3V | Internal |
| **External Sensors (I²C)** ||||||
| **21** | **I/O** | **I²C SDA** | **MLX90614, TSL2591** | **3.3V** | **SENSOR BUS** |
| **22** | **Output** | **I²C SCL** | **MLX90614, TSL2591** | **3.3V** | **SENSOR BUS** |
| **External Sensors (Analog/Interrupt)** ||||||
| 36 | Input-only | ADC | RG-9 rain sensor | 0-3.3V | Voltage divider |
| 34 | Input-only | Interrupt | Wind sensor (pulse) | 3.3V | Optocoupler |
| **External Sensors (UART - Alternative)** ||||||
| 17 | Input | UART2 RX | Wind sensor (RS485) | 3.3V | MAX485 module |
| 23 | Output | UART2 TX | Wind sensor (RS485) | 3.3V | MAX485 module |
| 25 | Output | RS485 DIR | MAX485 DE/RE | 3.3V | Optional, or GND |
| **System Reserved** ||||||
| 0 | I/O | Boot / Button | User button | 3.3V | Pull-up, avoid use |
| 2 | I/O | Onboard LED | LED | 3.3V | Available if LED not needed |
| 1, 3 | UART | USB Serial | USB UART | 3.3V | Do not use |
| 6-11 | SPI | Flash | Internal flash | 3.3V | Do not use |
| 12 | I/O | Reserved | — | 3.3V | Strapping pin, avoid |

---

## Sensor Wiring Details

### 1. MLX90614 IR Temperature Sensor (I²C)

**Device:** SparkFun SEN-09570 or Adafruit 1747  
**Interface:** I²C, address 0x5A (factory default)  
**Voltage:** 3.3V compatible

**Connections:**
```
MLX90614 Pin    Heltec GPIO    Signal
------------    -----------    ------
VCC             3.3V           Power (onboard regulator)
GND             GND            Ground
SDL             GPIO21         I²C SDA (Sensor bus)
SCL             GPIO22         I²C SCL (Sensor bus)
```

**Pull-up Resistors:**
- 4.7kΩ on SDA (GPIO21) to 3.3V
- 4.7kΩ on SCL (GPIO22) to 3.3V
- **Note:** Most breakout boards include onboard pull-ups; verify with multimeter

**Library:** SparkFun MLX90614 Arduino Library
```cpp
#include <SparkFunMLX90614.h>
IRTherm mlx;

void setup() {
  Wire.begin(21, 22);  // SDA, SCL on sensor bus
  mlx.begin();
}

void loop() {
  float skyTemp = mlx.object();      // IR temperature of sky
  float ambientTemp = mlx.ambient(); // Sensor ambient temperature
}
```

---

### 2. TSL2591 Sky Quality Meter (I²C)

**Device:** Adafruit 1980  
**Interface:** I²C, address 0x29 (factory default)  
**Voltage:** 3.3V compatible

**Connections:**
```
TSL2591 Pin     Heltec GPIO    Signal
------------    -----------    ------
VIN             3.3V           Power (onboard regulator)
GND             GND            Ground
SDA             GPIO21         I²C SDA (Sensor bus, shared with MLX90614)
SCL             GPIO22         I²C SCL (Sensor bus, shared with MLX90614)
```

**Pull-up Resistors:**
- Same 4.7kΩ pull-ups as MLX90614 (shared bus)

**Library:** Adafruit TSL2591 Arduino Library
```cpp
#include <Adafruit_TSL2591.h>
Adafruit_TSL2591 tsl = Adafruit_TSL2591(2591);

void setup() {
  Wire.begin(21, 22);  // SDA, SCL on sensor bus
  tsl.begin();
}

void loop() {
  uint32_t lum = tsl.getFullLuminosity();
  uint16_t ir = lum >> 16;
  uint16_t full = lum & 0xFFFF;
  uint16_t visible = full - ir;
  float lux = tsl.calculateLux(full, ir);
}
```

---

### 3. RG-9 Rain Sensor (Analog with Voltage Divider)

**Device:** Hydreon RG-9 Rain Sensor  
**Output:** Analog voltage, 0-5V (lower = wetter)  
**Problem:** ESP32 ADC maximum input = 3.3V  
**Solution:** Voltage divider to scale 5V → 3.3V

#### Voltage Divider Circuit

```
RG-9 Analog Out ────┬────── [R1: 5.1kΩ] ──────┬────── Heltec GPIO36 (ADC)
                    │                         │
                   GND                    [R2: 10kΩ]
                                              │
                                             GND
```

**

Calculation:**
```
Vout = Vin × (R2 / (R1 + R2))
Vout = 5.0V × (10kΩ / (5.1kΩ + 10kΩ))
Vout = 5.0V × 0.662
Vout = 3.31V  ← Within ESP32 safe range (< 3.3V peak)
```

**Component Specifications:**
- R1: 5.1kΩ, 1/4W, **1% tolerance** (precision required)
- R2: 10kΩ, 1/4W, **1% tolerance** (precision required)
- **Why 1% tolerance?** 5% resistors can vary ±0.25kΩ, causing Vout range 3.08V-3.54V (exceeds 3.3V limit)

**Connections:**
```
RG-9 Pin        Heltec Connection     Signal
--------        -----------------     ------
VCC (+12V)      External 12V supply   Power (sensor requires 12V)
GND             Heltec GND            Ground (common)
Analog Out      Voltage divider       Signal
Divider Out     GPIO36 (ADC1_CH0)     ADC input
```

**Firmware:**
```cpp
#define RAIN_PIN 36
#define ADC_SAMPLES 10

uint16_t readRain() {
  uint32_t sum = 0;
  for (int i = 0; i < ADC_SAMPLES; i++) {
    sum += analogRead(RAIN_PIN);
    delay(10);
  }
  return sum / ADC_SAMPLES;  // 0-4095 (12-bit ADC)
}

void loop() {
  uint16_t rainValue = readRain();
  // Lower value = wetter (inverted scale)
  // Dry: ~900-1023, Wet: 0-500
}
```

---

### 4. Wind Sensor (RS485 XNQJALCCY) - OPTION 1: Pulse Mode (RECOMMENDED)

**Device:** RS485 XNQJALCCY Wind Sensor (pulse output mode)  
**Output:** NPNR pulse output, 10-30V signal  
**Problem:** ESP32 GPIO maximum input = 3.3V  
**Solution:** 4N35 optocoupler for voltage isolation and level shifting

#### Optocoupler Circuit

```
Wind Sensor Pulse+ ────[1kΩ]────┬─── 4N35 Anode (pin 1)
                                 │
Wind Sensor Pulse- (GND) ────────┴─── 4N35 Cathode (pin 2)

4N35 Emitter (pin 5) ──────────────── Heltec GND
4N35 Collector (pin 4) ───┬────────── Heltec GPIO34
                          │
                      [10kΩ]  (pull-up to 3.3V)
                          │
                      Heltec 3.3V
```

**Component Specifications:**
- Optocoupler: 4N35, TIL111, or PC817 (any standard optocoupler)
- Input resistor: 1kΩ, 1/4W (limits current through optocoupler LED)
- Pull-up resistor: 10kΩ, 1/4W (ensures clean digital signal)

**Operation:**
- Wind pulse HIGH (10-30V) → LED conducts → Transistor ON → GPIO34 pulled LOW
- Wind pulse LOW (0V) → LED off → Transistor OFF → GPIO34 pulled HIGH
- Firmware reads FALLING edge of GPIO34

**Connections:**
```
Component       Heltec GPIO    Signal      Notes
-------------   -----------    ------      -----
4N35 Collector  GPIO34         Pulse input Interrupt-capable, input-only
10kΩ pull-up    3.3V           Pull-up     To Heltec 3.3V rail
4N35 Emitter    GND            Ground      Common ground
```

**Firmware:**
```cpp
#define WIND_PIN 34
volatile uint32_t windPulseCount = 0;

void IRAM_ATTR windISR() {
  windPulseCount++;
}

void setup() {
  pinMode(WIND_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(WIND_PIN), windISR, FALLING);
}

void loop() {
  uint32_t pulses = windPulseCount;
  windPulseCount = 0;
  float windSpeed = (pulses * 8.75) / 100.0;  // Sensor-specific formula
  delay(5000);  // Read every 5 seconds
}
```

---

### 5. Wind Sensor (RS485 XNQJALCCY) - OPTION 2: RS485 Mode (ALTERNATIVE)

**Device:** RS485 XNQJALCCY Wind Sensor (RS485 mode)  
**Interface:** RS485 differential signaling (A/B pair)  
**Problem:** ESP32 UART expects 3.3V TTL logic  
**Solution:** MAX485 transceiver module

#### MAX485 Wiring

```
Wind Sensor Pin     MAX485 Pin      Heltec GPIO    Signal
---------------     ----------      -----------    ------
RS485-A             A               —              Differential A
RS485-B             B               —              Differential B
GND                 GND             GND            Common ground
VCC (+5V or +12V)   —               External PSU   Sensor power

MAX485 Pin          Heltec GPIO     Signal
----------          -----------     ------
RO (Receiver Out)   GPIO17          UART2 RX
DI (Driver In)      GPIO23          UART2 TX
DE (Driver Enable)  GPIO25          Direction control (opt: GND for RX-only)
RE (Receiver Enable) GPIO25         Direction control (opt: GND for RX-only)
VCC                 3.3V            MAX485 power
GND                 GND             Common ground
```

**Module:** MAX485 breakout board (widely available, ~$1 USD)

**Connections:**
```
MAX485 Pin      Heltec GPIO    Notes
----------      -----------    -----
RO              GPIO17         UART2 RX (wind sensor data)
DI              GPIO23         UART2 TX (optional, for commands)
DE + RE         GPIO25         Tie together, or tie to GND if RX-only
VCC             3.3V           From Heltec regulator
GND             GND            Common ground
A, B            Wind sensor    RS485 differential pair
```

**Firmware:**
```cpp
#define WIND_RX 17
#define WIND_TX 23
#define WIND_DIR 25

void setup() {
  Serial2.begin(9600, SERIAL_8N1, WIND_RX, WIND_TX);
  pinMode(WIND_DIR, OUTPUT);
  digitalWrite(WIND_DIR, LOW);  // RX mode (or LOW for always RX)
}

void loop() {
  if (Serial2.available()) {
    String data = Serial2.readStringUntil('\n');
    // Parse wind speed from RS485 protocol
  }
}
```

**Comparison: Pulse vs RS485**

| Criterion | Pulse (GPIO34 + Optocoupler) | RS485 (UART2 + MAX485) |
|-----------|------------------------------|------------------------|
| **Wiring Complexity** | ✅ Simple (2 wires) | ⚠️ Medium (4 wires + transceiver) |
| **Component Cost** | ✅ ~$0.50 (4N35) | ⚠️ ~$1.50 (MAX485) |
| **Firmware Complexity** | ✅ Simple (interrupt) | ⚠️ Medium (UART parsing) |
| **Reliability** | ✅ High (optical isolation) | ⚠️ Medium (RS485 termination required) |
| **Recommendation** | **PREFERRED** | Fallback if pulse unavailable |

---

## Power Distribution

### USB Power (Development/Production)

```
USB 5V ──→ Onboard Regulator ──→ 3.3V Rails
  │                                   │
  │                                   ├─→ ESP32-PICO-D4
  │                                   ├─→ SX1276 LoRa radio
  │                                   ├─→ SSD1306 OLED display
  │                                   └─→ External sensors (MLX90614, TSL2591)
  │
  └─→ LiPo Charging Circuit (TP4054, 500mA)
        │
        └─→ 3.7V LiPo Battery (JST-PH connector)
```

**Current Budget:**
- ESP32 (active): ~80 mA
- ESP32 (deep sleep): ~20 µA
- SX1276 (TX): ~120 mA peak
- SX1276 (RX): ~15 mA
- OLED (active): ~20 mA
- MLX90614: ~2 mA
- TSL2591: ~0.5 mA
- **Total (active, TX):** ~220 mA
- **Total (sleep):** ~20 µA

**Voltage Regulator:** Onboard AMS1117-3.3 (800 mA maximum)

### External Sensor Power

**RG-9 Rain Sensor:**
- Requires 12V external power supply (sensor has onboard regulator)
- **Cannot be powered from Heltec 3.3V rail**
- Analog output is 0-5V (scaled by voltage divider)

**Wind Sensor:**
- Requires 10-30V external power supply (sensor spec)
- **Cannot be powered from Heltec 3.3V rail**
- Pulse output is 10-30V (isolated by optocoupler)

**Recommended Power Architecture:**
```
Mains AC 110/220V
  │
  ├─→ 5V USB adapter ──→ Heltec USB port (board + I²C sensors)
  │
  └─→ 12V wall adapter ──→ RG-9 rain sensor
                        └─→ Wind sensor (if 12V compatible)
```

**Alternative (Battery Operation):**
```
Solar Panel (5W, 5V) ──→ Charge Controller ──→ 3.7V LiPo (3000-5000 mAh)
                                                  │
                                                  └─→ Heltec JST connector
                                                  
External 12V Battery ──→ RG-9 + Wind Sensor (separate power system)
```

---

## Assembly and Testing Procedure

### Phase 1: Board Verification (No Sensors)

**Goal:** Verify Heltec board functions correctly before adding sensors.

1. **Visual Inspection:**
   - Check for physical damage
   - Verify U.FL antenna connector is intact
   - Confirm display is properly seated

2. **Power Test:**
   - Connect USB cable
   - Onboard LED should light
   - Display should show Heltec logo (if factory firmware present)

3. **LoRa Test:**
   - Flash minimal LMIC firmware (TTN join test)
   - Attach 868/915 MHz antenna to U.FL connector
   - Verify TTN console shows device join

**Exit Criteria:** Device successfully joins TTN and transmits test packet.

---

### Phase 2: I²C Sensors (MLX90614 + TSL2591)

**Goal:** Verify sensor I²C bus works correctly.

1. **I²C Scanner Test:**
   ```cpp
   #include <Wire.h>
   
   void setup() {
     Serial.begin(115200);
     Wire.begin(21, 22);  // SDA, SCL on sensor bus
     Serial.println("I2C Scanner");
   }
   
   void loop() {
     for (byte i = 8; i < 120; i++) {
       Wire.beginTransmission(i);
       if (Wire.endTransmission() == 0) {
         Serial.printf("Device found at 0x%02X\n", i);
       }
     }
     delay(5000);
   }
   ```

2. **Expected Output:**
   ```
   Device found at 0x29  ← TSL2591
   Device found at 0x5A  ← MLX90614
   ```

3. **Sensor Read Test:**
   - Flash firmware with MLX90614 + TSL2591 libraries
   - Verify serial output shows temperature and lux values
   - Manually change lighting/temperature to verify responsiveness

**Exit Criteria:** Both sensors detected at correct addresses, readings stable and responsive.

---

### Phase 3: Analog Sensor (RG-9 Rain)

**Goal:** Verify voltage divider and ADC work correctly.

1. **Voltage Divider Bench Test:**
   - Apply 5V to RG-9 analog output simulator (or use lab power supply)
   - Measure voltage at GPIO36 with multimeter
   - **Expected:** 3.3V (within ±0.1V tolerance)

2. **ADC Read Test:**
   ```cpp
   void loop() {
     uint16_t adcValue = analogRead(36);
     float voltage = (adcValue / 4095.0) * 3.3;
     Serial.printf("ADC: %d, Voltage: %.2fV\n", adcValue, voltage);
     delay(1000);
   }
   ```

3. **RG-9 Wet Test:**
   - Short RG-9 output to GND (simulates wet condition)
   - **Expected ADC:** ~0-100 (low value)
   - Remove short (simulates dry condition)
   - **Expected ADC:** ~900-1023 (high value)

**Exit Criteria:** ADC values respond correctly to simulated wet/dry conditions.

---

### Phase 4: Interrupt Sensor (Wind Pulse)

**Goal:** Verify optocoupler and interrupt work correctly.

1. **Optocoupler Bench Test:**
   - Apply 12V pulse to optocoupler input (or use function generator)
   - Measure GPIO34 voltage with oscilloscope
   - **Expected:** GPIO34 toggles between 3.3V (pulse low) and 0V (pulse high)

2. **Interrupt Test:**
   ```cpp
   volatile uint32_t pulseCount = 0;
   
   void IRAM_ATTR windISR() {
     pulseCount++;
   }
   
   void setup() {
     pinMode(34, INPUT);
     attachInterrupt(digitalPinToInterrupt(34), windISR, FALLING);
   }
   
   void loop() {
     Serial.printf("Pulses: %d\n", pulseCount);
     pulseCount = 0;
     delay(5000);
   }
   ```

3. **Wind Sensor Test:**
   - Connect wind sensor pulse output through optocoupler
   - Manually spin wind sensor (if accessible) or blow on anemometer
   - **Expected:** Pulse count increases proportionally to wind speed

**Exit Criteria:** Interrupt fires correctly on wind pulses, no false triggers.

---

### Phase 5: Integration Test (All Sensors + LoRa)

**Goal:** Verify complete system works reliably.

1. **Flash Production Firmware:**
   - All sensors initialized
   - 60-second transmission interval
   - LoRa payload includes all sensor data

2. **24-Hour Burn-In:**
   - Run continuously for 24 hours
   - Monitor serial output for errors
   - Check TTN console for consistent uplinks
   - **Success Criteria:** Zero sensor read failures, >95% packet success rate

3. **Field Deployment:**
   - Install in weatherproof enclosure
   - Mount external antenna
   - Connect external power
   - Monitor for 1 week

**Exit Criteria:** System operates reliably in field conditions.

---

## Troubleshooting Guide

### Issue: LoRa Not Joining TTN

**Symptoms:** `EV_JOIN_FAILED` in serial output

**Possible Causes:**
1. Incorrect TTN credentials (DevEUI, AppEUI, AppKey)
2. No antenna connected
3. No TTN gateway coverage
4. Wrong frequency plan (868 MHz vs 915 MHz)

**Solutions:**
1. Verify credentials match TTN console exactly
2. Attach external antenna to U.FL connector
3. Check [TTN Mapper](https://ttnmapper.org) for gateway coverage
4. Update firmware frequency plan to match region

---

### Issue: I²C Sensor Not Detected

**Symptoms:** I²C scanner doesn't show expected device address

**Possible Causes:**
1. Wiring error (SDA/SCL swapped or wrong GPIO)
2. Missing pull-up resistors
3. Sensor not powered
4. Incorrect I²C address

**Solutions:**
1. Verify SDA=GPIO21, SCL=GPIO22 (sensor bus, NOT GPIO4/15)
2. Measure resistance from SDA/SCL to 3.3V (should be ~4.7kΩ)
3. Verify sensor VCC is connected to 3.3V
4. Check sensor datasheet for alternate I²C addresses

---

### Issue: ADC Reading Exceeds 3.3V (Damaged ESP32)

**Symptoms:** `analogRead()` returns 4095 constantly, or ADC non-functional

**Possible Causes:**
1. Voltage divider miscalculated
2. Wrong resistor values used
3. Sensor output exceeded 5V

**Solutions (PREVENTION ONLY - DAMAGE IS PERMANENT):**
1. Double-check voltage divider calculation before connecting
2. Measure voltage at GPIO36 with multimeter before applying power
3. Use 1% tolerance resistors for accuracy
4. Consider using external ADC (ADS1115) for safety

---

### Issue: Wind Pulse Not Detected

**Symptoms:** Interrupt never fires, pulseCount stays at 0

**Possible Causes:**
1. Optocoupler wired incorrectly
2. Pull-up resistor missing
3. Interrupt attached to wrong edge (RISING vs FALLING)
4. Wind sensor not powered

**Solutions:**
1. Verify 4N35 collector to GPIO34, emitter to GND
2. Measure GPIO34 voltage: should be 3.3V when idle (pull-up active)
3. Change `FALLING` to `RISING` in `attachInterrupt()`
4. Verify wind sensor has external 12V power

---

### Issue: Display Shows Garbage or Blank

**Symptoms:** OLED displays random pixels or stays blank

**Possible Causes:**
1. Display not initialized in firmware
2. I²C address conflict (if sensors on wrong bus)
3. Display damaged

**Solutions:**
1. Add display initialization code:
   ```cpp
   #include <U8g2lib.h>
   U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, 16, 15, 4);
   
   void setup() {
     u8g2.begin();
     u8g2.clearBuffer();
     u8g2.setFont(u8g2_font_ncenB08_tr);
     u8g2.drawStr(0, 10, "AllSky Node");
     u8g2.sendBuffer();
   }
   ```
2. Verify sensors are on GPIO21/22, NOT GPIO4/15
3. Contact Heltec support for replacement

---

## Bill of Materials (BOM)

### Core Hardware

| Item | Description | Qty | Source | Est. Cost |
|------|-------------|-----|--------|-----------|
| **Heltec WiFi LoRa 32 V2** | ESP32 + SX1276 + OLED | 1 | Heltec/AliExpress | $25 USD |
| **External Antenna** | 868/915 MHz, U.FL connector | 1 | Amazon/eBay | $3 USD |
| **MLX90614** | IR temperature sensor | 1 | SparkFun/Adafruit | $15 USD |
| **TSL2591** | Sky quality meter | 1 | Adafruit | $7 USD |
| **RG-9 Rain Sensor** | Analog rain sensor | 1 | Hydreon | $50 USD |
| **RS485 Wind Sensor** | XNQJALCCY anemometer | 1 | AliExpress | $30 USD |

### Supporting Components

| Item | Description | Qty | Source | Est. Cost |
|------|-------------|-----|--------|-----------|
| **Resistor 5.1kΩ 1%** | Voltage divider R1 | 1 | Mouser/Digikey | $0.10 USD |
| **Resistor 10kΩ 1%** | Voltage divider R2, pull-up | 2 | Mouser/Digikey | $0.20 USD |
| **4N35 Optocoupler** | Pulse isolation | 1 | Mouser/Digikey | $0.50 USD |
| **Resistor 1kΩ** | Optocoupler LED current | 1 | Mouser/Digikey | $0.10 USD |
| **MAX485 Module** | RS485 transceiver (alt) | 1 | Amazon/eBay | $1.50 USD |
| **3.7V LiPo Battery** | Optional, 3000 mAh | 1 | Adafruit/Amazon | $15 USD |
| **Weatherproof Enclosure** | IP65, ~150×100×50mm | 1 | Amazon | $10 USD |

**Total Estimated Cost:** ~$157 USD (without optional battery/enclosure)

---

## Related Documentation

- **Board Architecture:** [`ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md`](ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md)  
- **System Architecture:** [`../ARCHITECTURE_PLAN_V2.md`](../ARCHITECTURE_PLAN_V2.md)  
- **Legacy Wiring (RFM95):** [`../legacy/HARDWARE_WIRING_STRATEGY.md`](../legacy/HARDWARE_WIRING_STRATEGY.md)  
- **Firmware README:** [`../../firmware/allsky-sensors/README.md`](../../firmware/allsky-sensors/README.md)

---

**Document Status:** CANONICAL WIRING REFERENCE  
**Last Updated:** 2025-12-16  
**Review Date:** 2025-12-16 (after Phase 5 integration test)
