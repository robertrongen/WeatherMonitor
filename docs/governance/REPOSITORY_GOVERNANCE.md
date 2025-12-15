# Repository Reorganization and Implementation Governance

**Status:** Pre-Implementation Governance Phase  
**Date:** 2025-12-15  
**Mode:** Architect Mode - No Code Changes Yet  
**Purpose:** Prepare clean repository structure before firmware implementation begins

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

#### **Category C: New Firmware (Will Be Created)**
**Owner:** This project (skymonitor)  
**Purpose:** ESP32 + RFM95 LoRa sensor node firmware (Option A)  
**Will Change During Implementation:** YES (new codebase, heavily inspired by stoflamp)

**Files/Folders (NEW):**
- `firmware/allsky-sensors/` - ESP32 + RFM95 firmware
  - `platformio.ini` - PlatformIO project configuration
  - `src/main.cpp` - Main firmware (sensor acquisition + LoRa transmission)
  - `lib/` - Custom libraries (if any)
  - `include/` - Header files
  - `.gitignore` - Ignore build artifacts

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
├─ docs/                           # Renamed from documentation/ for consistency
│  ├─ architecture/                # Architecture and design docs
│  │  ├─ ARCHITECTURE_PLAN_V1.md   # Original architecture (historical)
│  │  ├─ ARCHITECTURE_PLAN_V2.md   # Revised architecture (CURRENT)
│  │  └─ HARDWARE_WIRING_STRATEGY.md # Wiring plan (CURRENT)
│  ├─ governance/                  # Repository and project governance
│  │  ├─ REPOSITORY_GOVERNANCE.md  # This document
│  │  └─ IMPLEMENTATION_READINESS.md # Pre-coding checklist (NEW)
│  ├─ reference/                   # Reference materials
│  │  ├─ Sky Quality Calculator.xls
│  │  └─ SkyMonitor 2.png
│  └─ README.md                    # Documentation index
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

| Folder | Purpose | Ownership | Changes During Implementation? |
|--------|---------|-----------|-------------------------------|
| `safety-monitor/` | Raspberry Pi application (Flask, control logic) | This project | **YES** (add LoRa API polling) |
| `firmware/allsky-sensors/` | ESP32+RFM95 LoRa sensor node firmware | This project | **YES** (new, primary work) |
| `firmware/legacy/` | Archived Arduino + ESP8266 firmware | This project | **NO** (read-only reference) |
| `firmware/display-client/` | LILYGO T-Display firmware | This project | **NO** (independent subsystem) |
| `docs/` | All documentation (architecture, governance, reference) | This project | **YES** (add implementation logs) |
| `fritzing/` | Legacy circuit diagrams | This project | **NO** (archived reference) |
| `admin/` | Maintenance scripts | This project | **NO** (utility scripts unchanged) |

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
  ARCHITECTURE_PLAN.md         → docs/architecture/ARCHITECTURE_PLAN_V1.md
  ARCHITECTURE_PLAN_V2.md      → docs/architecture/ARCHITECTURE_PLAN_V2.md
  HARDWARE_WIRING_STRATEGY.md  → docs/architecture/HARDWARE_WIRING_STRATEGY.md
  REPOSITORY_GOVERNANCE.md     → docs/governance/REPOSITORY_GOVERNANCE.md
  Sky Quality Calculator.xls   → docs/reference/Sky Quality Calculator.xls
  SkyMonitor 2.png             → docs/reference/SkyMonitor 2.png
```

**Operation 4:** Create New Firmware Skeleton
```
CREATE (new directory structure):
  firmware/allsky-sensors/
  firmware/allsky-sensors/platformio.ini
  firmware/allsky-sensors/src/
  firmware/allsky-sensors/include/
  firmware/allsky-sensors/lib/
  firmware/allsky-sensors/test/
  firmware/allsky-sensors/README.md
  firmware/allsky-sensors/.gitignore
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

### 4.1 Prerequisites Confirmed

**Architecture and Design:**
- [x] System architecture approved (ARCHITECTURE_PLAN_V2.md)
- [x] Hardware wiring strategy approved (HARDWARE_WIRING_STRATEGY.md)
- [x] Backend strategy approved (The Things Network v3 with MQTT)
- [x] Decision matrix evaluated (Option A: ESP32+RFM95 single board selected)

**Hardware Decisions Locked:**
- [ ] **Wind sensor interface mode chosen** (Pulse + optocoupler OR RS485 + MAX485)
- [ ] **Power supply strategy confirmed** (USB 5V from Pi OR battery+solar OR mains adapter)
- [ ] **RFM95 reset pin handling decided** (Shared EN OR dedicated GPIO)
- [ ] **Component procurement approved** (Voltage divider resistors, optocoupler if pulse mode)

**Backend Configuration:**
- [ ] **TTN coverage validated** at observatory site (check TTN Mapper or deploy test node)
- [ ] **TTN application created** (DevEUI, AppEUI, AppKey generated)
- [ ] **MQTT vs. Webhook chosen** for Raspberry Pi integration (recommendation: MQTT)

**Repository Governance:**
- [ ] **Repository reorganization plan approved** (this document)
- [ ] **File movement operations reviewed** (Step 3.1)
- [ ] **Git history preservation strategy confirmed** (Step 3.2)

### 4.2 Open Decisions That MUST Be Resolved Before Coding

**Critical Hardware Decisions:**
1. **Wind Sensor Mode (Decision W1 from HARDWARE_WIRING_STRATEGY.md):**
   - [ ] Confirmed: Pulse mode with optocoupler (GPIO34)
   - [ ] Confirmed: RS485 mode with MAX485 (GPIO16/17)
   - **BLOCKER:** Cannot write firmware without this decision

2. **Component Procurement Status:**
   - [ ] ESP32 DevKit V1 ordered/available
   - [ ] RFM95W 868 MHz ordered/available
   - [ ] Voltage divider resistors (5.1kΩ + 10kΩ, 1%) ordered/available
   - [ ] Optocoupler 4N35 + resistors (1kΩ + 10kΩ) ordered/available (if pulse mode)
   - [ ] MAX485 module ordered/available (if RS485 mode)
   - **BLOCKER:** Cannot test firmware without hardware

3. **TTN Coverage Status:**
   - [ ] TTN gateway within range confirmed (check ttnmapper.org)
   - [ ] Fallback plan if no coverage (deploy own Chirpstack gateway?)
   - **BLOCKER:** Cannot deploy firmware without LoRa connectivity

### 4.3 Coding Model Governance

**Context:** You are currently operating in **Anthropic Claude Sonnet 4.5** (Architect Mode).

**For Implementation Phase:** Firmware and application coding will require a different model to optimize cost and performance.

**Available Models for Implementation:**
1. **MiniMax-M2** (RECOMMENDED for coding)
2. **xAI Grok Code Fast** (ALTERNATIVE for coding)

**Recommendation Will Be Provided in Step 5.**

---

## STEP 5 — MODEL CONFIRMATION CHECKPOINT

### 5.1 Coding Model Recommendation

**Recommended Model: MiniMax-M2**

**Rationale:**
1. **Cost Efficiency:** MiniMax-M2 optimized for coding tasks at lower token cost than Claude Sonnet 4.5.
2. **Code Quality:** Suitable for embedded C++ (ESP32/PlatformIO) and Python (Safety Monitor enhancements).
3. **Context Window:** Sufficient for firmware development with stoflamp reference patterns.
4. **Proven Track Record:** MiniMax-M2 performs well on structured coding tasks with clear specifications.

**Alternative: xAI Grok Code Fast** (Use if MiniMax-M2 unavailable or if real-time debugging with faster iteration needed)

**Why Switch from Claude Sonnet 4.5?**
Claude Sonnet 4.5 excels at architecture, analysis, and strategic planning (as demonstrated in this governance phase). However, for line-by-line firmware coding, schema definitions, and repetitive implementation patterns, a model optimized for coding workload provides better cost-performance balance without sacrificing quality when requirements are this clearly specified.

### 5.2 Final Pre-Implementation Checklist

**Before Switching to Implementation Mode, Confirm:**
- [ ] Repository reorganization plan approved (Step 3)
- [ ] File movement strategy clear (git mv operations documented)
- [ ] Hardware decisions locked (wind sensor mode, power supply, components ordered)
- [ ] Backend configuration ready (TTN app created, MQTT credentials available)
- [ ] Coding model selected (MiniMax-M2 or Grok Code Fast)
- [ ] Implementation sequence understood:
  1. Execute repository reorganization (git mv operations)
  2. Create firmware skeleton (platformio.ini, src/, include/)
  3. Port stoflamp LMIC initialization patterns
  4. Implement sensor acquisition logic
  5. Integrate TTN payload encoder
  6. Add Safety Monitor LoRa API polling

---

## FINAL QUESTION

**Do you approve this repository reorganization plan and confirm the coding model (MiniMax-M2 recommended), so I may switch to implementation mode?**

**If Approved:**
- Execute `git mv` operations to reorganize repository
- Switch to **MiniMax-M2** for firmware and application implementation
- Begin Phase 0 (stoflamp firmware baseline port to PlatformIO)

**If Modifications Needed:**
- Specify which folder structure or file movements require changes
- Clarify any remaining hardware decisions (wind sensor mode, power supply)
- Confirm alternative coding model if not MiniMax-M2
