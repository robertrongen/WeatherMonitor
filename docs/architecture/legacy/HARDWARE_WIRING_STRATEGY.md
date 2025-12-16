# AllSky Sensors - Hardware Wiring Strategy (Option A)

**Status:** Hardware Design - Awaiting Approval  
**Date:** 2025-12-15  
**Mode:** Architect Mode - Hardware Level Only  
**Reference Baseline:** stoflamp project (proven ESP32 + RFM95 configuration)

---

## STEP 1 — STOFLAMP REFERENCE DESIGN ANALYSIS

### 1.1 MCU and LoRa Module Configuration (from stoflamp)

**MCU:** DOIT ESP32 DEVKIT V1  
- Dual-core Xtensa LX6, 240 MHz
- 520 KB SRAM, 4 MB Flash
- 34x GPIO pins (30-pin variant also common)
- Native SPI, I²C, UART support
- ADC: 18 channels, 12-bit resolution, **0-3.3V input range**

**LoRa Module:** RFM95W (SX1276 chipset)  
- Frequency: 868 MHz (EU) / 915 MHz (US)
- Interface: SPI
- Power: 3.3V supply (dedicated regulator recommended)
- Antenna: External via SMA or wire

### 1.2 Proven RFM95 Wiring (from stoflamp, lines 111-116, 283-292)

**SPI Bus (Shared ESP32 VSPI):**
```
ESP32 GPIO    RFM95 Pin    Signal
-----------   ---------    ------
GPIO 18       SCK          SPI Clock
GPIO 19       MISO         SPI Master In Slave Out
GPIO 23       MOSI         SPI Master Out Slave In
```

**Dedicated RFM95 Control:**
```
ESP32 GPIO    RFM95 Pin    Signal      Notes
-----------   ---------    ------      -----
GPIO 2        NSS/CS       Chip Select SPI slave select
GPIO 4        DIO0         Interrupt   TX/RX done
GPIO 5        DIO1         Interrupt   RX timeout
---           RST          Reset       Connected to ESP32 EN (auto-reset) OR GPIO (manual)
```

**Power:**
- RFM95 VCC: 3.3V (100 µF decoupling capacitor near module)
- RFM95 GND: Common ground with ESP32

**Why This Works:**
1. **SPI pins (18, 19, 23) are ESP32 VSPI defaults** → No conflicts with other hardware peripherals
2. **DIO0 and DIO1 on GPIO 4, 5** → Interrupt-capable pins, suitable for LoRaWAN timing
3. **CS on GPIO 2** → Safe for SPI control, not a strapping pin
4. **RST handling flexible:** Can use ESP32 EN pin (shared reset) or dedicated GPIO if manual control needed

### 1.3 Assumptions Confirmed by stoflamp

1. **Power Source:** USB 5V (regulated to 3.3V for RFM95 and sensors)
2. **SPI Bus Sharing:** NRF24L01 also on same SPI bus (pins 25, 26 for CE/CSN) → Proves SPI bus can be shared with proper CS management
3. **I²C Bus Usage:** OLED display (0x3C) + HTU21D sensor (0x40) on GPIO 21 (SDA) + GPIO 22 (SCL) → Standard I²C pins, no conflicts
4. **Interrupt Management:** GPIO 13 used for dust sensor interrupt → ESP32 has enough interrupt-capable pins
5. **Semaphore/Mutex:** stoflamp uses FreeRTOS semaphores (`IOsem`) to prevent SPI/I²C bus conflicts → This pattern **must be replicated** for allsky-sensors

---

## STEP 2 — WIRING PLAN FOR ALLSKY-SENSORS (OPTION A)

### 2.1 Complete Pin Allocation Table

| ESP32 GPIO | Function | Signal Type | Sensor/Module | Voltage Domain | Protection Required | Stoflamp Reusable? |
|------------|----------|-------------|---------------|----------------|---------------------|---------------------|
| **SPI BUS (VSPI)** |||||||
| 18 | SCK | SPI Clock | RFM95 | 3.3V | No | **YES** |
| 19 | MISO | SPI Data In | RFM95 | 3.3V | No | **YES** |
| 23 | MOSI | SPI Data Out | RFM95 | 3.3V | No | **YES** |
| 2 | CS/NSS | SPI Chip Select | RFM95 | 3.3V | No | **YES** |
| 4 | DIO0 | Interrupt | RFM95 (TX/RX done) | 3.3V | No | **YES** |
| 5 | DIO1 | Interrupt | RFM95 (RX timeout) | 3.3V | No | **YES** |
| **I²C BUS** |||||||
| 21 | SDA | I²C Data | MLX90614 + TSL2591 | 3.3V | No | **YES** |
| 22 | SCL | I²C Clock | MLX90614 + TSL2591 | 3.3V | No | **YES** |
| **ANALOG INPUT** |||||||
| 36 (VP) | ADC | Analog In | RG-9 Rain Sensor | **0-3.3V** | **Voltage Divider** | NO (no ADC in stoflamp) |
| **WIND SENSOR (OPTION 1: PULSE MODE)** |||||||
| 34 | Interrupt | Digital In (Pulse) | Wind Sensor (NPNR pulse) | **10-30V** | **Optocoupler Required** | NO (different sensor) |
| **WIND SENSOR (OPTION 2: RS485 MODE)** |||||||
| 16 (RX2) | UART RX | Serial Data | Wind Sensor (RS485-A) | 5V | **MAX485 Module** | NO (UART2 used for GPS in stoflamp) |
| 17 (TX2) | UART TX | Serial Data | Wind Sensor (RS485-B) | 5V | **MAX485 Module** | NO (UART2 used for GPS in stoflamp) |
| **SYSTEM** |||||||
| 0 | Boot Mode | Strapping Pin | Reserved (BOOT button) | 3.3V | No | YES (pullup) |
| EN | Reset | Hardware Reset | Shared with RFM95 (optional) | 3.3V | No | YES |

### 2.2 Detailed Sensor Connections

#### **2.2.1 RG-9 Rain Sensor (Analog)**

**Current Output:** 0-5V analog (lower voltage = wetter conditions)  
**Problem:** ESP32 ADC maximum input = 3.3V  
**Solution:** Voltage divider to scale 0-5V → 0-3.3V

**Wiring:**
```
RG-9 Analog Out ─────┬─────[10kΩ]─────┬───── ESP32 GPIO36 (ADC1_CH0)
                     │                 │
                    GND               [10kΩ]
                                       │
                                      GND
```

**Calculation:**
- Vout = Vin × (R2 / (R1 + R2))
- Vout = 5V × (10kΩ / (10kΩ + 5.1kΩ)) = 3.31V (within ESP32 safe range)
- **Recommended resistors:** R1 = 5.1kΩ (1%), R2 = 10kΩ (1%) for precision

**Signal Type:** Analog voltage, read via `analogRead(GPIO36)`  
**Reusable from stoflamp?** NO (stoflamp has no ADC usage, different pattern required)  
**Voltage Domain:** 0-5V (sensor) → 0-3.3V (ESP32 after divider)  
**Protection:** Voltage divider acts as overvoltage protection

---

#### **2.2.2 Wind Sensor (RS485 XNQJAL YCY) - OPTION 1: Pulse Mode (RECOMMENDED)**

**Current Output:** NPNR pulse output, 10-30V signal  
**Problem:** ESP32 GPIO maximum input = 3.3V  
**Solution:** Optocoupler to isolate and level-shift

**Wiring:**
```
Wind Sensor Pulse+ ─────[1kΩ]────┬──── 4N35 Anode (pin 1)
                                  │
Wind Sensor Pulse- (GND) ─────────┘

4N35 Cathode (pin 2) ──────── Wind Sensor GND
4N35 Emitter (pin 5) ──────── ESP32 GND
4N35 Collector (pin 4) ───┬─── ESP32 GPIO34
                          │
                       [10kΩ]  (pull-up)
                          │
                        ESP32 3.3V
```

**Component:** 4N35 optocoupler (or equivalent: TIL111, PC817)  
**Resistor Values:**
- Input series: 1kΩ (limits current through LED)
- Output pull-up: 10kΩ (ensures clean digital signal)

**Signal Type:** Digital interrupt, read via `attachInterrupt(GPIO34, ISR, FALLING)`  
**Reusable from stoflamp?** NO (stoflamp uses GPIO 13 for dust sensor, different interrupt pattern but logic is similar)  
**Voltage Domain:** 10-30V (sensor) → 3.3V (ESP32 after optocoupler)  
**Protection:** Optical isolation prevents high-voltage damage

---

#### **2.2.3 Wind Sensor (RS485 XNQJALCCY) - OPTION 2: RS485 Mode (ALTERNATIVE)**

**Current Output:** RS485 differential signaling (A/B pair), 5V logic  
**Problem:** ESP32 UART expects 3.3V logic  
**Solution:** MAX485 transceiver module (handles voltage translation and RS485 protocol)

**Wiring:**
```
Wind Sensor RS485-A ────── MAX485 Pin A
Wind Sensor RS485-B ────── MAX485 Pin B
Wind Sensor GND ─────────── MAX485 GND

MAX485 RO (Receiver Out) ─── ESP32 GPIO16 (UART2 RX)
MAX485 DI (Driver In) ──────── ESP32 GPIO17 (UART2 TX)
MAX485 DE + RE (Direction) ─── ESP32 GPIO25 (or GND for RX-only)
MAX485 VCC ────────────────── ESP32 3.3V
MAX485 GND ────────────────── ESP32 GND
```

**Module:** MAX485 breakout board (readily available, ~$1)  
**Signal Type:** UART serial, read via `Serial2.begin(9600)` (or sensor-specific baud rate)  
**Reusable from stoflamp?** NO (stoflamp UART2 used for GPS, but serial pattern  is identical)  
**Voltage Domain:** 5V RS485 (sensor) → 3.3V UART (ESP32 via MAX485)  
**Protection:** MAX485 handles differential signaling and ESD protection

**Option 1 vs. Option 2 Comparison:**
| Criterion | Option 1 (Pulse + Optocoupler) | Option 2 (RS485 + MAX485) |
|-----------|--------------------------------|---------------------------|
| **Complexity** | Low (2 resistors, 1 IC) | Medium (MAX485 module + direction control) |
| **Cost** | ~$0.50 | ~$1.50 |
| **Firmware** | Simple pulse counting (interrupt-based) | UART parsing (protocol-dependent) |
| **Reliability** | High (optical isolation) | Medium (requires correct RS485 termination) |
| **stoflamp Similarity** | Similar (GPIO 13 dust sensor pulse) | Similar (UART2 GPS parsing) |
| **Recommendation** | **PREFERRED** (simpler, proven pattern) | Fallback if pulse mode unavailable |

---

#### **2.2.4 MLX90614 IR Temperature Sensor (I²C)**

**Current Output:** I²C digital (address 0x5A, standard in stoflamp)  
**Problem:** None (native I²C support, 3.3V compatible)  
**Solution:** Direct connection to ESP32 I²C bus

**Wiring:**
```
MLX90614 VCC ──── ESP32 3.3V
MLX90614 GND ──── ESP32 GND
MLX90614 SDA ──── ESP32 GPIO21 (SDA)
MLX90614 SCL ──── ESP32 GPIO22 (SCL)
```

**Pull-up Resistors:** 4.7kΩ on SDA and SCL (typically included on sensor breakout board)  
**I²C Address:** 0x5A (factory default)  
**Signal Type:** I²C digital, read via `Wire.begin()` + SparkFun MLX90614 library  
**Reusable from stoflamp?** **YES** (identical pins, same I²C usage pattern)  
**Voltage Domain:** 3.3V  
**Protection:** None required

---

#### **2.2.5 TSL2591 Sky Quality Meter (I²C)**

**Current Output:** I²C digital (address 0x29)  
**Problem:** None (native I²C support, 3.3V compatible)  
**Solution:** Direct connection to ESP32 I²C bus (shared with MLX90614)

**Wiring:**
```
TSL2591 VCC ──── ESP32 3.3V
TSL2591 GND ──── ESP32 GND
TSL2591 SDA ──── ESP32 GPIO21 (SDA, shared with MLX90614)
TSL2591 SCL ──── ESP32 GPIO22 (SCL, shared with MLX90614)
```

**Pull-up Resistors:** 4.7kΩ on SDA and SCL (shared with MLX90614)  
**I²C Address:** 0x29 (no conflict with MLX90614 at 0x5A)  
**Signal Type:** I²C digital, read via `Wire.begin()` + Adafruit TSL2591 library  
**Reusable from stoflamp?** **YES** (identical pins, same I²C usage pattern as HTU21D)  
**Voltage Domain:** 3.3V  
**Protection:** None required

---

## STEP 3 — PIN ALLOCATION STRATEGY (RISK-AWARE)

### 3.1 Safe Pin Categories

**Category A: Proven Safe (from stoflamp):**
- GPIO 2, 4, 5: RFM95 SPI control → **REUSE AS-IS**
- GPIO 18, 19, 23: VSPI bus → **REUSE AS-IS**
- GPIO 21, 22: I²C bus → **REUSE AS-IS**

**Category B: Safe for New Sensors (verified ESP32-safe):**
- GPIO 36 (input-only, ADC1_CH0): Rain sensor ADC → **SAFE** (not strapping pin)
- GPIO 34 (input-only): Wind sensor interrupt → **SAFE** (not strapping pin, interrupt-capable)
- GPIO 16, 17 (UART2): Wind sensor RS485 (if using Option 2) → **SAFE CANDIDATE** (stoflamp uses for GPS, but available here)

**Category C: AVOID (Strapping Pins / Reserved):**
- GPIO 0: Boot mode select → **RESERVED** (button on devkit)
- GPIO 2: (Already used for RFM95 CS, but safe in this context)
- GPIO 12: MTDI strapping pin → **AVOID** (can affect boot if pulled high)
- GPIO 15: MTDO strapping pin → **AVOID** (can affect boot if pulled low)

### 3.2 Conflict Avoidance Strategy

**SPI Bus Conflicts:**
- **Risk:** Multiple SPI devices (RFM95 only in this design)
- **Mitigation:** Single SPI device, CS handled by GPIO2 (dedicated)
- **stoflamp Pattern:** Semaphore (`IOsem`) before `claimIO("RFM95 send")` → **MUST REPLICATE**

**I²C Bus Conflicts:**
- **Risk:** MLX90614 (0x5A) + TSL2591 (0x29) on same bus
- **Mitigation:** Different I²C addresses ensure no conflict
- **stoflamp Pattern:** Semaphore (`IOsem`) before `claimIO("I2C read")` → **MUST REPLICATE**

**Interrupt Conflicts:**
- **Risk:** Wind sensor (GPIO34) + RFM95 DIO0 (GPIO4) + RFM95 DIO1 (GPIO5)
- **Mitigation:** ESP32 supports multiple interrupts, all pins interrupt-capable
- **stoflamp Pattern:** `attachInterrupt(digitalPinToInterrupt(PIN), ISR, FALLING)` → **PROVEN SAFE**

**WiFi/LoRa Conflicts:**
- **Risk:** stoflamp comment (line 8): "Voorkom tegelijkertijd zenden van WiFi en LoRa"
- **Mitigation:** Single semaphore for all radio operations (WiFi not used in sensor node, only LoRa)
- **Not Applicable Here:** Sensor node = LoRa-only (no WiFi after initial commissioning)

---

## STEP 4 — MIGRATION OF PHYSICAL WIRING

### 4.1 Current Setup (USB Serial)

**Arduino Nano (Rain + Wind):**
- RG-9 rain sensor → Analog pin A0
- Wind sensor pulses → Digital pin 2 (interrupt)
- USB connection → Raspberry Pi (5V power + serial data)

**ESP8266 D1 Mini (IR Temp + SQM):**
- MLX90614 → I²C (D1=SCL, D2=SDA on ESP8266)
- TSL2591 → I²C (shared bus)
- USB connection → Raspberry Pi (5V power + serial data)

### 4.2 Sensor Wire Reusability

| Sensor | Current Wiring | Can Reuse? | Modification Required |
|--------|----------------|------------|------------------------|
| **RG-9 Rain** | 3-wire to Arduino (VCC, GND, Analog Out) | **YES** | Add voltage divider at ESP32 end (2 resistors) |
| **Wind (Pulse)** | 3-wire to Arduino (VCC, GND, Pulse) | **PARTIAL** | Add optocoupler circuit at ESP32 end |
| **Wind (RS485)** | 4-wire if RS485 used (VCC, GND, A, B) | **CONDITIONAL** | Depends if RS485 mode available; needs MAX485 module |
| **MLX90614** | 4-wire I²C to ESP8266 (VCC, GND, SDA, SCL) | **YES** | Direct reconnection to ESP32 GPIO21/22 |
| **TSL2591** | 4-wire I²C to ESP8266 (VCC, GND, SDA, SCL) | **YES** | Direct reconnection to ESP32 GPIO21/22 (shared with MLX90614) |

### 4.3 Breadboard Testing Strategy

**Phase 1: LoRa Connectivity Test (No Sensors)**
1. Wire ESP32 + RFM95 on breadboard (stoflamp pins exactly)
2. Flash minimal LMIC firmware (TTN join test)
3. Verify successful LoRa transmission to TTN console
4. **Exit Criteria:** Packet visible in TTN with correct DevEUI

**Phase 2: I²C Sensors (MLX90614 + TSL2591)**
1. Add MLX90614 and TSL2591 to I²C bus (GPIO21/22)
2. Flash firmware with sensor read + LoRa transmit loop
3. Verify sensor readings in Serial Monitor
4. Verify LoRa payload contains sensor data
5. **Exit Criteria:** TTN payload decoder shows correct temperature and lux values

**Phase 3: ADC Test (RG-9 Rain Sensor)**
1. Add voltage divider to breadboard (5.1kΩ + 10kΩ)
2. Connect RG-9 analog output through divider to GPIO36
3. Flash firmware with ADC read (10 samples averaged)
4. Verify ADC readings respond to simulated rain (wet finger on sensor)
5. **Exit Criteria:** ADC value correlates with wetness (lower when wet)

**Phase 4: Interrupt Test (Wind Sensor Pulse)**
1. Add 4N35 optocoupler circuit to breadboard
2. Connect wind sensor pulse output through optocoupler to GPIO34
3. Flash firmware with interrupt counter
4. Manually simulate pulses (or use function generator if available)
5. **Exit Criteria:** Pulse count increments correctly, no false triggers

**Phase 5: Integration Test (All Sensors + LoRa)**
1. Combine all sensors on breadboard
2. Flash final firmware (sensor acquisition + LoRa transmission loop)
3. Run for 1 hour continuously
4. Monitor Serial output for errors (sensor read failures, LoRa timeouts)
5. Check TTN console for consistent uplinks
6. **Exit Criteria:** Zero errors, 100% packet success rate

### 4.4 Final Deployment Sequence

**Step 1:** Transfer breadboard circuit to prototype PCB or perfboard  
**Step 2:** Test on bench for 24 hours (ESP32 powered by USB, sensors connected)  
**Step 3:** Install in weatherproof enclosure  
**Step 4:** Deploy enclosure at sensor site (maintain USB power initially)  
**Step 5:** Monitor TTN + Safety Monitor for 1 week (parallel with USB serial as fallback)  
**Step 6:** If stable, finalize wiring and remove USB serial boards  

---

## STEP 5 — DECISIONS AND CHECKPOINT

### 5.1 Concrete Wiring Decisions Requiring Approval

**Decision W1: Wind Sensor Interface Mode**
- **Option 1 (RECOMMENDED):** Pulse mode with 4N35 optocoupler
- **Option 2 (ALTERNATIVE):** RS485 mode with MAX485 module
- **Question:** Does your wind sensor support pulse output mode, or is RS485 mandatory?
- **Impact:** Affects GPIO assignment (GPIO34 vs. GPIO16/17) and component BOM

**Decision W2: Power Supply Strategy**
- **Option A:** USB 5V from Raspberry Pi (current setup, retained during migration)
- **Option B:** External 5V power supply (mains adapter) at sensor enclosure
- **Option C:** Battery + solar panel (requires charge controller, larger enclosure)
- **Recommendation:** Option A for migration Phase 1-3, revisit if battery operation desired later

**Decision W3: RFM95 Reset Pin Handling**
- **Option A:** Tie RFM95 RST to ESP32 EN pin (shared auto-reset, simpler wiring)
- **Option B:** Connect RFM95 RST to dedicated GPIO (e.g., GPIO27) for manual reset control
- **stoflamp Choice:** LMIC_UNUSED_PIN (line 287) suggests software-only reset or shared EN
- **Recommendation:** Option A (shared EN) for simplicity, unless manual RFM95 reset needed for debugging

**Decision W4: Voltage Divider Resistor Precision**
- **Option A:** 1% tolerance resistors (5.1kΩ + 10kΩ) for accurate ADC scaling
- **Option B:** 5% tolerance resistors (5.1kΩ + 10kΩ) for lower cost
- **Recommendation:** Option A (1%) to minimize rain sensor calibration drift

**Decision W5: I²C Pull-Up Resistors**
- **Assumption:** Sensor breakout boards have on-board 4.7kΩ pull-ups
- **Question:** Verify MLX90614 and TSL2591 breakout boards include pull-ups, or add external 4.7kΩ on SDA/SCL to ESP32 3.3V
- **Action:** Measure with multimeter before final assembly

### 5.2 Hardware-Level Risks

| **Risk** | **Likelihood** | **Impact** | **Mitigation** |
|----------|---------------|-----------|----------------|
| RG-9 overvoltage damage to ESP32 ADC | Low | High | Voltage divider with 1% resistors, test with multimeter before connection |
| Wind sensor pulse voltage exceeds 3.3V despite optocoupler | Low | Medium | Verify 4N35 collector voltage <3.3V with oscilloscope |
| I²C address conflict (MLX90614 or TSL2591 non-standard address) | Low | Low | I²C scanner sketch before firmware deployment |
| SPI bus contention (RFM95 lockup) | Low | Medium | Implement IOsem semaphore pattern from stoflamp |
| RFM95 fails to join TTN (antenna mismatch, SF too low) | Medium | High | Use 868MHz quarter-wave wire antenna (86mm), start with SF12 for testing |
| Loose breadboard connections causing intermittent failures | High | Low | Use perfboard or PCB for final deployment, solder all connections |

### 5.3 Open Hardware Questions

1. **Q-HW1:** What is the physical distance between current sensor enclosure and allsky-camera enclosure (Raspberry Pi)?
   - **Why:** Determines if existing sensor wires can be reused or need extension
   - **Action:** Measure and confirm wire gauge is adequate (minimum 22 AWG for 5V power over >5m)

2. **Q-HW2:** Does the current enclosure have space for ESP32 + RFM95 + voltage divider + optocoupler circuits?
   - **Action:** Measure internal dimensions and compare with component footprints

3. **Q-HW3:** Is there a mounting hole or DIN rail inside the enclosure for securing the ESP32 devkit?
   - **Action:** Plan mechanical mounting strategy (e.g., standoffs, hot glue, Velcro)

4. **Q-HW4:** What is the antenna routing strategy for RFM95 (internal stub antenna vs. external SMA connector)?
   - **Recommendation:** External 868 MHz quarter-wave wire antenna through cable gland (better signal, no enclosure interference)

5. **Q-HW5:** Are grounding and ESD protection adequate for outdoor deployment?
   - **Action:** Verify enclosure is grounded, consider TVS diodes on long sensor cables if lightning risk

### 5.4 Required Confirmat

ions Before Implementation

**Hardware Confirmations:**
- [ ] Wind sensor pulse output voltage measured (should be 10-30V as spec'd)
- [ ] RG-9 analog output voltage range verified (should be 0-5V as spec'd)
- [ ] MLX90614 and TSL2591 I²C addresses confirmed (0x5A and 0x29)
- [ ] ESP32 DevKit V1 variant selected (30-pin or 38-pin, specify exact model)
- [ ] RFM95 frequency confirmed (868 MHz for EU)
- [ ] Enclosure dimensions measured and component fit verified
- [ ] Voltage divider resistor values calculated and purchased (5.1kΩ + 10kΩ, 1% tolerance)
- [ ] 4N35 optocoupler and supporting resistors purchased (1kΩ + 10kΩ)

**Tooling and Testing:**
- [ ] Multimeter available for voltage measurements
- [ ] Oscilloscope available (optional, for pulse waveform verification)
- [ ] Soldering iron and solder for final connections
- [ ] Breadboard and jumper wires for prototyping
- [ ] TTN account configured and application created (see Architecture Plan v2)

---

## APPROVAL CHECKPOINT

**Do you approve this wiring strategy for Option A (ESP32 + RFM95 consolidated sensor node), and should we proceed to firmware implementation using the stoflamp repository as the hardware baseline?**

**Specific Areas for Final Hardware Review:**
- Pin allocation table (Section 2.1)
- RG-9 voltage divider design (Section 2.2.1)
- Wind sensor interface choice (Section 2.2.2 vs. 2.2.3)
- Breadboard testing sequence (Section 4.3)
- Wiring decisions W1-W5 (Section 5.1)

**Next Steps After Approval:**
1. Procure components (BOM generation)
2. Breadboard Phase 1 (LoRa connectivity test with stoflamp baseline firmware)
3. Firmware skeleton development (sensor drivers + LMIC integration)
4. Phased sensor integration testing (Phases 2-5)
5. Enclosure mechanical design and final deployment

**If Approved with Modifications:**
- Specify which wiring decisions need changes (W1-W5)
- Identify any additional hardware constraints or preferences
