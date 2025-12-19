# Repository Reorganization and Implementation Governance

**Status:** Implementation Complete - Governance Updated
**Date:** 2025-12-19
**Last Updated:** 2025-12-19
**Purpose:** Document actual repository structure and governance after implementation

---

## STEP 1 — CURRENT WORKSPACE ANALYSIS

### 1.1 Current Repository Structure

```
skymonitor/ (workspace root)
├─ .vscode/              # VS Code configuration
├─ admin/                # Administrative scripts (backup, db import, upload commands)
├─ documentation/        # Architecture plans, diagrams, spreadsheets
├─ firmware/             # Arduino/ESP8266 firmware (LEGACY, to be archived)
│  ├─ skymonitor/        # Arduino Nano firmware (rain + wind sensors)
│  └─ wifi_sensors/      # ESP8266 D1 Mini firmware (MLX90614 + TSL2591)
├─ flask_session/        # Flask session data (runtime artifact)
├─ fritzing/             # Circuit diagrams for legacy USB serial setup
├─ lilygo/               # LILYGO T-Display firmware (display client)
├─ logs/                 # Runtime logs (not tracked in git)
├─ scripts/              # Utility scripts
├─ static/               # Flask web UI assets (favicon.ico)
├─ templates/            # Flask HTML templates
├─ test/                 # Test scripts for Safety Monitor components
├─ (root files)          # Python application modules for Safety Monitor
│  ├─ app.py             # Flask web server
│  ├─ control.py         # Main orchestration service
│  ├─ fetch_data.py      # Data acquisition from sensors/APIs
│  ├─ store_data.py      # SQLite database operations
│  ├─ settings.py        # Configuration management
│  ├─ weather_indicators.py # Cloud coverage/sky quality calculations
│  ├─ rain_alarm.py      # Rain alert Pushover notifications
│  ├─ system_monitor.py  # Raspberry Pi metrics collection
│  ├─ app_logging.py     # Logging utilities
│  ├─ requirements.txt   # Python dependencies
│  ├─ settings.json      # Active configuration (may contain secrets)
│  └─ sky_data.db        # SQLite database (runtime artifact)
└─ README.md             # Project documentation
```

### 1.2 Classification of Existing Code

#### **Category A: Active Safety Monitor Application (Will Remain Active)**
**Owner:** This project (skymonitor)  
**Purpose:** Raspberry Pi orchestration, data storage, web UI, safety logic  
**Will Change During Implementation:** YES (add LoRa backend API polling)

**Files:**
- `app.py` - Flask web server and API
- `control.py` - Main control loop (sensor fetch + relay control)
- `fetch_data.py` - Data acquisition module (ADD: LoRa backend polling function)
- `store_data.py` - SQLite database operations
- `settings.py` - Configuration loader
- `weather_indicators.py` - Sky quality calculations
- `rain_alarm.py` - Pushover notifications
- `system_monitor.py` - System metrics
- `app_logging.py` - Logging utilities
- `requirements.txt` - Python dependencies
- `templates/` - Flask HTML templates
- `static/` - Web UI assets
- `test/` - Test scripts
- `admin/` - Administrative scripts

---

#### **Category B: Legacy Firmware (Will Be Archived)**
**Owner:** This project (skymonitor)  
**Purpose:** Arduino Nano + ESP8266 USB serial sensor firmware (replaced by ESP32+RFM95)  
**Will Change During Implementation:** NO (archived, read-only reference)

**Files/Folders:**
- `firmware/skymonitor/` - Arduino Nano firmware (wind + rain, USB serial)
- `firmware/wifi_sensors/` - ESP8266 D1 Mini firmware (MLX90614 + TSL2591, USB serial)
- `firmware/READ.ME` - Legacy firmware notes

---

#### **Category C: Active Firmware (Implemented)**
**Owner:** This project (skymonitor)
**Purpose:** Heltec WiFi LoRa 32 V2 sensor node firmware (integrated ESP32 + SX1276)
**Status:** IMPLEMENTED (using OTAA, WiFi fallback, field-tested)

**Files/Folders:**
- `firmware/allsky-sensors/` - Heltec WiFi LoRa 32 V2 firmware (PlatformIO)
  - `platformio.ini` - PlatformIO project configuration
  - `src/main.cpp` - Main firmware (sensor acquisition + LoRa/WiFi transmission)
  - `src/lmic_project_config.h` - LMIC configuration
  - `src/secrets_template.h` - Template for credentials
  - `lib/` - Custom libraries
  - `include/` - Header files
  - `.gitignore` - Ignore build artifacts
  - `README.md` - Firmware documentation

---

#### **Category D: External References (NOT Owned, NOT Modified)**
**Owner:** External projects (Allsky, stoflamp)  
**Purpose:** Reference baselines, not part of this repository  
**Will Change During Implementation:** NO (external dependencies)

**External Projects:**
1. **Allsky Camera Software**
   - Location: `/home/robert/allsky/` (on Raspberry Pi, separate repository)
   - Integration Point: `/tmp/allskydata.json` (read-only file)
   - Upstream: https://github.com/AllskyTeam/allsky
   - Ownership: AllskyTeam (external)

2. **stoflamp Reference Design**
   - Location: `c:/github/stoflamp/` (separate repository, developer machine only)
   - Integration Point: Wiring patterns, firmware structure (reference only)
   - Upstream: Ed Smallenburg (personal project, not public)
   - Ownership: External (used as hardware/firmware baseline)

3. **Meet je Stad Firmware**
   - Location: https://github.com/meetjestad/mjs_firmware (external GitHub)
   - Integration Point: LoRa payload encoding concepts (reference only)
   - Ownership: Meet je Stad community (external)

---

#### **Category E: Configuration and Runtime Artifacts (Managed Separately)**
**Owner:** This project (skymonitor)  
**Purpose:** User-specific configuration, runtime data, logs  
**Will Change During Implementation:** YES (gitignored, user-managed)

**Files:**
- `.env` - Environment variables (API keys, secrets) - **git ignored**
- `settings.json` - Active configuration - **git tracked (without secrets)**
- `secrets.h` - WiFi credentials for legacy firmware - **git ignored**
- `sky_data.db` - SQLite database - **git ignored**
- `logs/` - Runtime logs - **git ignored**
- `flask_session/` - Flask session storage - **git ignored**

---

#### **Category F: Documentation and Diagrams (Active, Will Evolve)**
**Owner:** This project (skymonitor)  
**Purpose:** Architecture plans, wiring diagrams, reference docs  
**Will Change During Implementation:** PARTIALLY (add new docs, keep old as history)

**Files/Folders:**
- `documentation/` - All architecture and design documents
  - `ARCHITECTURE_PLAN.md` - Original architecture (v1)
  - `ARCHITECTURE_PLAN_V2.md` - Revised architecture with external LoRa backend
  - `HARDWARE_WIRING_STRATEGY.md` - Option A wiring plan (NEW)
  - `REPOSITORY_GOVERNANCE.md` - This document (NEW)
  - `Sky Quality Calculator.xls` - Legacy reference
  - `SkyMonitor 2.png` - System diagram
- `fritzing/` - Legacy USB serial circuit diagrams (ARCHIVE, not updated)

---

## STEP 2 — PROPOSED TARGET REPOSITORY STRUCTURE

### 2.1 Clean, Future-Proof Layout

```
skymonitor/ (workspace root)
│
├─ safety-monitor/                 # Raspberry Pi Safety Monitor Application
│  ├─ app.py                       # Flask web server
│  ├─ control.py                   # Main orchestration service
│  ├─ fetch_data.py                # Data acquisition (includes LoRa API polling)
│  ├─ store_data.py                # SQLite operations
│  ├─ settings.py                  # Configuration loader
│  ├─ weather_indicators.py        # Sky quality calculations
│  ├─ rain_alarm.py                # Rain alerts
│  ├─ system_monitor.py            # System metrics
│  ├─ app_logging.py               # Logging utilities
│  ├─ requirements.txt             # Python dependencies
│  ├─ settings.json                # Configuration (tracked, no secrets)
│  ├─ settings_example.json        # Template configuration
│  ├─ static/                      # Web UI assets
│  ├─ templates/                   # Flask HTML templates
│  ├─ test/                        # Test scripts
│  └─ README.md                    # Safety Monitor documentation
│
├─ firmware/                       # All microcontroller firmware
│  ├─ allsky-sensors/              # ESP32 + RFM95 LoRa sensor node (NEW, ACTIVE)
│  │  ├─ platformio.ini            # PlatformIO configuration
│  │  ├─ src/                      # Source code
│  │  │  └─ main.cpp               # Main firmware
│  │  ├─ include/                  # Headers
│  │  ├─ lib/                      # Custom libraries
│  │  ├─ test/                     # Firmware unit tests
│  │  └─ README.md                 # Firmware-specific documentation
│  │
│  ├─ legacy/                      # Archived legacy firmware (READ-ONLY)
│  │  ├─ arduino-nano/             # Renamed from skymonitor/
│  │  │  └─ skymonitor.ino         # Arduino Nano firmware (USB serial)
│  │  ├─ esp8266/                  # Renamed from wifi_sensors/
│  │  │  └─ wifi_sensors.ino       # ESP8266 firmware (USB serial)
│  │  └─ READ.ME                   # Legacy firmware notes
│  │
│  └─ display-client/              # LILYGO T-Display client (ACTIVE, separate concern)
│     └─ lilygo.ino                # Display firmware
│
├─ docs/                           # Documentation directory
│  ├─ architecture/                # Architecture and design docs
│  │  ├─ ARCHITECTURE_PLAN_V2.md   # System architecture (CURRENT)
│  │  ├─ board-esp32-lora-display/ # Board #4 - Heltec WiFi LoRa 32 V2 (CANONICAL)
│  │  │  ├─ ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md
│  │  │  └─ HARDWARE_WIRING_ESP32_LORA_DISPLAY.md
│  │  └─ legacy/                   # Superseded designs
│  │     ├─ ARCHITECTURE_PLAN_V1.md   # Original architecture
│  │     ├─ HARDWARE_WIRING_STRATEGY.md # Old wiring plan
│  │     └─ README.md
│  ├─ governance/                  # Repository and project governance
│  │  ├─ REPOSITORY_GOVERNANCE.md  # This document
│  │  └─ INTEGRATED_EXECUTION_PLAN.md # Implementation roadmap
│  ├─ reference/                   # Reference materials
│  │  ├─ Sky Quality Calculator.xls
│  │  ├─ SkyMonitor 2.png
│  │  └─ HTIT-WB32LA_V3.2.pdf
│  └─ fritzing/                    # Fritzing library files
│
├─ fritzing/                       # Circuit diagrams (ARCHIVE, not updated)
│  └─ (legacy diagrams for USB serial setup)
│
├─ admin/                          # Administrative scripts
│  ├─ db_backup.sh                 # Database backup
│  ├─ db_import.sh                 # Database import
│  ├─ reset_logs.sh                # Log cleanup
│  ├─ upload_wifi-ino.sh           # Legacy firmware upload
│  └─ 2do.me                       # TODO list
│
├─ .vscode/                        # VS Code configuration
├─ .env                            # Environment variables (git ignored)
├─ .gitignore                      # Git ignore rules
├─ example.env                     # Template environment variables
├─ secrets_example.h               # Template secrets for firmware
├─ README.md                       # Root project README
└─ skymonitor.code-workspace       # VS Code workspace file
```

### 2.2 Folder Purpose and Ownership

| Folder | Purpose | Ownership | Current Status |
|--------|---------|-----------|----------------|
| `safety-monitor/` | Raspberry Pi application (Flask, control logic) | This project | **ACTIVE** (manual control, robustness improvements added) |
| `firmware/allsky-sensors/` | Heltec WiFi LoRa 32 V2 sensor node firmware | This project | **ACTIVE** (OTAA + WiFi fallback implemented) |
| `firmware/legacy/` | Archived Arduino + ESP8266 firmware | This project | **ARCHIVED** (read-only reference) |
| `firmware/display-client/` | LILYGO T-Display firmware | This project | **ACTIVE** (independent subsystem) |
| `docs/` | All documentation (architecture, governance, reference) | This project | **MAINTAINED** (reflects actual implementation) |
| `fritzing/` | Legacy circuit diagrams | This project | **ARCHIVED** (legacy reference) |
| `admin/` | Maintenance scripts | This project | **MAINTAINED** (service management) |

---

## STEP 3 — MIGRATION PLAN FOR REPOSITORY REORGANIZATION

### 3.1 File Movement Operations

**Operation 1:** Archive Legacy Firmware
```
MOVE:
  firmware/skymonitor/         → firmware/legacy/arduino-nano/
  firmware/wifi_sensors/       → firmware/legacy/esp8266/
  firmware/READ.ME             → firmware/legacy/READ.ME
```

**Operation 2:** Reorganize Safety Monitor Application
```
MOVE (create new subfolder):
  app.py                       → safety-monitor/app.py
  control.py                   → safety-monitor/control.py
  fetch_data.py                → safety-monitor/fetch_data.py
  store_data.py                → safety-monitor/store_data.py
  settings.py                  → safety-monitor/settings.py
  weather_indicators.py        → safety-monitor/weather_indicators.py
  rain_alarm.py                → safety-monitor/rain_alarm.py
  system_monitor.py            → safety-monitor/system_monitor.py
  app_logging.py               → safety-monitor/app_logging.py
  requirements.txt             → safety-monitor/requirements.txt
  settings.json                → safety-monitor/settings.json
  settings_example.json        → safety-monitor/settings_example.json
  static/                      → safety-monitor/static/
  templates/                   → safety-monitor/templates/
  test/                        → safety-monitor/test/
```

**Operation 3:** Reorganize Documentation
```
MOVE:
  documentation/               → docs/
WITHIN docs/:
  ARCHITECTURE_PLAN.md         → docs/architecture/legacy/ARCHITECTURE_PLAN_V1.md
  ARCHITECTURE_PLAN_V2.md      → docs/architecture/ARCHITECTURE_PLAN_V2.md (CURRENT)
  HARDWARE_WIRING_STRATEGY.md  → docs/architecture/legacy/HARDWARE_WIRING_STRATEGY.md
  (NEW) Board #4 docs          → docs/architecture/board-esp32-lora-display/ (CANONICAL)
  REPOSITORY_GOVERNANCE.md     → docs/governance/REPOSITORY_GOVERNANCE.md
  INTEGRATED_EXECUTION_PLAN.md → docs/governance/INTEGRATED_EXECUTION_PLAN.md
  Sky Quality Calculator.xls   → docs/reference/Sky Quality Calculator.xls
  SkyMonitor 2.png             → docs/reference/SkyMonitor 2.png
  HTIT-WB32LA_V3.2.pdf         → docs/reference/HTIT-WB32LA_V3.2.pdf
```

**Operation 4:** Create New Firmware (COMPLETED)
```
CREATED:
  firmware/allsky-sensors/                    # Heltec WiFi LoRa 32 V2 firmware
  firmware/allsky-sensors/platformio.ini      # PlatformIO configuration
  firmware/allsky-sensors/src/main.cpp        # Main firmware (OTAA + WiFi fallback)
  firmware/allsky-sensors/src/lmic_project_config.h
  firmware/allsky-sensors/src/secrets_template.h
  firmware/allsky-sensors/include/
  firmware/allsky-sensors/lib/
  firmware/allsky-sensors/.gitignore
  firmware/allsky-sensors/README.md
  
  # Implementation documentation
  firmware/allsky-sensors/OTAA_JOIN_FIX_SUMMARY.md
  firmware/allsky-sensors/WIFI_FALLBACK_IMPLEMENTATION.md
  firmware/allsky-sensors/FIELD_TEST_MODE_DEPLOYMENT.md
```

**Operation 5:** Move LILYGO Firmware
```
MOVE:
  lilygo/                      → firmware/display-client/
```

**Operation 6:** Update Root-Level Files
```
UPDATE:
  README.md                    # Update to reflect new structure
  .gitignore                   # Ensure all runtime artifacts ignored
```

### 3.2 Git History Preservation Strategy

**Strategy:** Use `git mv` for file movements to preserve history.

**Example Commands:**
```bash
# Operation 1: Archive legacy firmware
git mv firmware/skymonitor firmware/legacy/arduino-nano
git mv firmware/wifi_sensors firmware/legacy/esp8266
git mv firmware/READ.ME firmware/legacy/READ.ME

# Operation 2: Create safety-monitor subfolder
mkdir safety-monitor
git mv app.py safety-monitor/app.py
git mv control.py safety-monitor/control.py
# ... repeat for all Python modules

# Operation 3: Reorganize docs
git mv documentation docs
mkdir -p docs/architecture docs/governance docs/reference
git mv docs/ARCHITECTURE_PLAN.md docs/architecture/ARCHITECTURE_PLAN_V1.md
# ... repeat for all docs

# Commit reorganization
git commit -m "Reorganize repository structure (safety-monitor, firmware, docs)"
```

**Why Git History Matters:**
- Allows `git log --follow <file>` to trace file history across renames
- Preserves authorship and commit messages for long-term maintainability
- Simplifies blame/annotate operations for debugging

### 3.3 What Remains Untouched

**Category A: External Dependencies (Not In This Repository)**
- Allsky software (`/home/robert/allsky/` on Raspberry Pi) - External project
- stoflamp reference (`c:/github/stoflamp/`) - External reference, not copied into this repo

**Category B: Runtime Artifacts (Git Ignored, User-Managed)**
- `sky_data.db` - SQLite database (user data, not tracked)
- `logs/` - Log files (runtime output, not tracked)
- `flask_session/` - Flask session data (runtime, not tracked)
- `.env` - Environment variables with secrets (not tracked)

**Category C: Configuration Templates (Tracked, But Not Modified)**
- `example.env` - Template for environment variables (tracked, unchanged)
- `secrets_example.h` - Template for firmware secrets (tracked, unchanged)

---

## STEP 4 — IMPLEMENTATION READINESS CHECK

### 4.1 Implementation Status Confirmed

**Architecture and Design:**
- [x] System architecture implemented (Board #4: Heltec WiFi LoRa 32 V2)
- [x] Hardware wiring documented (HARDWARE_WIRING_ESP32_LORA_DISPLAY.md)
- [x] Backend strategy implemented (The Things Network v3 with OTAA)
- [x] Hardware selected (Heltec WiFi LoRa 32 V2 - integrated ESP32 + SX1276)

**Hardware Decisions Made:**
- [x] **Wind sensor interface mode:** Pulse mode on GPIO34 with optocoupler
- [x] **Power supply strategy:** USB 5V power from Raspberry Pi
- [x] **Board selection:** Heltec WiFi LoRa 32 V2 (integrated LoRa + OLED)
- [x] **I²C bus separation:** Sensors on GPIO21/22, OLED on GPIO4/15

**Backend Configuration:**
- [x] **TTN coverage validated** (field tested with successful joins)
- [x] **TTN application created** (OTAA credentials configured)
- [x] **WiFi fallback implemented** (HTTP POST when LoRa unavailable)

**Repository Governance:**
- [x] **Repository reorganization completed** (safety-monitor/, firmware/ structure)
- [x] **File movement operations executed** (git mv operations complete)
- [x] **Git history preserved** (commit history intact)

### 4.2 Implementation Achievements

**Firmware Achievements:**
1. **OTAA Join Success:**
   - [x] Robust OTAA join with retry logic implemented
   - [x] Diagnostic fixes applied (OTAA_JOIN_FIX_SUMMARY.md)
   - [x] Field tested with successful TTN joins

2. **WiFi Fallback Implementation:**
   - [x] HTTP POST fallback when LoRa unavailable
   - [x] Documented in WIFI_FALLBACK_IMPLEMENTATION.md
   - [x] Field tested and verified functional

3. **Sensor Integration:**
   - [x] I²C bus separation (sensors vs OLED)
   - [x] MLX90614 IR temperature sensor
   - [x] TSL2591 sky quality meter
   - [x] RG-9 rain sensor (analog with voltage divider)
   - [x] Wind sensor (pulse counting on GPIO34)

### 4.3 Safety Monitor Application Updates

**Application Achievements:**
1. **Manual Control Feature:**
   - [x] Manual relay control added (MANUAL_CONTROL_FEATURE.md)
   - [x] Web UI controls for fan and heater
   - [x] Override system for testing

2. **Robustness Improvements:**
   - [x] Enhanced error handling (ROBUSTNESS_IMPROVEMENTS.md)
   - [x] Improved logging throughout codebase
   - [x] Better failure recovery mechanisms

3. **Serial Removal:**
   - [x] USB serial dependencies removed (SERIAL_REMOVAL_SUMMARY.md)
   - [x] Legacy Arduino/ESP8266 code archived
   - [x] Clean transition to WiFi/LoRa data sources

---

## STEP 5 — CURRENT IMPLEMENTATION STATUS

### 5.1 What Has Been Completed

**Repository Structure:** ✅ COMPLETE
- Safety Monitor code moved to `safety-monitor/` subdirectory
- Legacy firmware archived in `firmware/legacy/`
- Active firmware in `firmware/allsky-sensors/`
- Documentation organized in `docs/` with proper hierarchy

**Firmware Implementation:** ✅ SUBSTANTIALLY COMPLETE
- Heltec WiFi LoRa 32 V2 firmware operational
- OTAA join with TTN working
- WiFi fallback for HTTP POST working
- All sensors integrated and transmitting
- Field tested and deployed

**Application Updates:** ✅ COMPLETE
- Manual control feature added
- Robustness improvements applied
- USB serial removed
- Service files updated

### 5.2 Documentation Alignment Status

**What Needs Updating:**
- [x] This governance document (being updated now)
- [ ] Cross-references in README files to point to correct docs
- [ ] Ensure all links point to current canonical documentation

**Current Canonical Documentation:**
- **System Architecture:** [`docs/architecture/ARCHITECTURE_PLAN_V2.md`](../architecture/ARCHITECTURE_PLAN_V2.md)
- **Board Configuration:** [`docs/architecture/board-esp32-lora-display/`](../architecture/board-esp32-lora-display/)
- **Implementation Plan:** [`docs/governance/INTEGRATED_EXECUTION_PLAN.md`](INTEGRATED_EXECUTION_PLAN.md)
- **Legacy Designs:** [`docs/architecture/legacy/`](../architecture/legacy/)

---

## GOVERNANCE STATUS SUMMARY

**Repository Status:** IMPLEMENTED AND OPERATIONAL
**Governance Document Status:** UPDATED TO REFLECT ACTUAL STATE
**Last Verified:** 2025-12-19

The repository structure documented in Section 2.1 reflects the actual current state. All planned reorganization has been completed. Documentation should reference the current canonical sources listed in Section 5.2.
