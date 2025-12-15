# AllSky Safety Monitor - Integrated Execution Plan

**Status:** Ready for Implementation  
**Date:** 2025-12-15  
**Purpose:** Single-page build and coding roadmap for allsky-sensors + Safety Monitor

---

## SECTION 1 — MODULE OVERVIEW

### allsky-sensors (ESP32 + RFM95 LoRa Node)

**Hardware Responsibilities:**
- Acquire sensor data: RG-9 rain (analog), wind sensor (pulse interrupt), MLX90614 IR temp (I²C), TSL2591 SQM (I²C)
- Transmit via LoRa to The Things Network (TTN) every 30-60 seconds
- Operate autonomously (no dependency on Raspberry Pi availability)

**Firmware Responsibilities:**
- Initialize RFM95 (SPI), TSL2591 + MLX90614 (I²C), rain ADC, wind interrupt
- Join TTN via OTAA (or ABP), construct binary payload (~26 bytes)
- Manage power (deep sleep between transmissions if battery-powered)
- Implement watchdog for fault recovery

---

### allsky-camera / Safety Monitor (Raspberry Pi Application)

**Data Ingestion Responsibilities:**
- Poll TTN HTTP API or MQTT for allsky-sensors LoRa data (30-60 second interval)
- Continue reading Meet je Stad Node 580 temperature/humidity (external API, unchanged)
- Continue reading Allsky camera data from `/home/robert/allsky/tmp/allskydata.json` (unchanged)
- During Phase 1-3: Also read Arduino Nano + ESP8266 USB serial (parallel validation)

**Safety Logic Responsibilities:**
- Detect stale LoRa data (age >120 seconds), apply safe defaults (assume worst-case rain)
- Prioritize LoRa data over USB serial during parallel operation
- Control Waveshare relay board (fan/heater) based on integrated sensor data
- Trigger Pushover rain alerts when conditions met

**UI/Logging Responsibilities:**
- Display LoRa data source status in Flask dashboard ("SENSOR ONLINE" or "STALE")
- Log LoRa packet reception timestamps, frame counter deltas, TTN RSSI/SNR
- Add settings UI fields for TTN MQTT credentials or API endpoint

---

## SECTION 2 — WIRING PLAN SUMMARY

| Sensor/Module | ESP32 GPIO | Interface | Extra Components | Status |
|---------------|------------|-----------|------------------|--------|
| **RFM95 LoRa** | 2 (CS), 4 (DIO0), 5 (DIO1), 18 (SCK), 19 (MISO), 23 (MOSI) | SPI | None | **New** |
| **MLX90614 IR Temp** | 21 (SDA), 22 (SCL) | I²C (0x5A) | 4.7kΩ pull-ups (likely on breakout) | **Reuse existing I²C wires** |
| **TSL2591 SQM** | 21 (SDA), 22 (SCL) | I²C (0x29) | 4.7kΩ pull-ups (shared with MLX90614) | **Reuse existing I²C wires** |
| **RG-9 Rain** | 36 (ADC) | Analog 0-5V → 0-3.3V | **Voltage divider: 5.1kΩ + 10kΩ (1%)** | **Modify: Add divider at ESP32 end** |
| **Wind (Pulse)** | 34 (Interrupt) | Digital (10-30V pulse → 3.3V) | **4N35 optocoupler + 1kΩ + 10kΩ resistors** | **Modify: Add optocoupler circuit** |
| **Wind (RS485)** | 16 (RX2), 17 (TX2) | UART RS485 | **MAX485 module** | **Alternative to pulse mode** |

**Decision Required:** Choose **Wind Pulse (GPIO34)** OR **Wind RS485 (GPIO16/17)** before hardware assembly.

---

## SECTION 3 — FIRMWARE IMPLEMENTATION PLAN (allsky-sensors)

### **Step 1: Base Project Setup**
**Goal:** Create PlatformIO ESP32 project with LMIC library  
**Dependencies:** None (fresh start)  
**Actions:**
- Initialize PlatformIO project: `pio init --board esp32doit-devkit-v1`
- Add libraries: `LMIC-Arduino`, `Adafruit TSL2591`, `SparkFun MLX90614`
- Configure `platformio.ini` with ESP32 settings and upload port
- Copy pin definitions from stoflamp (`GPIO 2,4,5,18,19,23` for RFM95)

**Verification:** Compile succeeds, upload to ESP32 via USB, serial monitor shows "Project initialized"

---

### **Step 2: LoRa Connectivity (TTN Join + Uplink)**
**Goal:** Join TTN via OTAA, send test packet  
**Dependencies:** Step 1 complete, TTN application created (DevEUI/AppKey configured)  
**Actions:**
- Initialize LMIC with stoflamp pin mapping (`lmic_pins` struct)
- Implement `os_getDevEui()`, `os_getArtEui()`, `os_getDevKey()` callbacks
- Call `LMIC_reset()`, configure EU868 channels, start join
- Implement `onEvent()` handler to detect `EV_JOINED` and `EV_TXCOMPLETE`
- Send test payload (e.g., hardcoded `{0x01, 0x02, 0x03}`)

**Verification:** TTN console shows device joined, uplink packet visible with correct DevEUI

---

### **Step 3: I²C Sensors Integration**
**Goal:** Read MLX90614 and TSL2591, transmit via LoRa  
**Dependencies:** Step 2 complete, I²C sensors wired to GPIO21/22  
**Actions:**
- Add `Wire.begin(21, 22)` in `setup()`
- Initialize MLX90614 (`therm.begin()`) and TSL2591 (`tsl.begin()`)
- Read sky temperature, ambient temperature, IR, full spectrum, lux
- Construct binary payload (e.g., temps as int16_t scaled by 100, lux as float)
- Replace test payload with sensor data

**Verification:** Serial monitor shows sensor readings, TTN payload decoder displays correct temperature and lux values

---

### **Step 4: Analog + Interrupt Sensors Integration**
**Goal:** Read RG-9 rain (ADC) and wind sensor (pulse count or RS485)  
**Dependencies:** Step 3 complete, voltage divider + optocoupler wired  
**Actions:**
- Configure GPIO36 as ADC input (`analogRead()`)
- Read RG-9 with 10-sample averaging to reduce noise
- *If Pulse Mode:* Attach interrupt on GPIO34 (`attachInterrupt(GPIO34, windISR, FALLING)`), count pulses in ISR
- *If RS485 Mode:* Initialize `Serial2.begin(9600)` on GPIO16/17, parse wind sensor protocol
- Add rain intensity and wind speed to LoRa payload

**Verification:** Serial monitor shows rain and wind values responding to sensor changes, TTN payload includes all 4 sensor types

---

### **Step 5: Payload Construction and Encoding**
**Goal:** Optimize LoRa payload for TTN fair use (~30 bytes max)  
**Dependencies:** Step 4 complete, all sensors functional  
**Actions:**
- Define payload format (reference: stoflamp BitStream pattern or MJS firmware)
  - Header: Version (1 byte) + Node ID (1 byte) + Sequence (1 byte)
  - Rain: uint16_t scaled (2 bytes)
  - Wind: uint16_t scaled (2 bytes)
  - Sky temp: int16_t ×100 (2 bytes)
  - Ambient temp: int16_t ×100 (2 bytes)
  - SQM IR: uint16_t (2 bytes)
  - SQM full: uint16_t (2 bytes)
  - SQM visible: uint16_t (2 bytes)
  - SQM lux: float (4 bytes)
  - Footer: CRC16 (2 bytes) - optional
  - **Total: ~23 bytes** (well within SF7 limit)
- Write TTN payload decoder JavaScript function in TTN console
- Test decoding matches expected values

**Verification:** TTN console shows human-readable decoded JSON with all sensor fields correct

---

### **Step 6: Power Management and Watchdogs**
**Goal:** Add deep sleep (if battery-powered) and watchdog recovery  
**Dependencies:** Step 5 complete, basic operation stable  
**Actions:**
- Implement `esp_sleep_enable_timer_wakeup(30 * 1000000)` for 30-second intervals (if battery mode)
- Enter deep sleep after LoRa transmission completes (`EV_TXCOMPLETE`)
- **If USB-powered:** Skip deep sleep, use `delay()` or FreeRTOS task scheduling
- Enable hardware watchdog (`esp_task_wdt_init(30, true)`) to reset on firmware hang
- Test watchdog by inducing infinite loop, verify auto-recovery

**Verification:** Device wakes every 30 seconds (serial timestamp increments), watchdog resets device after 30-second hang

---

## SECTION 4 — SAFETY MONITOR / APPLICATION PLAN

### **Step 1: Repository Reorganization**
**Goal:** Move Python files to `safety-monitor/` subfolder, archive legacy firmware  
**Actions:**
- Execute `git mv` operations from REPOSITORY_GOVERNANCE.md (Section 3.1)
- Update systemd service files (`app.service`, `control.service`) with new paths
- Update `README.md` to reflect new structure
- Test Flask app starts: `python safety-monitor/app.py`

**Verification:** Services restart successfully, web UI accessible at `http://allsky.local:5000`

---

### **Step 2: LoRa Backend Ingestion (MQTT)**
**Goal:** Add TTN MQTT client to `fetch_data.py`  
**Dependencies:** Step 1 complete, TTN MQTT credentials available  
**Actions:**
- Install `paho-mqtt` library (`pip install paho-mqtt`, update `requirements.txt`)
- Create `get_lora_sensor_data()` function in `fetch_data.py`:
  - Connect to `eu1.cloud.thethings.network:1883` with TLS
  - Subscribe to `v3/{application_id}/devices/{device_id}/up`
  - Parse MQTT message JSON, extract `decoded_payload`
  - Return dict: `{rain_intensity, wind_speed, sky_temperature, ambient_temperature, sqm_ir, sqm_full, sqm_visible, sqm_lux, received_at}`
- Store MQTT credentials in `.env` (TTN_APP_ID, TTN_API_KEY)

**Verification:** Run `python safety-monitor/fetch_data.py` standalone, verify MQTT connection and payload parsing

---

### **Step 3: Data Model Alignment**
**Goal:** Integrate LoRa data into control loop without breaking existing USB/MJS flow  
**Dependencies:** Step 2 complete  
**Actions:**
- Modify `control_fan_heater()` in `control.py`:
  - Call `get_lora_sensor_data()` alongside existing `get_rain_wind_data()` and `get_sky_data()`
  - Tag data with source: `"data_source": "LoRa_TTN"` vs `"USB_Nano"` vs `"USB ESP8266"`
  - Store both in database for parallel comparison (Phase 1-2)
- Ensure existing fields match (`rain_intensity`, `wind`, `sky_temperature`, `ambient_temperature`, `sqm_ir`, `sqm_full`, `sqm_visible`, `sqm_lux`)

**Verification:** Database contains rows from both USB and LoRa sources with identical schema

---

### **Step 4: Stale Data Handling and Prioritization**
**Goal:** Implement safe defaults when LoRa data missing, prioritize LoRa over USB  
**Dependencies:** Step 3 complete  
**Actions:**
- Check `received_at` timestamp from TTN MQTT: if age >120 seconds, mark stale
- If stale:
  - Log warning: "LoRa sensor data stale (last update: X seconds ago)"
  - Apply safe default: `rain_intensity = 0` (assume raining for safety)
  - Flag for UI: `lora_status = "STALE"`
- If NOT stale and USB also available: prioritize LoRa data, log both for validation
- If stale AND USB available: fallback to USB data
- If stale >600 seconds (10 min): Send Pushover notification "LoRa sensor offline"

**Verification:** Disconnect sensor node, verify Safety Monitor switches to safe defaults within 2 minutes, Pushover alert after 10 minutes

---

### **Step 5: UI and Logging Updates**
**Goal:** Display LoRa status in dashboard, add TTN settings page  
**Dependencies:** Step 4 complete  
**Actions:**
- Add `lora_status` variable to `index.html` template (display "ONLINE" or "STALE")
- Add `data_source` column to dashboard table (show "LoRa" vs "USB" for each row)
- Extend `settings.html` to include TTN MQTT credentials (TTN_APP_ID, TTN_API_KEY, TTN_DEVICE_ID)
- Add log entries in `control.log`: "LoRa data received: RSSI=-112 dBm, SNR=8.5 dB, age=3s"

**Verification:** Dashboard shows "SENSOR ONLINE" when LoRa data fresh, "STALE" when >120s, settings page can update TTN credentials

---

### **Step 6: Cutover and Cleanup**
**Goal:** Decommission USB serial sensors after LoRa proven stable  
**Dependencies:** 7 days continuous LoRa operation with >95% packet success rate  
**Actions:**
- Set `control.py` to use LoRa as primary, USB as deprecated fallback only
- Power down Arduino Nano + ESP8266, disconnect USB cables
- Move `firmware/skymonitor/` and `firmware/wifi_sensors/` to `firmware/legacy/` (already done in Step 1if using REPOSITORY_GOVERNANCE plan)
- Remove `get_rain_wind_data()` and `get_sky_data()` USB functions from `fetch_data.py`
- Remove USB serial port settings from `settings.json`
- Update `README.md` to reflect LoRa-only operation

**Verification:** System boots and operates without USB sensors, no USB-related warnings in logs, firmware files archived

---

## SECTION 5 — INTEGRATED TIMELINE

| Phase | Duration | Parallel Work | Sequential Dependency | Key Checkpoint |
|-------|----------|---------------|----------------------|----------------|
| **Phase 0: Prep** | 1-2 weeks | Hardware procurement, TTN setup | None | Components received, TTN app created |
| **Phase 1A: Firmware Base** | 1 week | Repository reorganization (App Step 1) | None | First LoRa packet visible in TTN console |
| **Phase 1B: Sensors** | 2 weeks | MQTT client development (App Step 2) | Firmware Step 1 complete | All sensors transmitting via LoRa |
| **Phase 2: Parallel Validation** | 2-3 weeks | USB + LoRa both logging | Firmware Step 5 + App Step 3 complete | 95%+ packet success rate, data quality match |
| **Phase 3: Prioritization** | 1 week | Stale data logic + UI updates (App Steps 4-5) | Phase 2 validation passed | LoRa primary, USB fallback, dashboard shows status |
| **Phase 4: Cutover** | 1 week | Continuous monitoring | 7 days stable LoRa operation | USB sensors removed, firmware archived |
| **TOTAL** | **6-9 weeks** | | | USB serial decommissioned, LoRa-only operation |

**Parallelization Opportunities:**
- Repository reorganization can happen while breadboarding firmware
- MQTT client development can start while firmware is in sensor integration phase
- Documentation updates can happen continuously

**Sequential Dependencies:**
- Firmware LoRa connectivity MUST work before sensor integration
- Parallel validation MUST complete before cutover
- 7-day stable operation MUST pass before USB decommissioning

---

## SECTION 6 — FINAL IMPLEMENTATION APPROVALS

**Before Starting:**
- [ ] **Hardware Decision:** Wind pulse (GPIO 34) OR RS485 (GPIO 16/17) - CONFIRM CHOICE
- [ ] **Power Decision:** USB 5V from Pi (simple) OR battery+solar (complex) - CONFIRM CHOICE
- [ ] **Component Procurement:** ESP32, RFM95, resistors, optocoupler/MAX485 - CONFIRM ORDERED/AVAILABLE
- [ ] **TTN Coverage:** Gateway within range confirmed (check ttnmapper.org) - CONFIRM COVERAGE
- [ ] **TTN Setup:** Application created, DevEUI/AppEUI/AppKey generated - CONFIRM READY
- [ ] **Coding Model:** Approve **MiniMax-M2** for implementation phase - CONFIRM MODEL

**Post-Implementation Success Criteria:**
- LoRa packet reception rate ≥95% over 7 consecutive days
- Data accuracy within ±5% of USB serial baseline (Phase 2 validation)
- End-to-end latency sensor → TTN → Pi <10 seconds
- Relay control functions correctly with LoRa data only
- Zero false rain alerts during dry conditions
- Dashboard displays "SENSOR ONLINE" when LoRa data fresh

**Emergency Rollback Plan:**
If LoRa fails validation (Phase 2), revert to USB serial as primary until root cause resolved. USB sensors remain connected until Phase 4 specifically to enable this rollback.

---

## EXECUTION SEQUENCE SUMMARY

1. **Firmware First:** Get LoRa sensor node transmitting to TTN (Firmware Steps 1-5)
2. **Application Second:** Add TTN MQTT ingestion to Safety Monitor (App Steps 1-3)
3. **Parallel Validation:** Run both USB and LoRa for 2-3 weeks, compare data quality (Phase 2)
4. **Cutover:** Switch to LoRa primary, monitor for 7 days, decommission USB (Phases 3-4)

**Ready to Proceed?** Confirm final hardware decisions + coding model (MiniMax-M2) → Switch to Implementation Mode
