# AllSky Safety Monitor - Modular Architecture Plan

**Status:** Draft for Review  
**Date:** 2025-12-15  
**Mode:** Architect Mode - Analysis and Design Only

---

## STEP 1 – CURRENT STATE ANALYSIS

### 1.1 System Overview

The current system is a monolithic AllSky Safety Monitor running on a Raspberry Pi 4B that integrates:
- **ZWO ASI224MC camera** with Allsky software (upstream project baseline)
- **Environmental sensors** via two USB serial interfaces
- **Safety logic** for observatory protection (fan, heater, rain alerts)
- **External sensor data** from Meet je Stad node 580 (temperature, humidity)

### 1.2 Existing Firmware Analysis

#### **Arduino Nano (firmware/skymonitor/skymonitor.ino)**
- **Port:** `/dev/ttyUSB1` (configurable in settings)
- **Baud Rate:** 115200
- **Sensors Managed:**
  - Hydreon RG-9 rain sensor (analog pin A0)
  - RS485 XNQJALYCY wind sensor (interrupt pin 2, NPNR pulse output)
- **Data Output:** JSON every 5 seconds
  ```json
  {"wind_speed": <float>, "rain_intensity": <float>}
  ```
- **Features:**
  - Serial-controlled debug mode (DEBUG ON/OFF)
  - 5-sample rolling average for rain readings
  - Pulse counting for wind speed calculation

#### **ESP8266 D1 Mini (firmware/wifi_sensors/wifi_sensors.ino)**
- **Port:** `/dev/ttyUSB0` (configurable in settings)
- **Baud Rate:** 115200
- **Sensors Managed:**
  - MLX90614 IR temperature sensor (I2C: sky + ambient temperature)
  - TSL2591 sky quality meter (I2C: IR, full spectrum, visible, lux)
- **Data Output:** JSON every 30 seconds
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
- **Features:**
  - I2C device scanning on startup
  - Serial-controlled debug mode
  - LED status feedback (solid = healthy, blinking = sensor failure)
  - Graceful handling of missing sensors (reports "N/A")

### 1.3 Safety Monitor Services (Raspberry Pi)

#### **control.py** (control.service)
Main orchestration service that runs in an infinite loop:
1. Fetches external temperature/humidity from Meet je Stad node 580
2. Fetches rain/wind data via serial from Arduino Nano
3. Fetches sky quality data via serial from ESP8266
4. Reads Allsky camera data from `/home/robert/allsky/tmp/allskydata.json`
5. Computes derived values (dew point, heat index, cloud coverage, brightness, Bortle scale)
6. Controls Waveshare RPi Relay Board (3 channels via GPIO 26, 20, 21):
   - Fan In + Fan Out (Ch1 + Ch3): ON if temp > threshold OR camera temp > 25°C OR dew point proximity OR CPU temp > threshold
   - Dew Heater (Ch2): ON if temp < dew point + threshold
7. Stores all data in SQLite database (`sky_data.db`)
8. Triggers WebSocket update to connected clients
9. Checks rain alert conditions (`rain_alarm.py`)
10. Repeats every 60 seconds (configurable)

#### **app.py** (app.service)
Flask web server providing:
- Dashboard UI (`/`, `/dashboard`, `/settings`)
- REST API endpoints (`/api/sky_data`, `/api/metrics_data`)
- WebSocket integration for real-time updates
- Log viewing (`/logs/<log_name>`)
- Rain alert enable/disable controls

#### **system_monitor.py** (system_monitor.service)
Background service collecting Raspberry Pi metrics:
- CPU temperature and usage
- Memory usage
- Disk usage
- Stores in separate `Metrics` table

#### **fetch_data.py**
Data acquisition module with functions:
- `get_temperature_humidity(url)`: Fetches from external API (Meet je Stad)
- `get_rain_wind_data(port, rate)`: Reads from Arduino Nano serial
- `get_sky_data(port, rate)`: Reads from ESP8266 serial
- `get_allsky_data(file_path)`: Parses Allsky JSON file
- All functions have timeout handling and retry logic

#### **rain_alarm.py**
Safety alert system:
- Monitors rain intensity against threshold
- Sends Pushover notifications when raining detected
- Respects user-controlled alert active/inactive state
- Auto-disables alert after notification sent

### 1.4 Allsky Integration Points

The system integrates with the **upstream Allsky project** (https://github.com/AllskyTeam/allsky) at the **data consumption layer only**:

**Integration Pattern:**
- Allsky runs independently on the same Raspberry Pi
- Allsky generates `/home/robert/allsky/tmp/allskydata.json` containing:
  - `AS_TEMPERATURE_C`: Camera sensor temperature
  - `AS_STARCOUNT`: Detected star count (night only)
  - `DAY_OR_NIGHT`: Current imaging mode
- Safety Monitor reads this file passively (no modification to Allsky)
- Data is used for:
  - **Safety Logic:** Camera temperature influences fan control
  - **Observability:** Star count displayed in dashboard
  - **Context:** Day/night mode affects display logic

**Allsky Responsibilities (Upstream Baseline):**
- Camera capture and image processing
- Star detection algorithms
- Web UI for camera images
- Timelapse generation
- Image overlays and metadata

**Safety Monitor Responsibilities (This Project):**
- Environmental sensor integration
- Safety-critical relay control
- Observatory protection logic
- Unified data storage and API
- Alert notifications

### 1.5 Data Flow Diagram (Current State)

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4B                          │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │   Allsky     │      │    Safety    │                   │
│  │   Software   │─────▶│   Monitor    │                   │
│  │  (Upstream)  │ JSON │  control.py  │                   │
│  └──────────────┘      └──────┬───────┘                   │
│         │                      │                            │
│         │ I²C                  │ GPIO                       │
│         ▼                      ▼                            │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │ ZWO ASI224MC │      │  Waveshare   │                   │
│  │    Camera    │      │ Relay Board  │                   │
│  └──────────────┘      └──────────────┘                   │
│                                                             │
│  USB Serial Ports:                                         │
│  ┌──────────────────────────────────────┐                 │
│  │ /dev/ttyUSB0         /dev/ttyUSB1    │                 │
│  └─────┬──────────────────────┬─────────┘                 │
└────────┼──────────────────────┼───────────────────────────┘
         │                      │
         ▼                      ▼
  ┌──────────────┐      ┌──────────────┐
  │  ESP8266     │      │ Arduino Nano │
  │  D1 Mini     │      │              │
  └──────┬───────┘      └──────┬───────┘
         │ I²C                 │
         ▼                     ▼
  ┌──────────────┐      ┌──────────────┐
  │  MLX90614    │      │   RG-9 Rain  │
  │  TSL2591     │      │   Wind Sensor│
  └──────────────┘      └──────────────┘

  External API:
  ┌──────────────────────────────┐
  │  Meet je Stad Node 580       │
  │  (temp + humidity)           │
  └──────────────────────────────┘
```

### 1.6 Component Classification

#### **a) allsky-camera Responsibilities**
Items that should remain with the Raspberry Pi camera module:
- ZWO ASI224MC camera interfacing
- Allsky software (upstream project - no changes)
- Image capture, processing, timelapse
- Web UI for camera viewing
- Waveshare Relay Board control (safety-critical placement)
- Safety decision logic (requires all sensor data integration)
- Flask web server (dashboard, API, settings)
- SQLite database (unified data storage)
- Meet je Stad external API integration (stationary network service)
- System monitoring (Raspberry Pi metrics)

#### **b) allsky-sensors Responsibilities**
Items that should become standalone LoRa sensor node:
- Rain sensor (RG-9) reading and processing
- Wind sensor (RS485 XNQJALYCY) reading and processing
- IR temperature sensor (MLX90614) reading and processing
- Sky quality meter (TSL2591) reading and processing
- Local sensor calibration and validation
- Data aggregation and packaging
- LoRa transmission logic

#### **c) Shared/Integration Glue**
Items requiring coordination:
- **Data contract definitions** (sensor telemetry format)
- **Time synchronization** (sensor timestamps vs. Raspberry Pi clock)
- **Fallback handling** (what happens when LoRa link fails)
- **Configuration management** (sensor IDs, transmission intervals)
- **Validation logic** (stale data detection, outlier filtering)

---

## STEP 2 – TARGET ARCHITECTURE DESIGN

### 2.1 Modular Architecture Overview

**Principle:** Separation of concerns with stable, well-defined interfaces.

```
┌─────────────────────────────────────────────────────────────────┐
│                      ALLSKY-CAMERA MODULE                        │
│                    (Raspberry Pi 4B 8GB)                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Allsky Software (Upstream)                   │  │
│  │  - Camera capture and processing                          │  │
│  │  - Star detection                                         │  │
│  │  - Web UI                                                 │  │
│  │  - Writes: /tmp/allskydata.json                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Safety Monitor Application                     │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │  Data Ingestion Layer                                │ │  │
│  │  │  - LoRa receiver (SX127x module)                    │ │  │
│  │  │  - Allsky JSON file reader                          │ │  │
│  │  │  - Meet je Stad API client                          │ │  │
│  │  │  - USB serial fallback (during migration)           │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │  Decision Logic Layer                                │ │  │
│  │  │  - Safety thresholds evaluation                     │ │  │
│  │  │  - Fan/heater control logic                         │ │  │
│  │  │  - Rain alert triggers                              │ │  │
│  │  │  - Stale data handling                              │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │  Output Layer                                        │ │  │
│  │  │  - GPIO relay control                               │ │  │
│  │  │  - SQLite database storage                          │ │  │
│  │  │  - Flask web server / REST API                      │ │  │
│  │  │  - Pushover notifications                           │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Hardware:                                                       │
│  - ZWO ASI224MC camera                                          │
│  - Waveshare RPi Relay Board                                    │
│  - LoRa receiver module (SX1276/RFM95W)                        │
└──────────────────────────────────────────────────────────────────┘
                               ▲
                               │ LoRa 868/915 MHz
                               │ (bidirectional for config)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ALLSKY-SENSORS MODULE                        │
│               (Standalone LoRa Node - Future)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Sensor Acquisition Logic                        │  │
│  │  - Rain sensor driver (RG-9)                             │  │
│  │  - Wind sensor driver (RS485)                            │  │
│  │  - IR temp sensor driver (MLX90614)                      │  │
│  │  - SQM driver (TSL2591)                                  │  │
│  │  - Local validation and calibration                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Data Aggregation & Packaging                    │  │
│  │  - Sensor data buffering                                 │  │
│  │  - Timestamp management                                  │  │
│  │  - Data compression/encoding                             │  │
│  │  - Checksum/CRC calculation                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           LoRa Communication                              │  │
│  │  - Transmission scheduling (adaptive duty cycle)         │  │
│  │  - Downlink command handling (config updates)           │  │
│  │  - Retry logic and acknowledgment                        │  │
│  │  - Power management (sleep modes)                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Hardware Options:                                               │
│  - Option A: Arduino + ESP32 + LoRa module                      │
│  - Option B: Single ESP32 board with LoRa (TTGO Lora32)        │
│  - Option C: Custom PCB with STM32 + SX1276                     │
│  - Sensors: RG-9, RS485 Wind, MLX90614, TSL2591                │
│  - Power: Battery + solar panel OR wired                        │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Responsibility Boundaries

#### **ALLSKY-CAMERA Module**
**Primary Responsibilities:**
- Observatory safety enforcement (relay control)
- Data aggregation from multiple sources (LoRa, Allsky, external API)
- User interface and configuration management
- Historical data storage and API
- Alert generation and notification

**Key Constraint:** Remains stationary, network-connected, mains-powered.

#### **ALLSKY-SENSORS Module**
**Primary Responsibilities:**
- Autonomous sensor data collection
- Local data validation and preprocessing
- Wireless transmission via LoRa
- Power-efficient operation (if battery-powered)

**Key Constraint:** Operates independently; no dependencies on network or Raspberry Pi availability.

### 2.3 Interaction Points

#### **Between Allsky (Upstream) and Safety Monitor**
- **Interface Type:** File-based
- **File Path:** `/home/robert/allsky/tmp/allskydata.json`
- **Update Frequency:** Per Allsky image capture cycle (~10-60 seconds)
- **Data Flow Direction:** Allsky → Safety Monitor (read-only)
- **Failure Mode:** Safety Monitor continues with missing camera data fields

#### **Between Safety Monitor and LoRa Sensor Node**
- **Interface Type:** Wireless LoRa communication
- **Frequency Band:** 868 MHz (EU) or 915 MHz (US)
- **Topology:** Star network (sensor node → gateway)
- **Data Flow:**
  - **Uplink (primary):** Sensor telemetry (periodic, ~30-60 seconds)
  - **Downlink (optional):** Configuration commands, acknowledgments
- **Failure Mode:** Safety Monitor uses last known good values, flags stale data

#### **Between Safety Monitor and Meet je Stad Node 580**
- **Interface Type:** HTTPS REST API
- **Endpoint:** `https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1`
- **Update Frequency:** ~5 minutes (external system schedule)
- **Data Flow Direction:** Meet je Stad → Safety Monitor
- **Failure Mode:** Safety Monitor continues with missing external temp/humidity

### 2.4 Safety-Critical Logic Placement

**Decision:** All safety-critical logic MUST remain on the Raspberry Pi (allsky-camera module).

**Rationale:**
1. **Proximity to actuators:** GPIO relay control requires local decision-making.
2. **Multi-source integration:** Fan/heater control depends on:
   - Sensor data (LoRa)
   - Camera temperature (Allsky)
   - CPU temperature (local)
   - External weather (Meet je Stad)
3. **Fail-safe behavior:** Local logic can implement safe defaults when sensor data is stale.
4. **Latency:** Safety decisions must be <5 seconds; LoRa + retry could exceed this.

**Safety Logic Examples:**
- Turn fans ON if any temperature threshold exceeded
- Turn heater OFF if temperature above dew point + margin
- Trigger rain alert if rain intensity below threshold AND alert active

### 2.5 Time, Synchronization, and Stale Data Handling

#### **Time Synchronization**
**Challenge:** LoRa sensor node may have clock drift; Raspberry Pi has NTP access.

**Solution:**
- Raspberry Pi timestamps all received data upon ingestion
- Sensor node includes relative timestamp (milliseconds since boot)
- Optional: Periodic time sync via LoRa downlink command
- Database stores "received_at" (Raspberry Pi time) + "sensor_time_offset" (if available)

#### **Stale Data Detection**
**Criteria:**
- **Sensor data age > 2x expected update interval** (e.g., >120 seconds if 60-second transmissions)
- **Missing consecutive updates > threshold** (e.g., 3 missed transmissions)

**Handling Strategy:**
1. **Log warning:** Record stale data event with timestamp
2. **UI indication:** Display sensor status as "OFFLINE" or "STALE" in dashboard
3. **Safety fallback:**
   - Continue using last known good values for non-critical displays
   - For safety decisions, apply conservative defaults:
     - Assume worst-case rain condition (trigger alerts)
     - Assume worst-case temperature (activate cooling)
4. **Alert escalation:** If stale duration > 10 minutes, send notification to operator

#### **Data Validation**
**Checks:**
- Range validation (e.g., temperature -40°C to +60°C)
- Rate-of-change limits (e.g., temperature cannot change >10°C in 60 seconds)
- Checksum verification (included in LoRa payload)
- Sensor status flags (from sensor node diagnostics)

### 2.6 Failure Isolation

#### **Sensor Node Failure**
**Impact:** No new sensor data received.
**Isolation:**
- Raspberry Pi continues operating with stale sensor data + safe defaults
- Allsky camera continues capturing images
- Meet je Stad data still available
- Web UI remains accessible, displays "SENSOR OFFLINE" status

**Recovery:**
- Automatic when sensor node resumes transmission
- No manual intervention required on Raspberry Pi

#### **Raspberry Pi Failure**
**Impact:** No safety decisions, no relay control, no data logging.
**Isolation:**
- Sensor node continues collecting data (optionally buffering)
- When Raspberry Pi recovers, historical data may be lost (depends on buffer size)

**Mitigation:**
- Watchdog timer for control.py service (auto-restart)
- UPS for Raspberry Pi (prevent abrupt shutdowns)
- Redundant sensor node buffer (store last N readings)

#### **Allsky Software Failure**
**Impact:** No camera temperature, star count, or day/night status.
**Isolation:**
- Safety Monitor continues with sensor data
- Fan control uses ambient temperature only
- Dashboard displays "CAMERA OFFLINE" for Allsky fields

**Recovery:**
- Independent of Safety Monitor operation
- Allsky has its own watchdog mechanisms

#### **LoRa Communication Failure**
**Impact:** Loss of sensor telemetry.
**Isolation:**
- Raspberry Pi detects stale data
- Applies safe defaults (see Stale Data Handling above)

**Diagnostics:**
- Check LoRa receiver module (SPI communication test)
- Check sensor node power/status LEDs
- Review LoRa packet logs for interference patterns

---

## STEP 3 – DATA CONTRACTS (CONCEPTUAL)

### 3.1 Sensor Telemetry Domains

#### **Domain 1: Rain and Wind**
**Source:** Hydreon RG-9 + RS485 Wind Sensor (currently Arduino Nano)  
**Update Rate:** 5 seconds (current), target 30-60 seconds (LoRa)  
**Data Fields:**
- `rain_intensity` (float): Analog rain sensor reading, 0-1023 range, lower = wetter
- `wind_speed` (float): Calculated wind speed in m/s or km/h, 0-70 m/s range

**Units and Semantics:**
- Rain: Raw ADC counts (0-1023), inverted scale, calibration applied in Safety Monitor
- Wind: Pulse count converted to speed, formula: (pulses * 8.75) / 100

**Expected Update Rate:** Every 30 seconds over LoRa

#### **Domain 2: Infrared Temperature**
**Source:** MLX90614 IR sensor (currently ESP8266)  
**Update Rate:** 30 seconds (current and target)  
**Data Fields:**
- `sky_temperature` (float): IR temperature of sky in °C, typical range -40°C to +40°C
- `ambient_temperature` (float): Sensor ambient temperature in °C, typical range -10°C to +50°C

**Units and Semantics:**
- Temperatures in Celsius with 0.01°C resolution
- Sky temperature < ambient indicates clear sky
- Delta used for cloud coverage calculation

**Expected Update Rate:** Every 30 seconds over LoRa

#### **Domain 3: Sky Quality**
**Source:** TSL2591 light sensor (currently ESP8266)  
**Update Rate:** 30 seconds (current and target)  
**Data Fields:**
- `sqm_ir` (integer): IR counts, range 0-65535
- `sqm_full` (integer): Full spectrum counts, range 0-65535
- `sqm_visible` (integer): Visible counts (full - IR), range 0-65535
- `sqm_lux` (float): Calculated lux value, sky quality metric

**Units and Semantics:**
- Raw counts from 16-bit ADC
- Lux calculated by TSL2591 library formula
- Used for brightness and Bortle scale computation

**Expected Update Rate:** Every 30 seconds over LoRa

#### **Domain 4: External Environmental Data**
**Source:** Meet je Stad Node 580 (external API)  
**Update Rate:** ~5 minutes (external system schedule)  
**Data Fields:**
- `temperature` (float): Ambient air temperature in °C
- `humidity` (float): Relative humidity in %, range 0-100

**Units and Semantics:**
- Professional-grade weather station data
- Used for dew point calculation and relay control
- Continues as-is, no changes required

#### **Domain 5: Camera and System Data**
**Source:** Allsky software + Raspberry Pi system  
**Update Rate:** Variable (camera per-image, system per control loop)  
**Data Fields:**
- `camera_temp` (integer): Camera sensor temperature in °C
- `star_count` (integer): Detected stars (night only)
- `day_or_night` (string): "DAY" or "NIGHT"
- `cpu_temperature` (integer): Raspberry Pi CPU temp in °C

**Units and Semantics:**
- Camera temp influences fan control (threshold: 25°C)
- Star count for observability (no control logic)
- CPU temp for system protection (threshold: 65°C)

### 3.2 LoRa Payload Strategy (Conceptual)

**Guiding Principles:**
- **Compact:** LoRa packets limited to ~51 bytes (SF7) or ~222 bytes (SF12)
- **Structured:** Fixed-length fields for predictable parsing
- **Extensible:** Version byte allows future schema evolution
- **Robust:** Include checksum for integrity verification

**Payload Structure (Conceptual):**
```
[ Header | Sensor Block 1 | Sensor Block 2 | ... | Footer ]

Header (3 bytes):
- Protocol version (1 byte)
- Sensor node ID (1 byte)
- Sequence number (1 byte)

Sensor Block (variable per domain):
- Domain ID (1 byte): 0x01 = Rain/Wind, 0x02 = IR Temp, 0x03 = SQM
- Data fields (type-specific encoding)

Footer (2 bytes):
- CRC16 checksum
```

**Example Encoding (Rain/Wind):**
```
Domain ID: 0x01
rain_intensity: uint16_t (2 bytes, scaled 0-1023)
wind_speed: uint16_t (2 bytes, scaled m/s * 100)
Total: 5 bytes
```

**Example Encoding (IR Temp):**
```
Domain ID: 0x02
sky_temperature: int16_t (2 bytes, scaled °C * 100)
ambient_temperature: int16_t (2 bytes, scaled °C * 100)
Total: 5 bytes
```

**Example Encoding (SQM):**
```
Domain ID: 0x03
sqm_ir: uint16_t (2 bytes)
sqm_full: uint16_t (2 bytes)
sqm_visible: uint16_t (2 bytes)
sqm_lux: uint32_t (4 bytes, IEEE 754 float)
Total: 11 bytes
```

**Full Packet Size Estimate:**
- Header: 3 bytes
- Rain/Wind: 5 bytes
- IR Temp: 5 bytes
- SQM: 11 bytes
- Footer: 2 bytes
- **Total: 26 bytes** (well within LoRa limits for SF7)

**Note:** Byte-level format and encoding details deferred to implementation phase.

### 3.3 Data Contract Versioning

**Strategy:**
- Version byte in header indicates contract version
- Raspberry Pi maintains decoder for multiple versions (backward compatibility)
- Sensor node firmware embeds version number
- Migration allows coexistence of old (USB) and new (LoRa) sensors

**Version History (Planned):**
- **v1:** Initial LoRa deployment, matches current USB serial JSON semantics
- **v2+:** Future schema enhancements (additional sensors, diagnostics)

---

## STEP 4 – MIGRATION STRATEGY

### 4.1 Phased Migration Plan

#### **Phase 0: Preparation (Pre-Migration)**
**Goal:** Establish baseline and acquire hardware.

**Tasks:**
1. Document current system performance metrics (data latency, reliability)
2. Order LoRa hardware:
   - Raspberry Pi LoRa receiver module (SX1276/RFM95W HAT or USB)
   - LoRa transceiver for sensor node (TTGO Lora32 or similar)
3. Create backup of current firmware and configuration
4. Set up development environment for LoRa firmware (PlatformIO or Arduino IDE)
5. Define test criteria for each phase

**Exit Criteria:**
- Hardware received and verified functional
- Baseline metrics documented
- Test plan approved

#### **Phase 1: Parallel Operation (Coexistence)**
**Goal:** Add LoRa sensor node while keeping USB serial sensors operational.

**Architecture:**
```
Raspberry Pi:
  ├─ USB Serial (existing): Arduino Nano + ESP8266
  └─ LoRa Receiver (new): Receives from LoRa sensor node
```

**Tasks:**
1. **Sensor Node Development:**
   - Port Arduino Nano + ESP8266 firmware to single LoRa-enabled board
   - Implement basic LoRa transmission (no retries yet)
   - Add sensor status diagnostics (battery level, signal strength)
   - Test LoRa range and packet success rate

2. **Raspberry Pi Modifications:**
   - Install LoRa receiver module (HAT or USB)
   - Add LoRa driver and packet decoder to `fetch_data.py`
   - Create new function: `get_lora_sensor_data()`
   - Modify `control.py` to accept data from BOTH USB and LoRa sources
   - Store data with source tag (`data_source: "USB"` or `"LoRa"`)

3. **Validation:**
   - Compare USB vs. LoRa data side-by-side in database
   - Monitor for discrepancies (calibration drift, timing issues)
   - Verify LoRa packet reception rate (target: >95%)
   - Check for LoRa interference or blind spots

**Duration:** 2-4 weeks

**Exit Criteria:**
- LoRa sensor node operational and transmitting
- Data from both sources logged simultaneously
- No significant data discrepancies (within sensor accuracy)
- Packet reception rate acceptable

#### **Phase 2: Validation and Tuning**
**Goal:** Optimize LoRa configuration and validate data quality.

**Tasks:**
1. **LoRa Parameter Tuning:**
   - Test different spreading factors (SF7 vs. SF12) for range vs. power
   - Adjust transmission power based on signal strength
   - Implement adaptive data rate if needed

2. **Data Quality Validation:**
   - Statistical analysis of USB vs. LoRa data (mean, std dev, outliers)
   - Measure latency from sensor reading to Raspberry Pi ingestion
   - Test stale data detection logic (simulate sensor node offline)

3. **Failure Scenario Testing:**
   - Disconnect sensor node (verify safe defaults applied)
   - Disconnect USB sensors (verify LoRa continues)
   - Interrupt LoRa communication (verify stale data handling)
   - Test recovery after power cycle of sensor node

4. **User Acceptance Testing:**
   - Dashboard displays both sources correctly
   - Relay control functions with LoRa data
   - Rain alerts trigger correctly
   - Configuration changes propagate to sensor node (if downlink implemented)

**Duration:** 1-2 weeks

**Exit Criteria:**
- LoRa data quality equivalent to USB data
- All failure scenarios handled gracefully
- User acceptance criteria met
- Go/no-go decision point PASSED

#### **Phase 3: Cutover**
**Goal:** Switch primary data source from USB to LoRa.

**Tasks:**
1. **Configuration Update:**
   - Modify `control.py` to prioritize LoRa data over USB
   - Set USB data as fallback only (deprecated warning in logs)
   - Update dashboard to indicate primary source

2. **Monitoring Period:**
   - Run in primary LoRa mode for 1 week with USB still connected
   - Monitor for unexpected issues
   - Keep USB sensors powered as safety backup

3. **Firmware Finalization:**
   - Add retry logic and acknowledgment to sensor node
   - Implement downlink command handling (optional)
   - Add OTA update capability (optional)

**Duration:** 1 week

**Exit Criteria:**
- System operates reliably with LoRa as primary source for 168 hours (7 days)
- No critical issues observed
- Fallback to USB not triggered unintentionally

#### **Phase 4: Decommissioning and Cleanup**
**Goal:** Remove USB serial sensors and legacy code.

**Tasks:**
1. **Physical Removal:**
   - Power down Arduino Nano and ESP8266
   - Disconnect USB cables
   - (Optional) Repurpose hardware for other projects

2. **Code Cleanup:**
   - Remove `get_rain_wind_data()` and `get_sky_data()` from `fetch_data.py`
   - Remove USB serial configuration from `settings.json`
   - Archive legacy firmware (`firmware/skymonitor/`, `firmware/wifi_sensors/`)
   - Update documentation (README.md)

3. **Final Validation:**
   - Confirm system boots and operates without USB sensors
   - Verify error logs do not show USB-related warnings
   - Update Fritzing diagrams to reflect new architecture

**Duration:** 1-2 days

**Exit Criteria:**
- USB sensors physically removed
- Legacy code archived (not deleted, for reference)
- Documentation updated
- System operational and clean

### 4.2 Risk Analysis and Mitigations

| **Risk** | **Likelihood** | **Impact** | **Mitigation** |
|----------|---------------|-----------|----------------|
| LoRa range insufficient | Medium | High | Phase 1 includes range testing; use higher SF or external antenna |
| Interference from other 868 MHz devices | Low | Medium | Use frequency hopping or listen-before-talk |
| Sensor node power failure (if battery) | Medium | High | Solar panel + large battery; low-power deep sleep modes |
| Data loss during migration | Low | Medium | Dual-source logging in Phase 1; keep USB operational until Phase 4 |
| Firmware bugs in LoRa node | Medium | Medium | Extensive testing in Phase 2; OTA update capability for fixes |
| Performance regression (latency) | Low | Low | Measure latency in Phase 2; LoRa latency <5 seconds acceptable |
| User error (wrong configuration) | Low | Medium | Default safe settings; web UI for configuration validation |

### 4.3 Rollback Plan

**Trigger Conditions:**
- Packet reception rate consistently <80% for 48 hours
- Unexplained sensor data anomalies causing false alerts
- Critical relay control malfunction attributed to LoRa data

**Rollback Procedure:**
1. Revert `control.py` to use USB serial as primary source
2. Comment out LoRa receiver code in `fetch_data.py`
3. Reconnect and power Arduino Nano + ESP8266
4. Verify USB data reception
5. Notify users of rollback and root cause investigation

**Post-Rollback:**
- Investigate failure mode (hardware, firmware, environmental)
- Fix issue in development environment
- Re-test before attempting Phase 1 again

---

## STEP 5 – OPEN QUESTIONS AND ASSUMPTIONS

### 5.1 Assumptions

1. **LoRa Hardware Availability:**
   - Assume standard SX1276/RFM95W modules compatible with Raspberry Pi (e.g., Dragino, Waveshare)
   - Assume Meet je Stad LoRa codebase (https://github.com/meetjestad/mjs_firmware) is adaptable to this use case

2. **Sensor Compatibility:**
   - Assume RG-9 and RS485 wind sensor can interface with ESP32/Arduino-compatible LoRa board
   - Assume MLX90614 and TSL2591 work on same I²C bus without address conflicts

3. **Power Requirements:**
   - **Option A:** Sensor node powered by mains (current wiring in place) → No battery concerns
   - **Option B:** Sensor node battery-powered → Requires solar panel or periodic charging

4. **Raspberry Pi LoRa Interface:**
   - Assume SPI-based LoRa HAT OR USB-based LoRa dongle available
   - Assume Python LoRa library (e.g., `pyLoRa`, `pySX127x`) functional and maintained

5. **Allsky Software Stability:**
   - Assume Allsky continues writing `/home/robert/allsky/tmp/allskydata.json` in current format
   - Assume no breaking changes in upstream Allsky project during migration

6. **Observatory Site Characteristics:**
   - Assume line-of-sight or near-line-of-sight between sensor node and Raspberry Pi
   - Assume distance <200 meters (typical LoRa SF7 range with good link budget)

7. **Regulatory Compliance:**
   - Assume 868 MHz ISM band usage complies with local regulations (EU)
   - Assume duty cycle limits (1% for 868 MHz) respected by transmission schedule

### 5.2 Open Questions Requiring Confirmation

#### **Hardware and Placement**
1. **Q1:** What is the physical distance between the current sensor enclosure and the Raspberry Pi?
   - **Why It Matters:** Determines LoRa spreading factor, antenna requirements, and expected link budget.
   - **Action Required:** Measure distance; assess line-of-sight obstructions.

2. **Q2:** Is the sensor enclosure currently wired for mains power, or is battery power required?
   - **Why It Matters:** Impacts hardware selection (power-hungry ESP32 OK vs. deep-sleep-optimized MCU required).
   - **Action Required:** Confirm current power source; decide if maintaining wired power or switching to battery.

3. **Q3:** What is the target form factor for the sensor node? Single board or modular?
   - **Why It Matters:** Options range from off-the-shelf TTGO Lora32 (integrated) to custom PCB (modular).
   - **Action Required:** Define budget, timeline, and complexity tolerance.

#### **LoRa Configuration**
4. **Q4:** Should the system support bidirectional communication (downlink commands)?
   - **Why It Matters:** Adds complexity but enables remote configuration updates and acknowledgments.
   - **Current Assumption:** Uplink-only initially; downlink optional for Phase 3.
   - **Action Required:** Decide if remote sensor configuration is a priority.

5. **Q5:** What is the acceptable data latency for safety decisions?
   - **Current Assumption:** <5 seconds acceptable; LoRa transmission + processing ~1-3 seconds.
   - **Action Required:** Confirm safety requirements; validate latency in Phase 2 testing.

6. **Q6:** Should multiple sensor nodes be supported (future expansion)?
   - **Why It Matters:** Requires node ID management and gateway design for multi-node networks.
   - **Current Assumption:** Single sensor node initially; architecture extensible to multi-node.
   - **Action Required:** Confirm if additional sensor locations planned.

#### **Meet je Stad Integration**
7. **Q7:** Is the code reference to Meet je Stad firmware (https://github.com/meetjestad/mjs_firmware) meant to inspire the LoRa protocol design, or directly reuse the codebase?
   - **Current Assumption:** Conceptual alignment (LoRa sensor node pattern), not direct code reuse.
   - **Action Required:** Clarify if MJS protocol compatibility is desired.

8. **Q8:** Should the new LoRa sensor node data be sent to the Meet je Stad network as well, or only to the local Raspberry Pi?
   - **Current Assumption:** Local-only communication; Meet je Stad Node 580 remains external.
   - **Action Required:** Confirm if integration with Meet je Stad infrastructure is desired.

#### **Allsky Integration**
9. **Q9:** Are there any known plans to upgrade or modify the Allsky software in the near term?
   - **Why It Matters:** Could impact stability of `/home/robert/allsky/tmp/allskydata.json` interface.
   - **Action Required:** Check Allsky project roadmap; subscribe to upgrade notifications.

10. **Q10:** Should the Safety Monitor remain a separate application, or eventually merge into Allsky as a module/plugin?
   - **Current Assumption:** Remain separate for maintainability and separation of concerns.
   - **Action Required:** Confirm long-term vision for integration depth.

#### **Migration and Testing**
11. **Q11:** What is the acceptable downtime window during cutover (Phase 3)?
   - **Current Assumption:** Zero downtime required; parallel operation ensures continuity.
   - **Action Required:** Confirm if any maintenance windows available.

12. **Q12:** Who will perform on-site validation and testing during Phase 1-3?
   - **Action Required:** Identify personnel with physical access to observatory.

13. **Q13:** What is the desired timeline for completing all 4 migration phases?
   - **Current Assumption:** 4-8 weeks total (assuming no major blockers).
   - **Action Required:** Confirm deadlines; adjust phase durations accordingly.

#### **Safety and Compliance**
14. **Q14:** Are there any observatory-specific safety regulations or insurance requirements affecting sensor placement or system design?
   - **Action Required:** Review site safety documentation.

15. **Q15:** What is the failure recovery procedure if both LoRa and USB sensors fail simultaneously?
   - **Current Assumption:** Manual intervention required; push notification alerts operator.
   - **Action Required:** Confirm manual failsafe procedure and notification escalation.

### 5.3 Architectural Trade-Offs

#### **Trade-Off 1: Centralized vs. Distributed Safety Logic**
**Option A (Selected):** Safety logic on Raspberry Pi (centralized)  
**Option B (Rejected):** Safety logic partially on sensor node (distributed)

**Rationale for A:**
- Simpler sensor node firmware
- Easier to update safety logic without OTA updates to sensor node
- Relay control physically near Raspberry Pi (GPIO)

**Consequence:**
- Sensor node becomes "dumb" telemetry transmitter
- Network failure impacts safety decisions (mitigated by stale data handling)

#### **Trade-Off 2: LoRa vs. WiFi**
**Option A (Selected):** LoRa for sensor communication  
**Option B (Rejected):** WiFi (as currently implemented with ESP8266)

**Rationale for A:**
- Greater range (LoRa >1 km vs. WiFi ~100 m)
- Lower power consumption (relevant if battery-powered)
- Fewer infrastructure dependencies (no WiFi network required at sensor location)
- Better aligned with remote sensor node use case

**Consequence:**
- More complex protocol (binary payload vs. JSON over WiFi)
- Additional hardware required (LoRa modules)
- Regulatory compliance (duty cycle limits)

#### **Trade-Off 3: Single Multi-Sensor Node vs. Multiple Single-Sensor Nodes**
**Option A (Selected):** Single node with all 4 sensors  
**Option B (Rejected):** Separate nodes per sensor type

**Rationale for A:**
- Simpler physical installation
- Fewer LoRa transmissions (lower network congestion)
- Reduced hardware cost

**Consequence:**
- Single point of failure (entire sensor node down affects all sensors)
- Larger sensor enclosure required

**Mitigation:** USB serial fallback during migration (Phase 1-2) provides redundancy.

---

## SUMMARY AND NEXT STEPS

### Architecture Highlights

1. **Modular Separation:** Clear boundary between allsky-camera (Raspberry Pi + Allsky + Safety Monitor) and allsky-sensors (standalone LoRa node).

2. **Safety-Critical Placement:** All decision logic and relay control remain on Raspberry Pi for reliability and multi-source integration.

3. **Stable Interfaces:**
   - Allsky → Safety Monitor: File-based JSON (no changes to Allsky)
   - Sensor Node → Safety Monitor: LoRa telemetry (versioned protocol)
   - External API → Safety Monitor: HTTPS REST (Meet je Stad, unchanged)

4. **Graceful Degradation:** Stale data and failure modes handled with safe defaults and operator notifications.

5. **Migration Safety:** 4-phase plan with parallel operation ensures zero-downtime transition.

### Dependencies

**Prerequisites for Implementation Mode:**
- **Confirmed:** Hardware selection (specific LoRa modules, board choice)
- **Confirmed:** Power strategy (mains vs. battery)
- **Confirmed:** Distance and line-of-sight assessment
- **Resolved:** Open questions Q1-Q15
- **Approval:** This architecture and migration plan

**Estimated Timeline:** 4-8 weeks for full migration (post-approval)

### Deliverables Upon Approval

1. **Design Documentation:** This document (ARCHITECTURE_PLAN.md) finalized
2. **Implementation Roadmap:** Detailed task breakdown for each phase
3. **Hardware BOM:** Parts list with links and cost estimates
4. **Test Plan:** Acceptance criteria and validation procedures
5. **Risk Register:** Updated risk tracking through implementation

---

## APPROVAL CHECKPOINT

**Do you approve this architecture and migration plan, or would you like changes before we proceed to implementation mode?**

**Specific Areas for Review:**
- Module responsibility boundaries (Section 2.2)
- LoRa payload structure (Section 3.2)
- Migration phase definitions (Section 4.1)
- Open questions requiring answers (Section 5.2)
- Architectural trade-offs (Section 5.3)

**Next Steps After Approval:**
1. Answer open questions Q1-Q15
2. Switch to Implementation Mode (or Code Mode if immediate development desired)
3. Begin Phase 0: Preparation tasks
