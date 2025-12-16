# AllSky Safety Monitor - Revised Modular Architecture Plan (v2)

**Status:** Updated for Heltec WiFi LoRa 32 V2 (Board #4)
**Date:** 2025-12-16
**Mode:** Architecture Reference Document

---

## ⚠️ CANONICAL HARDWARE BASELINE (Updated 2025-12

-16)

**IMPORTANT:** This architecture has been finalized with **Heltec WiFi LoRa 32 V2** (Board #4) as the canonical sensor node hardware, replacing the previous generic ESP32 DevKit + external RFM95 design.

### Key Architectural Changes

1. **Integrated LoRa Radio** - Eliminates external SPI wiring (factory-integrated SX1276)
2. **Separate I²C Buses** - Sensors use GPIO21/22 (isolated from display bus GPIO4/15)
3. **Built-in OLED Display** - Field diagnostics without serial cable
4. **Reduced Assembly Complexity** - Single board vs dual-board design
5. **Smaller Enclosure** - Compact footprint (~50mm × 25mm)

### Canonical Pin Definitions

**For complete hardware specifications and wiring guide, see:**
- **Board Architecture:** [`board-esp32-lora-display/ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md`](board-esp32-lora-display/ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md)
- **Wiring Guide:** [`board-esp32-lora-display/HARDWARE_WIRING_ESP32_LORA_DISPLAY.md`](board-esp32-lora-display/HARDWARE_WIRING_ESP32_LORA_DISPLAY.md)

**Quick Reference - External Sensor Pins:**

| Sensor | GPIO | Signal | Notes |
|--------|------|--------|-------|
| MLX90614 (I²C) | GPIO21 (SDA), GPIO22 (SCL) | I²C 0x5A | **Separate sensor bus** |
| TSL2591 (I²C) | GPIO21 (SDA), GPIO22 (SCL) | I²C 0x29 | **Separate sensor bus** |
| RG-9 Rain (Analog) | GPIO36 | ADC | Voltage divider 5V→3.3V |
| Wind (Pulse) | GPIO34 | Interrupt | Optocoupler 10-30V→3.3V |
| Wind (RS485 Alt) | GPIO17 (RX), GPIO23 (TX) | UART2 | MAX485 transceiver |

**Legacy Hardware:** Previous ESP32 DevKit + external RFM95 documentation has been moved to [`legacy/HARDWARE_WIRING_STRATEGY.md`](legacy/HARDWARE_WIRING_STRATEGY.md) for reference.

---

## REVISION SUMMARY (Original v2 - 2025-12-15)

**Key Changes from v1:**
1. **Removed assumption of local LoRa receiver on Raspberry Pi**
2. **Introduced external LoRa backend as first-class component**
3. **Changed data flow:** Sensor Node → LoRa → Backend → HTTP API → Safety Monitor
4. **Mandatory RFM95 (SX127x) LoRa module requirement**
5. **Evaluated multiple sensor node architecture options (not limited to ESP32)**
6. **Backend strategy analysis for public/external LoRa termination**

---

## STEP 1 — REVISED TARGET ARCHITECTURE (NO LOCAL RECEIVER)

### 1.1 End-to-End Data Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                    ALLSKY-SENSORS MODULE                           │
│                  (Standalone LoRa Sensor Node)                     │
│                                                                    │
│  Hardware:                                                         │
│  - MCU (ESP32 / STM32 / SAMD / Arduino + shield)                   │
│  - RFM95 LoRa transceiver (SX127x)                                 │
│  - RG-9 rain sensor                                                │
│  - RS485 wind sensor (or pulse output mode)                        │
│  - MLX90614 IR temperature sensor (I²C)                            │
│  - TSL2591 sky quality meter (I²C)                                 │
│                                                                    │
│  Firmware Responsibilities:                                        │
│  - Sensor data acquisition every 30-60 seconds                     │
│  - Local validation and preprocessing                              │
│  - LoRa packet construction with node ID and sequence              │
│  - Transmission via RFM95 to external gateway                      │
└─────────────────────────┬──────────────────────────────────────────┘
                          │
                          │ LoRa Uplink 868 MHz (EU) / 915 MHz (US)
                          │ Spread Factors SF7-SF12
                          │ Public/Community Gateway Network
                          ▼
┌───────────────────────────────────────────────────────────────────┐
│                      LoRa BACKEND / GATEWAY                       │
│                   (External Infrastructure)                       │
│                                                                   │
│  Options:                                                         │
│  A) The Things Network (TTN v3)                                   │
│  B) Chirpstack (self-hosted or cloud)                             │
│  C) Meet je Stad network infrastructure                           │
│  D) Helium Network                                                │
│                                                                   │
│  Functions:                                                       │
│  - Receive LoRa packets from public gateways                      │
│  - Decode and store sensor telemetry                              │
│  - Expose HTTP(S) API for data retrieval                          │
│  - Authentication and access control                              │
└─────────────────────────┬─────────────────────────────────────────┘
                          │
                          │ HTTPS GET request
                          │ Polling interval: 30-60 seconds
                          │ Authentication: API key / token
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ALLSKY-CAMERA MODULE                           │
│                    (Raspberry Pi 4B 8GB)                            │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │            Allsky Software (Upstream - Unchanged)             │  │
│  │  - ZWO ASI224MC camera capture                                │  │
│  │  - Image processing and star detection                        │  │
│  │  - Web UI for camera viewing                                  │  │
│  │  - Writes: /home/robert/allsky/tmp/allskydata.json            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Safety Monitor Application                       │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │  Data Ingestion Layer                                   │  │  │
│  │  │  - HTTP API poller (fetch_data.py enhancement)          │  │  │
│  │  │  - Allsky JSON file reader (unchanged)                  │  │  │
│  │  │  - Meet je Stad API client (unchanged)                  │  │  │
│  │  │  - USB serial reader (parallel during migration)        │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │  Decision Logic Layer                                   │  │  │
│  │  │  - Stale data detection (API timestamp vs current)      │  │  │
│  │  │  - Safety threshold evaluation                          │  │  │
│  │  │  - Fan/heater control logic                             │  │  │
│  │  │  - Rain alert triggers                                  │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │  Output Layer                                           │  │  │
│  │  │  - Waveshare RPi Relay Board control (GPIO)             │  │  │
│  │  │  - SQLite database storage                              │  │  │
│  │  │  - Flask web server / REST API                          │  │  │
│  │  │  - Pushover notifications                               │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Hardware:                                                          │
│  - Raspberry Pi 4B 8GB                                              │
│  - ZWO ASI224MC camera                                              │
│  - Waveshare RPi Relay Board                                        │
│  - NO local LoRa receiver required                                  │
└─────────────────────────────────────────────────────────────────────┘
                          ▲
                          │
                          │ HTTPS GET (optional: external monitoring)
                          │
                  External Consumer
                  (e.g., smartphone app)
```

### 1.2 Architecture Summary

**Critical Change:** The Raspberry Pi Safety Monitor no longer receives LoRa packets directly. Instead:

1. **Sensor Node transmits to public/external LoRa network** (e.g., The Things Network, Chirpstack)
2. **Backend gateway infrastructure receives, decodes, and stores data**
3. **Backend exposes HTTP(S) API** with sensor telemetry (similar to Meet je Stad pattern)
4. **Safety Monitor polls API** every 30-60 seconds (same interval as USB serial readings)
5. **Safety Monitor treats LoRa data identically to Meet je Stad data:** external source via HTTP

**Advantages:**
- No additional hardware on Raspberry Pi (no LoRa HAT/USB dongle)
- Leverages existing public LoRa gateway infrastructure
- Sensor node has multiple reception paths LoRa gateways within range)
- API-based integration is already proven pattern (Meet je Stad node 580)
- Can monitor sensor health remotely via backend web UI

**Disadvantages:**
- Dependency on external backend service availability
- Additional network hop increases latency (typical: 1-5 seconds)
- Requires internet connectivity for Safety Monitor (already required for Meet je Stad and Pushover)
- Backend service must be configured and maintained

---

## STEP 2 — SENSOR NODE OPTIONS ANALYSIS (RFM95 REQUIRED)

### Common Requirements Across All Options

**Sensor Interfacing:**
- **RG-9 Rain:** Analog input (0-5V, inverted scale, lower = wetter)
- **Wind Sensor:**
  - **Option 1 (Pulse):** Digital interrupt pin, pulse counting, 10-30V supply tolerance
  - **Option 2 (RS485):** UART with RS485 transceiver (MAX485 or equivalent), 5V logic level
- **MLX90614:** I²C bus (address 0x5A), 3.3V or 5V compatible
- **TSL2591:** I²C bus (address 0x29), 3.3V compatible
- **RFM95:** SPI interface (MOSI, MISO, SCK, CS, RST, DIO0-DIO5), 3.3V logic

**Power Considerations:**
- Current setup: Both boards powered via USB (5V from external power supply)
- Future: Battery-powered node requires <100 mA average current (deep sleep between readings)
- Mains-powered node: No power budget constraints

**Environmental:**
- Outdoor enclosure (IP65+), temperature range -20°C to +50°C
- EMI from wind sensor pulse output (if used) requires filtering

---

### Option A: Consolidated Single-Board Node (ESP32 + RFM95)

**Architecture:**
Replace both Arduino Nano and ESP8266 D1 Mini with single ESP32 development board + RFM95 module.

**Hardware Components:**
- **ESP32 DevKit** (30-pin or 38-pin variant)
- **RFM95 LoRa module** (SX1276 868 MHz or 915 MHz)
- **Sensors:** All 4 sensors interface directly to ESP32
- **Power:** USB 5V OR 3.7V LiPo battery + solar panel

**Wiring Strategy:**
- **RFM95:** SPI pins (VSPI: GPIO5=CS, GPIO18=SCK, GPIO19=MISO, GPIO23=MOSI, GPIO2=RST, GPIO4=DIO0)
- **MLX90614 + TSL2591:** I²C (GPIO21=SDA, GPIO22=SCL), shared bus
- **RG-9 Rain:** ADC (GPIO36 or GPIO39, 12-bit, 0-3.3V range, needs voltage divider if sensor outputs >3.3V)
- **Wind Sensor:**
  - **Pulse Mode:** GPIO interrupt (GPIO34, with debounce, optocoupler for voltage isolation)
  - **RS485 Mode:** UART2 (GPIO16=RX, GPIO17=TX) + MAX485 transceiver

**Pros:**
- **Single firmware codebase:** Unified sensor acquisition logic, simpler maintenance
- **Rich peripheral support:** ESP32 has native SPI, I²C, multiple UARTs, ADC
- **WiFi available:** Useful for debugging (can log to MQTT or HTTP during development)
- **Large community:** ESP32 + RFM95 is well-documented (e.g., TTGO Lora32 projects)
- **Power management:** Deep sleep modes can achieve <10 µA in sleep (critical if battery-powered)
- **Lower overall cost:** Single board instead of two boards + USB cables

**Cons:**
- **Voltage domains:** RG-9 outputs 0-5V, ESP32 ADC max 3.3V → requires voltage divider (risk of incorrect calculation damaging ADC)
- **Wind sensor voltage:** If wind sensor pulses are 10-30V, requires optocoupler (additional component)
- **Firmware complexity:** All sensor drivers in one codebase, larger binary size, harder to isolate failures
- **Migration risk:** New hardware means full firmware rewrite, cannot incrementally port from Arduino/ESP8266
- **SPI conflicts if WiFi used:** ESP32 WiFi uses same SPI bus as RFM95 (manageable but requires careful mutex handling)

**Sensor Interface Feasibility:**
- **RG-9:** ✓ Feasible with voltage divider (2x 10kΩ resistors)
- **Wind (Pulse):** ✓ Feasible with 4N35 optocoupler + 10kΩ pull-up
- **Wind (RS485):** ✓ Feasible with MAX485 module (~$1)
- **MLX90614:** ✓ Direct connection, no issues
- **TSL2591:** ✓ Direct connection, no issues
- **RFM95:** ✓ Direct connection via SPI

**Enclosure Impact:**
- Single board reduces enclosure size
- Need space for RFM95 module (antenna SMA connector must be accessible)
- If battery-powered: Add LiPo battery + solar charge controller

**Firmware Complexity:**
- **Moderate:** ESP32 Arduino framework well-supported
- LoRa library: RadioHead or LMIC (LMIC preferred for TTN compatibility)
- Sensor drivers: Adafruit libraries available for MLX90614, TSL2591
- Wind sensor: Custom pulse counting or RS485 parser
- RG-9: Simple analogRead()
- Deep sleep management adds complexity

**Reliability:**
- **Single point of failure:** If ESP32 firmware crashes, all sensors offline
- Watchdog timer required for recovery from hangs
- SPI/I²C bus contention if not properly mutex-protected

**Migration Effort:**
- **High:** Complete firmware rewrite from two codebases to one
- Must replicate Arduino's wind pulse logic and ESP8266's sensor JSON output
- Testing period extended due to new hardware platform

**Long-term Maintainability:**
- **Good:** Single codebase easier to update than two separate firmwares
- ESP32 ecosystem actively maintained (Espressif support through 2030+)
- RFM95 modules commodity hardware (readily replaceable)

**Risks:**
- Incorrect voltage divider calculation → damaged ESP32 ADC
- SPI conflicts between WiFi and RFM95 → packet loss or lockups
- Firmware bugs affect all sensors simultaneously
- ESP32 supply shortages (improved recently but historically problematic)

---

### Option B: Dual-Board with LoRa Bridge

**Architecture:**
Keep existing Arduino Nano and ESP8266 D1 Mini largely unchanged. Add third board (LoRa Bridge) that aggregates USB serial JSON from both boards and transmits via RFM95.

**Hardware Components:**
- **Arduino Nano** (unchanged): RG-9 + wind sensor, USB serial JSON output
- **ESP8266 D1 Mini** (unchanged): MLX90614 + TSL2591, USB serial JSON output
- **LoRa Bridge Board:**
  - Microcontroller (Arduino Pro Mini, STM32 Blue Pill, or small ESP32)
  - RFM95 LoRa module
  - 2x USB-to-serial adapters OR 2x UART inputs
  - USB power OR independent power supply

**Wiring Strategy:**
- Phase 1 (prototyping): Arduino Nano → USB → LoRa Bridge; ESP8266 → USB → LoRa Bridge
- Phase 2 (final): Arduino → UART (GPIO) → Bridge; ESP8266 → UART (GPIO) → Bridge
- Bridge board: GPIO for 2x UART RX + SPI for RFM95

**Pros:**
- **Minimal firmware changes:** Arduino and ESP8266 firmware remain 95% identical to current
- **Incremental migration:** Can build and test bridge board independently, then swap connections
- **Fault isolation:** Sensor boards can be debugged independently via their own serial outputs
- **Proven sensor code:** Reuse existing, tested sensor acquisition logic
- **Lower initial risk:** Existing hardware continues working during bridge development

**Cons:**
- **Three boards instead of one:** Increased complexity in wiring, enclosure, and power distribution
- **Multiple points of failure:** Bridge board plus two sensor boards
- **Higher power consumption:** Three MCUs running (problematic if battery-powered)
- **Serial aggregation complexity:** Bridge must parse JSON from two sources, merge, and repackage for LoRa
- **Latency:** Extra hop through bridge adds 1-2 seconds
- **Cost:** Additional board, additional enclosure space, additional power wiring

**Sensor Interface Feasibility:**
- Same as current (unchanged sensor boards)
- Bridge board only handles UART serial communication (low complexity)

**Enclosure Impact:**
- Larger enclosure required for three boards
- More complex wiring harness (power distribution, serial connections)

**Firmware Complexity:**
- **Low on sensor boards:** Minimal changes (maybe remove WiFi debug code from ESP8266)
- **Moderate on bridge:** Must parse two JSON streams, merge into single LoRa payload
- If Arduino + ESP8266 send data at different intervals, bridge must handle asynchronous arrival
- Bridge watchdog must detect if sensor board hangs (no data received for N seconds)

**Reliability:**
- **Moderate:** Three independent failure points
- If bridge fails, sensors still operational (can be read via USB for debugging)
- If sensor board fails, other sensor board unaffected

**Migration Effort:**
- **Low:** Parallel development, minimal changes to existing firmware
- Bridge can be tested offline (feed test JSON via serial)
- Cutover is simple: redirect serial connections from Pi to bridge

**Long-term Maintainability:**
- **Poor:** Three codebases to maintain, more complex troubleshooting
- Higher ongoing burden for updates
- Difficult to justify once system is working (no clear path to consolidation)

**Risks:**
- Bridge firmware complexity (JSON parsing, asynchronous data handling)
- UART buffer overflows if sensor boards send data faster than bridge can process
- Power distribution issues (ground loops, noise on serial lines)
- Three-board system harder to explain and document for future maintainers

---

### Option C: Hybrid — Single Sensor Board + LoRa (Keep One Board)

**Architecture:**
Replace ONE existing board (either Nano or ESP8266) with ESP32+RFM95. Keep the other board operational, with ESP32+RFM95 acting as both sensor node and bridge.

**Variant C1:** Replace Arduino Nano, keep ESP8266
- ESP32+RFM95 handles RG-9 + wind sensor + RFM95 transmission
- ESP8266 continues with MLX90614 + TSL2591
- ESP32 reads ESP8266 JSON via serial, merges with own sensor data, transmits via LoRa

**Variant C2:** Replace ESP8266, keep Arduino Nano
- ESP32+RFM95 handles MLX90614 + TSL2591 + RFM95 transmission
- Arduino Nano continues with RG-9 + wind
- ESP32 reads Arduino Nano JSON via serial, merges with own sensor data, transmits via LoRa

**Hardware Components (Variant C1):**
- **ESP32 DevKit** + **RFM95**
- **ESP8266 D1 Mini** (unchanged)
- UART connection between ESP32 and ESP8266

**Hardware Components (Variant C2):**
- **ESP32 DevKit** + **RFM95**
- **Arduino Nano** (unchanged)
- UART connection between ESP32 and Arduino

**Pros:**
- **Partial reuse:** One board's firmware unchanged (lower migration risk)
- **Simpler than Option B:** Only two boards instead of three
- **Incremental path:** Can extend to full Option A later by migrating remaining sensors
- **Cost-effective:** Only one new board required initially

**Cons:**
- **Still two boards:** Not as clean as Option A
- **Serial dependency:** ESP32 depends on other board's serial output (latency, failure propagation)
- **Unclear benefit over Option A:** If replacing one board, why not replace both?
- **Asymmetric architecture:** Harder to explain and troubleshoot

**Sensor Interface Feasibility:**
- **C1:** ESP32 must handle RG-9 (voltage divider) + wind (pulse or RS485) → Same challenges as Option A
- **C2:** ESP32 must handle I²C sensors (MLX90614, TSL2591) → Easier than C1, no voltage domains

**Enclosure Impact:**
- Similar to current (two boards)
- Slightly more complex wiring for UART connection

**Firmware Complexity:**
- **Moderate:** ESP32 must parse serial JSON from other board + manage own sensors + LoRa
- Essentially a hybrid of Options A and B

**Reliability:**
- **Moderate:** Two failure points instead of one or three
- If unchanged board fails, ESP32 can continue with partial data (degrades gracefully)

**Migration Effort:**
- **Medium:** One new firmware to write, one existing firmware unchanged
- Testing complexity between single-board (A) and full bridge (B)

**Long-term Maintainability:**
- **Moderate:** Two codebases, but simpler than Option B
- Unclear upgrade path (stay hybrid or consolidate to Option A?)

**Risks:**
- Same sensor interface risks as Option A (depending on which sensors ESP32 handles)
- Serial communication reliability between boards

---

## STEP 2 DECISION MATRIX (MANDATORY)

| **Criterion**                     | **Option A: Single ESP32+RFM95**                   | **Option B: Dual Board + Bridge**                   | **Option C: Hybrid (ESP32+RFM95 + 1 Old Board)**      |
|-----------------------------------|----------------------------------------------------|-----------------------------------------------------|-------------------------------------------------------|
| **Architecture**                  | Consolidated single node                           | Three boards: Nano + ESP8266 + Bridge               | Two boards: ESP32+RFM95 replaces 1, keeps other       |
| **Boards/Components**             | ESP32 DevKit, RFM95, sensors, power                | Existing Nano + ESP8266 + new bridge MCU + RFM95    | ESP32+RFM95 + (Nano OR ESP8266)                       |
| **Sensors per Board**             | All 4 sensors on ESP32                             | Nano: rain+wind; ESP8266: IR+SQM; Bridge: LoRa     | ESP32: 2 sensors + LoRa; Other board: 2 sensors       |
| **RFM95 Integration**             | Direct SPI to ESP32                                | SPI to bridge board, serial from sensor boards      | Direct SPI to ESP32, serial from other board          |
| **Power Impact**                  | Single 5V supply OR 3.7V battery                   | Three 5V supplies (high if battery)                 | Two 5V supplies (moderate if battery)                 |
| **Enclosure Impact**              | Compact (1 board + RFM95 module)                   | Large (3 boards + wiring)                           | Medium (2 boards + RFM95)                             |
| **Firmware Complexity**           | Moderate (unified but larger codebase)             | Low sensors, Moderate bridge (JSON aggregation)     | Moderate (hybrid sensor+bridge logic)                 |
| **Reliability & Isolation**       | Single point of failure                            | Three failure points, better isolation              | Two failure points, partial isolation                 |
| **Migration Effort**              | High (full rewrite)                                | Low (minimal sensor board changes)                  | Medium (one board rewrite)                            |
| **Long-term Maintainability**     | High (single codebase, standard platform)          | Low (3 codebases, complex troubleshooting)          | Medium (2 codebases, unclear upgrade path)            |
| **Key Risks**                     | Voltage domain errors, SPI conflicts, firmware bug affects all | Bridge complexity, power distribution, 3x failures | Sensor interface risks (depends which sensors on ESP32) |
| **Cost**                          | Low (~$15 ESP32 + $10 RFM95)                       | Medium (~$35: all boards)                           | Low-Medium (~$25: ESP32+RFM95 + keep existing)        |
| **Overall Recommendation Score**  | **HIGH**                                           | **LOW**                                             | **MEDIUM**                                            |

### Justification for Recommendation: Option A (Single ESP32+RFM95)

**Recommended Choice: Option A**

Option A provides the cleanest long-term architecture with a single, maintainable firmware codebase and minimal hardware complexity. While migration effort is higher upfront, the result is a system that is easier to troubleshoot, update, and extend. Key advantages:

1. **Simplicity:** One board, one firmware, one SPI bus for LoRa, one I²C bus for sensors.
2. **Proven platform:** ESP32+RFM95 is widely used in LoRa sensor projects (TTGO Lora32, Heltec boards).
3. **Cost-effective:** Lower total component cost and simpler power distribution.
4. **Maintainability:** Future developers need only understand one codebase, not three.
5. **Enclosure:** Smallest footprint, easier to weatherproof.

**Voltage domain concerns (RG-9, wind sensor) are manageable with standard techniques (voltage divider, optocoupler) that are well-documented in ESP32 projects.**

Option B is rejected due to excessive complexity (3 boards, 3 codebases, poor long-term maintainability). Option C offers no clear advantage over A (if replacing one board anyway, may as well replace both for cleaner architecture).

---

## STEP 3 — BACKEND STRATEGY (CONCEPTUAL)

### 3.1 Backend Requirements

1. **Receive LoRa uplink packets** from public gateway network
2. **Decode sensor telemetry** from RFM95 transmission
3. **Store timestamped data** (persistent, with retention policy)
4. **Expose HTTP(S) API** for Safety Monitor consumption
5. **Authentication/Authorization** to prevent unauthorized access
6. **Monitoring/Alerting** (optional) for backend health

### 3.2 Backend Option Analysis

#### **Option X: The Things Network (TTN) v3**

**Description:**
TTN is a community-driven, global LoRaWAN network with free tier for public use. Provides application server with built-in HTTP integrations.

**How It Works:**
1. Register sensor node as "device" on TTN console (obtain DevEUI, AppEUI, AppKey)
2. Configure sensor node with OTAA (Over-The-Air Activation) credentials
3. Sensor node joins TTN network automatically when in range of public gateway
4. TTN decodes LoRa packets using user-defined payload decoder (JavaScript function)
5. Decoded data available via:
   - **TTN HTTP Integration:** Webhook pushes data to external server
   - **TTN MQTT API:** Subscribe to uplink messages
   - **TTN Data Storage Integration:** Redirect to third-party database (e.g., InfluxDB, PostgreSQL)

**Safety Monitor Changes Required:**
- **Polling Strategy:**
  - Option 3a: Store TTN webhook payloads in simple HTTP endpoint (Flask route on Raspberry Pi or separate microservice)
  - Option 3b: Subscribe to TTN MQTT broker (mqtt://eu1.cloud.thethings.network) from Raspberry Pi
  - Option 3c: Query TTN Application Data API (HTTPS REST, requires bearer token)
- **Authentication:** TTN API key in Raspberry Pi environment variables
- **Parsing:** TTN delivers decoded JSON (e.g., `{"rain_intensity": 123.4, "wind_speed": 5.6, ...}`)
- **Timestamp:** TTN includes `received_at` timestamp (ISO 8601 UTC)

**Advantages:**
- Free for reasonable usage (10 messages/day/node well within fair use)
- Public gateway coverage in urban/semi-urban areas (Netherlands has excellent coverage)
- Mature platform with good documentation
- Payload decoder allows custom JSON format (compatible with current data structure)
- Built-in device management, uplink logging, downlink capability

**Disadvantages:**
- Dependency on third-party service (TTN operational reliability)
- Coverage gaps in remote rural areas (need to check gateway map)
- Fair use policy limits (max 30 seconds airtime per day per device at SF12)
- API rate limits (60 requests/minute for HTTP Integration)
- TTN v3 migration required if using v2 (v2 EOL 2021, but some deployments linger)

**Complexity:**
- Low for sensor node (standard LMIC library with OTAA)
- Low for Safety Monitor (HTTP webhook or MQTT client, both well-supported in Python)

**Long-term Viability:**
- Good: TTN community-backed, open-source stack (Chirpstack-based)
- Recent funding and governance improvements (2023-2024)

---

#### **Option Y: Chirpstack (Self-Hosted or Cloud)**

**Description:**
Chirpstack is open-source LoRaWAN network server software. Can be self-hosted on VPS/cloud or run locally.

**How It Works:**
1. Deploy Chirpstack (Docker containers: network-server, application-server, Redis, PostgreSQL)
2. Configure packet forwarder on public gateway OR deploy own gateway (e.g., RAK gateway)
3. Register sensor node with Chirpstack application server
4. Chirpstack exposes gRPC + REST API for uplink data retrieval
5. Integrations available: HTTP, MQTT, InfluxDB, etc.

**Safety Monitor Changes Required:**
- Poll Chirpstack HTTP API (e.g., `/api/devices/{devEUI}/events`)
- Authentication via API key or JWT
- Parsing similar to TTN (JSON with application payload)

**Advantages:**
- Full control over infrastructure (no external dependency)
- No fair use limits (only limited by hardware resources)
- Can run on-premises (intranet, air-gapped if needed)
- Supports advanced features (geolocation, roaming, ADR)

**Disadvantages:**
- Requires gateway hardware (€200-500 for RAK or TTIG gateway)
- Infrastructure maintenance burden (updates, security patches, monitoring)
- Hosting costs if cloud-based (~$10-50/month for small VPS)
- Single gateway creates coverage SPOF (need redundancy for reliability)

**Complexity:**
- Moderate: Docker deployment, network configuration, SSL certificates
- Safety Monitor polling same as TTN (low complexity)

**Long-term Viability:**
- Excellent: Widely adopted in commercial IoT, actively maintained, strong community

---

#### **Option Z: Meet je Stad Network Integration**

**Description:**
Leverage existing Meet je Stad infrastructure (https://meetjestad.net) if compatible. MJS uses TTN backend with custom application server.

**How It Works:**
1. Coordinate with MJS community to register new sensor node
2. Configure node to transmit to MJS-associated TTN application
3. MJS stores data and exposes via existing `sensors_recent.php` endpoint
4. Safety Monitor queries: `https://meetjestad.net/data/?type=sensors&ids={NEW_NODE_ID}&format=json&limit=1`

**Safety Monitor Changes Required:**
- Add new URL to settings (e.g., `sensor_node_url`)
- Parse MJS JSON format (similar to existing `get_temperature_humidity()` function)
- Handle missing data gracefully (if node offline)

**Advantages:**
- **Minimal changes:** Reuses existing Meet je Stad integration pattern
- **Proven reliability:** MJS has been operational since 2016
- No additional backend setup required
- Free community service

**Disadvantages:**
- Dependency on MJS community (approval required, node must fit MJS objectives)
- MJS schema may not perfectly match sensor payload (e.g., RG-9 rain data not standard MJS field)
- Less control over data retention and access
- Public data visibility (MJS data is open, may not be desired for observatory-specific sensors)

**Complexity:**
- Very Low for Safety Monitor (copy existing MJS integration code)
- Low for sensor node (standard TTN integration)

**Long-term Viability:**
- Good: MJS has sustained operation for 8+ years, but depends on volunteer community

---

### 3.3 Backend Recommendation

**Recommended: Option X (The Things Network v3)**

**Rationale:**
1. **Zero infrastructure burden:** No gateway hardware or server maintenance required.
2. **Proven ecosystem:** Widely used, well-documented, strong community support.
3. **Good coverage:** Netherlands has dense TTN gateway network (verify specific site on TTN Mapper).
4. **Safety Monitor changes minimal:** Add HTTP webhook endpoint OR MQTT client (both standard Python patterns).
5. **Free tier sufficient:** 4 sensors × 60-second intervals × 30-byte payload = well within TTN fair use.

**Fallback:** If TTN coverage inadequate at site, deploy Option Y (Chirpstack + RAK gateway) with one-time hardware cost (~€250) but otherwise similar Safety Monitor integration.

**Not Recommended:** Option Z (MJS integration) unless MJS community explicitly supports non-standard weather station sensors (RG-9, MLX90614, TSL2591 are not typical MJS sensors).

---

## STEP 4 — DATA CONTRACTS (CONCEPTUAL)

### 4.1 Logical Sensor Data Models (Unchanged from v1)

**Sensor Domains:**
1. **Rain and Wind:** `rain_intensity` (float, 0-1023), `wind_speed` (float, m/s)
2. **IR Temperature:** `sky_temperature` (float, °C), `ambient_temperature` (float, °C)
3. **Sky Quality:** `sqm_ir` (int), `sqm_full` (int), `sqm_visible` (int), `sqm_lux` (float)

**Units and Semantics:** (same as v1)

**Update Rates:** Target 30-60 seconds per LoRa transmission

### 4.2 Timestamp Ownership and Drift Handling

**Backend-Assigned Timestamps:**
- Sensor node does NOT need RTC (real-time clock) → reduces cost and complexity
- Sensor node includes relative timestamp (milliseconds since boot) in payload as `sensor_uptime`
- Backend (TTN/Chirpstack) assigns authoritative timestamp upon packet reception: `received_at` (ISO 8601 UTC)
- Safety Monitor uses `received_at` for database storage and display

**Clock Drift Handling:**
- If sensor node reboots, `sensor_uptime` resets to zero → Not an issue, backend timestamp is authoritative
- For sequential packet loss detection: Backend includes `frame_counter` (LoRaWAN standard) that increments per transmission
- Safety Monitor compares `frame_counter` deltas to detect missing packets

**Time Synchronization:**
- Not required for safety logic (backend timestamps sufficient)
- Optional: If sensor node needs local timestamp for diagnostics, can implement LoRaWAN MAC commands (Class A devices support limited downlink)

### 4.3 Stale Data Detection and Safe Defaults

**Stale Data Criteria:**
- **Primary:** `received_at` timestamp age > 2× expected update interval (e.g., >120 seconds if 60-second transmissions)
- **Secondary:** Missing `frame_counter` sequence (gap > 3 consecutive frames)

**Safety Monitor Behavior When Data Stale:**

1. **Logging:** Record stale event with timestamp and last known good value
2. **UI Indication:** Dashboard displays "SENSOR OFFLINE" or "STALE (last update: HH:MM:SS ago)"
3. **Safety Fallback Defaults:**
   - **Rain intensity:** Assume worst-case (raining) → `rain_intensity = 0` (trigger alerts if alert_active)
   - **Wind speed:** Assume last known value (no safe default assumption)
   - **Sky temperature:** Continue using last value for cloud coverage (non-critical display)
   - **SQM values:** Continue using last value (non-critical display)
4. **Relay Control Impact:**
   - **Fan/Heater:** Use other available data sources (Allsky camera temp, Meet je Stad humidity, CPU temp) for decision
   - Do NOT shut down fan/heater based solely on missing sensor node data (fail-safe)
5. **Alert Escalation:** If stale duration > 10 minutes, send Pushover notification: "Warning: allsky-sensors node offline for 10+ minutes"

**Data Validation (Range Checks):**
- Rain: 0-1023 (enforce in firmware before transmission)
- Wind: 0-70 m/s (enforce in firmware)
- Sky temp: -60°C to +60°C (wider than expected for robustness)
- Ambient temp: -30°C to +60°C
- SQM values: 0-65535 (16-bit sensor range)
- If backend-decoded values exceed range → flag as invalid, apply stale data policy

**Checksum/Integrity:**
- LoRaWAN network layer includes MIC (Message Integrity Code) → No need for additional application-layer checksum
- If TTN/Chirpstack reports MIC failure, packet rejected before reaching Safety Monitor

---

## STEP 5 — MIGRATION PLAN UPDATE (REVISED FOR HTTP API)

### 5.1 Revised Phased Migration Plan

#### **Phase 0: Preparation (1-2 weeks)**

**Goals:**
- Acquire hardware for Option A (ESP32 + RFM95)
- Set up backend (TTN v3 application)
- Validate TTN gateway coverage at site

**Tasks:**
1. **Hardware Procurement:**
   - ESP32 DevKit (30-pin or 38-pin)
   - RFM95W 868 MHz LoRa module (Adafruit or HopeRF)
   - Voltage divider resistors for RG-9 (2x 10kΩ, 1%)
   - Optocoupler for wind sensor (4N35 or equivalent) if pulse mode
   - OR MAX485 module if RS485 mode preferred
   - Breadboard and jumper wires for prototyping
   - Antenna (868 MHz quarter-wave wire or stub antenna)

2. **TTN Setup:**
   - Create TTN account and application at https://console.cloud.thethings.network
   - Register sensor node device (select "Manually enter" for DevEUI, generate AppKey)
   - Define Payload Formatter (JavaScript decoder to convert binary to JSON)
   - Set up HTTP Integration (webhook URL or MQTT credentials)

3. **Coverage Validation:**
   - Check TTN Mapper (https://ttnmapper.org) for gateways within 5 km of site
   - If no coverage: Evaluate Option Y (Chirpstack + gateway) as fallback
   - Perform test transmission with TTGO Lora32 dev board (if available) at site

4. **Development Environment:**
   - Install PlatformIO OR Arduino IDE with ESP32 board support
   - Install LMIC library (MCCI LoRaWAN LMIC library, TTN-compatible)
   - Install sensor libraries (Adafruit TSL2591, SparkFun MLX90614)

5. **Baseline Metrics:**
   - Document current USB serial data latency (time from sensor reading to Pi ingestion)
   - Record current packet loss rate (should be ~0% over USB)
   - Measure current sensor update intervals (Arduino: 5s, ESP8266: 30s)

**Exit Criteria:**
- Hardware received and table-tested (sensor readings on breadboard)
- TTN application configured and receiving test packets
- Gateway coverage confirmed OR fallback plan approved
- Arduino IDE compiles example firmware successfully

---

#### **Phase 1: Parallel Operation (3-4 weeks)**

**Goals:**
- Deploy ESP32+RFM95 sensor node transmitting to TTN
- Safety Monitor polls TTN API in parallel with USB serial
- Validate data quality and LoRa reliability

**Architecture (Parallel Mode):**
```
Raspberry Pi Safety Monitor:
  ├─ fetch_data.py:
  │   ├─ get_rain_wind_data(USB1) → Arduino Nano (legacy)
  │   ├─ get_sky_data(USB0) → ESP8266 (legacy)
  │   └─ get_lora_sensor_data(TTN_API_URL) → ESP32+RFM95 (new, via TTN)
  └─ control.py:
      ├─ Tag data with source: "USB_Nano", "USB_ESP8266", "LoRa_TTN"
      └─ Store both sources in database for comparison
```

**Tasks:**

1. **Sensor Node Firmware Development:**
   - Port Arduino Nano logic (rain analog read, wind pulse counting) to ESP32
   - Port ESP8266 logic (MLX90614, TSL2591 I²C reads) to ESP32
   - Integrate LMIC library for TTN OTAA join
   - Construct LoRa payload (binary encoding, ~30 bytes)
   - Test transmission on bench (ESP32 → TTN → check console for uplinks)
   - Add deep sleep between transmissions (optional if battery-powered)

2. **TTN Payload Decoder:**
   - Write JavaScript decoder function in TTN console:
     ```
     Input: binary payload (hex string)
     Output: JSON {rain_intensity: X, wind_speed: Y, sky_temperature: Z, ...}
     ```
   - Test with sample payloads

3. **Safety Monitor Modifications (Raspberry Pi):**
   - **Option 3a (Webhook):**
     - Add Flask route `/webhook/ttn` to receive HTTP POST from TTN
     - Store received payload in temporary cache (e.g., Redis or in-memory dict)
     - `fetch_data.get_lora_sensor_data()` reads from cache
   - **Option 3b (MQTT):**
     - Install `paho-mqtt` library
     - Subscribe to `v3/{application_id}/devices/{device_id}/up` topic
     - Parse MQTT message, extract decoded payload
   - **Option 3c (HTTP API):**
     - Poll TTN Application Data API: `GET /api/v3/as/applications/{app_id}/packages/storage/uplink_message`
     - Requires bearer token in `Authorization` header
   - **Recommended:** Option 3b (MQTT) for lowest latency and simpler implementation

4. **Parallel Logging:**
   - Modify `control.py` to call both USB and TTN fetch functions
   - Store data with `data_source` column: "USB_legacy" or "LoRa_TTN"
   - Add comparison script to query database and compute differences:
     - Mean absolute error for each sensor
     - Missing data percentage
     - Timestamp delta (latency difference)

5. **Physical Deployment:**
   - Install ESP32+RFM95 node in weatherproof enclosure at sensor site
   - Keep Arduino Nano + ESP8266 connected to Raspberry Pi (USB)
   - Run for 2-3 weeks continuously

**Validation Criteria:**
- LoRa packet reception rate ≥95% (measured via TTN "Last Seen" timestamps)
- Data discrepancies <5% (accounting for sensor noise)
- End-to-end latency <10 seconds (sensor reading → TTN → Pi ingestion)
- No correlation between LoRa packet loss and time of day (indicates interference)

**Exit Criteria:**
- Validation criteria met for 7 consecutive days
- No safety-critical failures (relay control unchanged during test)
- User acceptance testing passed (dashboard displays both data sources correctly)

---

#### **Phase 2: Validation and Tuning (1-2 weeks)**

**Goals:**
- Optimize LoRa transmission parameters (SF, power)
- Test failure scenarios
- Finalize data source prioritization logic

**Tasks:**

1. **LoRa Parameter Tuning:**
   - Test different Spreading Factors (SF7, SF9, SF12) to balance range vs. airtime
   - Adjust transmission power (14 dBm default, can reduce to 10 dBm if gateways close)
   - Measure Time-on-Air (ToA) and ensure <30 seconds per transmission per day (TTN fair use)

2. **Failure Scenario Testing:**
   - **Scenario 1:** Power-cycle sensor node → verify OTAA rejoin successful
   - **Scenario 2:** Move node to fringe coverage area → measure packet loss increase
   - **Scenario 3:** Disable TTN API access (revoke token) → verify Safety Monitor detects stale data
   - **Scenario 4:** Induce firmware crash (watchdog test) → verify node recovery
   - **Scenario 5:** Disconnect USB sensors → verify relay control continues with LoRa data only

3. **Stale Data Handling Validation:**
   - Manually halt sensor node transmissions
   - Verify dashboard displays "SENSOR OFFLINE" within 2 minutes
   - Verify Pushover notification sent after 10 minutes
   - Verify relay control applies safe defaults

4. **Latency Analysis:**
   - Measure end-to-end latency at each stage:
     - Sensor acquisition: ~1 second
     - LoRa transmission: <1 second
     - Gateway → TTN: <2 seconds
     - TTN → Pi (MQTT): <1 second
     - Total: <5 seconds (acceptable for safety decisions)

5. **Data Source Prioritization:**
   - Modify `control.py` to prioritize LoRa data over USB if both available
   - Add logic: "If LoRa data age <120 seconds, use LoRa; else fallback to USB"

**Exit Criteria:**
- LoRa parameters optimized (SF selection, power setting documented)
- All failure scenarios handled gracefully
- Latency within acceptable bounds
- Data source prioritization logic tested and approved
- Go/No-Go decision: Approve Phase 3 cutover

---

#### **Phase 3: Cutover (1 week)**

**Goals:**
- Switch Safety Monitor to use LoRa as primary data source
- USB sensors remain connected but deprecated

**Tasks:**

1. **Configuration Update:**
   - Update `settings.json`: Add `lora_data_url` or `ttn_mqtt_broker`
   - Modify `control.py`: Remove USB data from normal flow, keep as emergency fallback
   - Add deprecation warnings in logs: "USB serial data deprecated, LoRa primary"

2. **Monitoring Period:**
   - Run with LoRa primary for 7 consecutive days
   - Monitor for unexpected behavior (relay control anomalies, missing data)
   - Keep USB sensors powered but only log data to separate "fallback" table

3. **Firmware Finalization:**
   - Add retry logic for failed transmissions (LMIC handles this automatically)
   - Add battery voltage monitoring (if battery-powered)
   - Add diagnostic payload fields (RSSI, SNR, frame counter)
   - Enable watchdog timer for fault recovery

4. **Documentation:**
   - Update README.md with LoRa setup instructions
   - Document TTN application configuration
   - Create troubleshooting guide (common failure modes)

**Exit Criteria:**
- System operates reliably with LoRa primary for 168 hours (7 days) without incident
- No unintended fallback to USB data
- Documentation reviewed and approved

---

#### **Phase 4: Decommissioning (1-2 days)**

**Goals:**
- Remove USB sensors and legacy firmware
- Archive code for reference

**Tasks:**

1. **Physical Removal:**
   - Power down Arduino Nano and ESP8266 D1 Mini
   - Disconnect USB cables from Raspberry Pi
   - Remove from enclosure (optional: repurpose boards for future projects)

2. **Code Cleanup:**
   - Remove `get_rain_wind_data()` and `get_sky_data()` USB functions from `fetch_data.py`
   - Remove `serial_port_rain` and `serial_port_json` from `settings.json`
   - Move `firmware/skymonitor/` and `firmware/wifi_sensors/` to `firmware/legacy/`
   - Add README in legacy folder: "Archived USB serial firmware, replaced by ESP32+RFM95 LoRa"

3. **Final Validation:**
   - Reboot Raspberry Pi, verify services start without USB serial errors
   - Check logs for no USB-related warnings
   - Verify dashboard displays LoRa data only

4. **Backup:**
   - Create full system backup (database, settings, firmware code)
   - Store backup off-site or in version control

**Exit Criteria:**
- USB sensors removed and archived
- System operational with LoRa-only data source
- No legacy code warnings in logs
- Migration complete

---

### 5.2 Acceptance Criteria Summary

**Data Quality:**
- LoRa data accuracy within ±5% of USB baseline (accounting for sensor noise)
- No systematic bias in LoRa readings

**Reliability:**
- Packet reception rate ≥95% over 7-day period
- Graceful handling of stale data (no false alarms)

**Latency:**
- End-to-end latency <10 seconds (sensor → TTN → Pi)
- Safety decisions execute within 5 seconds of data availability

**Safety:**
- Relay control functions correctly with LoRa data
- Rain alerts trigger correctly (no false negatives)
- Fail-safe behavior during sensor node offline periods

**Usability:**
- Dashboard displays LoRa data source clearly
- Settings UI allows configuration of TTN API credentials
- Troubleshooting logs include LoRa-specific diagnostics

---

## STEP 6 — DECISIONS, QUESTIONS, AND APPROVAL REQUEST

### 6.1 Recommended Decisions

**Decision 1: Sensor Node Architecture**
- **Recommendation:** Option A (Single ESP32 + RFM95)
- **Rationale:** Best long-term maintainability, lowest complexity, proven platform

**Decision 2: Backend Infrastructure**
- **Recommendation:** The Things Network v3
- **Rationale:** Zero infrastructure cost, good coverage, mature ecosystem
- **Fallback:** Chirpstack + RAK gateway if TTN coverage insufficient

**Decision 3: Backend Integration Method**
- **Recommendation:** MQTT client on Raspberry Pi
- **Rationale:** Lowest latency, simpler than webhook infrastructure, well-supported Python library

**Decision 4: Migration Timeline**
- **Recommendation:** 6-8 weeks total (Phase 0-4)
- **Rationale:** Allows thorough testing, minimizes risk, fits within operational constraints

**Decision 5: Wind Sensor Interface**
- **Recommendation:** Use pulse output mode with optocoupler (simpler than RS485)
- **Rationale:** Current Arduino firmware uses pulse counting successfully, easier to port

---

### 6.2 Decisions Requiring Your Confirmation

1. **Power Strategy:**
   - **Option A:** Continue mains/USB power to sensor node (simplest)
   - **Option B:** Battery + solar panel (requires charge controller, larger enclosure)
   - **Question:** Is sensor node location accessible for 5V USB power, or must it be battery-powered?

2. **TTN Coverage:**
   - **Question:** What is the physical address or coordinates of the observatory site?
   - **Action:** Check TTN Mapper for gateway coverage before committing to TTN backend

3. **Wind Sensor Voltage:**
   - **Question:** Does the RS485 wind sensor support pulse output mode, or is RS485 UART mandatory?
   - **Context:** Pulse mode is simpler to interface with ESP32 (one GPIO + optocoupler vs. UART + MAX485)

4. **Downlink Commands:**
   - **Question:** Should sensor node support configuration updates via LoRa downlink (e.g., change transmission interval)?
   - **Trade-off:** Adds complexity but enables remote management
   - **Recommendation:** Not required initially, can be added in future firmware update

5. **Data Visibility:**
   - **Question:** Should sensor data be private (TTN application visible only to you), or public (e.g., integrate with MJS network)?
   - **Recommendation:** Keep private initially for simplicity

6. **Firmware Update Strategy:**
   - **Question:** Is physical access to sensor node feasible for firmware updates, or is OTA (Over-The-Air) required?
   - **Context:** OTA via LoRa is complex and slow; OTA via WiFi (ESP32 native) is simpler but requires WiFi at sensor site

---

### 6.3 Open Questions (Unresolved)

1. **Q1:** Exact distance from sensor enclosure to nearest TTN gateway? (Impacts SF selection, range feasibility)

2. **Q2:** Current enclosure dimensions and weatherproofing rating? (Determines if ESP32+RFM95 fits without new enclosure)

3. **Q3:** Is observatory site internet-connected continuously? (Required for Safety Monitor to poll TTN API)

4. **Q4:** Preferred dashboard indication when LoRa data is stale? (Text message, color change, icon, audio alert?)

5. **Q5:** Should historical USB serial data be migrated to new schema, or keep separate for comparison?

6. **Q6:** If TTN coverage is insufficient, is €250 budget approved for Chirpstack gateway deployment?

7. **Q7:** Should sensor node transmit diagnostics (RSSI, SNR, battery voltage) in addition to sensor data?

8. **Q8:** Acceptable downtime window during Phase 3 cutover? (Assume zero downtime via parallel operation, but confirm)

9. **Q9:** Who will perform physical sensor node installation and initial commissioning?

10. **Q10:** Should this architecture support future expansion to multiple sensor nodes (e.g., second location for redundancy)?

---

### 6.4 Assumptions

1. **Assumption 1:** Observatory site is within TTN gateway coverage (to be validated in Phase 0)

2. **Assumption 2:** Raspberry Pi has persistent internet connectivity for TTN API polling

3. **Assumption 3:** Current sensor wiring can be transferred to ESP32 GPIO pins (RG-9 analog, wind pulse/RS485, I²C devices)

4. **Assumption 4:** Safety Monitor can tolerate 5-10 second latency for sensor data (vs. <1 second for USB serial)

5. **Assumption 5:** Allsky software will continue writing `/home/robert/allsky/tmp/allskydata.json` in current format (no breaking changes from upstream)

6. **Assumption 6:** USB serial sensors (Arduino Nano, ESP8266) will remain available for fallback during Phase 1-2 (parallel operation)

7. **Assumption 7:** Fair use limits of TTN are acceptable (30 seconds airtime/day → supports ~100 transmissions at SF7 or ~10 transmissions at SF12)

8. **Assumption 8:** Sensor node does not require real-time clock (backend assigns timestamps)

9. **Assumption 9:** ESP32 voltage domain concerns (3.3V ADC) can be resolved with voltage divider for RG-9 sensor

10. **Assumption 10:** Meet je Stad Node 580 external API integration continues unchanged (no dependency on new sensor node)

---

### 6.5 Summary of Required Approvals

**Approve the Following:**
1. **Sensor Node Architecture:** Option A (ESP32 + RFM95 single board)
2. **Backend Infrastructure:** The Things Network v3 with MQTT integration
3. **Migration Timeline:** 6-8 weeks, 4-phase plan with parallel operation
4. **Data Contracts:** Backend-assigned timestamps, stale data handling, safe defaults
5. **Budget:** ~€30 for ESP32 + RFM95 + components (+ €250 for gateway if TTN coverage insufficient)

**Confirm Decisions:**
- Power strategy (USB/mains vs. battery)
- Wind sensor interface mode (pulse vs. RS485)
- Data visibility (private vs. public)
- Firmware update strategy (physical access vs. OTA)

**Answer Open Questions:**
- Site location coordinates (for TTN coverage check)
- Current enclosure specifications
- Internet connectivity reliability
- Budget approval for fallback gateway

---

## NEXT STEPS AFTER APPROVAL

1. **Phase 0 Begins:** Hardware procurement, TTN account setup, coverage validation
2. **Detailed Design:** Pin mappings, circuit diagrams, Fritzing updates
3. **Firmware Skeleton:** Create repository structure, initialize PlatformIO project
4. **Safety Monitor Code Scaffolding:** Add MQTT client stub, TTN API parser stub
5. **Testing Protocol:** Define bench test procedures, field test checklist

**Estimated Time to First Transmission:** 2-3 weeks after approval (Phase 0 complete)

---

## APPROVAL CHECKPOINT

**Do you approve this revised architecture and recommended option (ESP32+RFM95 with TTN backend), or would you like changes before we proceed to implementation mode?**

**Specific Areas for Final Review:**
- Decision Matrix (Section 2, table comparing Options A/B/C)
- Backend strategy (TTN vs. Chirpstack vs. MJS)
- Migration phasing (Section 5.1, especially parallel operation approach)
- Open questions requiring your input (Section 6.2, 6.3)

**If Approved:**
- Confirm decisions in Section 6.2
- Provide answers to open questions in Section 6.3
- Mode switch to Code or Implementation mode for Phase 0 execution
