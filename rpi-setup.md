# Raspberry Pi Setup – AllSky Safety Monitor (Ground Truth)

This document summarizes the **known-good Raspberry Pi setup** for the **AllSky Camera + Safety Monitor** system.
It is intended to quickly ground new debugging sessions and avoid re-diagnosing already solved issues.

---

## Hardware Context

- Platform: Raspberry Pi (64-bit)
- OS: Raspberry Pi OS **Trixie** (Debian-based)
- Camera:
  - AllSky camera connected to the Raspberry Pi
  - Operated by the AllSky software stack
- GPIO used:
  - Relay module (active-low)
  - Fan and heater controlled via GPIO
- GPIO access via `/dev/gpiomem`

---

## AllSky Camera Integration

- The Raspberry Pi runs **AllSky camera software** in parallel with the Safety Monitor
- AllSky is responsible for:
  - Camera capture
  - Image processing
  - Web UI for sky images
- Safety Monitor is responsible for:
  - Environmental safety decisions
  - Fan and heater control
  - Protecting camera and enclosure hardware

### Interaction Model

- AllSky and Safety Monitor run as **separate services**
- There is **no shared GPIO access**
- Safety Monitor does **not** control the camera directly
- Integration is **loose and resilient**:
  - If AllSky stops, Safety Monitor continues protecting hardware
  - If Safety Monitor stops, AllSky may still capture images (not safe long-term)

This separation is **intentional**.

---

## High-Level Architecture

The system is intentionally split into two Python services for the Safety Monitor:

### 1. Control Service (`control.py`)

- Owns **all GPIO access**
- Runs continuously
- Implements safety logic and fallback behaviour
- Exposes a **local-only Flask API** on:
<http://127.0.0.1:5001>

markdown
Copy code

- Example endpoints:
- `GET /status`
- `POST /actuators`

### 2. App Service (`app.py`)

- Provides the Safety Monitor web UI
- Runs on:
http://<hostname>:5000

yaml
Copy code

- Never touches GPIO directly
- Communicates with `control.py` via HTTP

This split is **intentional and correct**.
There is **no port conflict** between AllSky, port 5000, and port 5001.

---

## Python Environment (Critical)

### Virtual Environment Requirements

A Python virtual environment **must** be used, but it **must include system site packages**.

Correct creation:

```python3 -m venv venv --system-site-packages```

Why this is required:

- GPIO backend (lgpio) is installed system-wide via APT
- Standard venvs cannot see system packages
- Without --system-site-packages, GPIO silently falls back to mock mode
- Result: API works, but relays never click

Python Version

- Python 3.12+
- Python 3.13 confirmed working
- Matches Raspberry Pi OS Trixie

GPIO Backend (Final Choice)

- GPIO backend: lgpio
- Installed via:
```sudo apt install python3-rpi-lgpio```
- RPi.GPIO is not used
- wiringPi is not required

Behaviour Notes

- GPIO pins are claimed exclusively
- If you see:
``` lgpio.error: 'GPIO busy' ```
→ This means the control service already owns the pin (normal and correct)

## systemd Services

### control.service (Safety Monitor Control)

Key properties:

- Runs as user robert
- Uses venv Python
- Has explicit WorkingDirectory
- Owns GPIO

Example (essential parts):

``` ini
[Service]
Type=simple
User=robert
WorkingDirectory=/home/robert/WeatherMonitor/safety-monitor
ExecStart=/home/robert/WeatherMonitor/venv/bin/python \
          /home/robert/WeatherMonitor/safety-monitor/control.py
Restart=always
RestartSec=5
```

Never use `/usr/bin/python3` for `control.py`.

### app.service (Safety Monitor UI)

- Runs in the same venv
- No GPIO access
- Safe to restart independently

### Time Handling

- `datetime.utcnow()` is not used
- All timestamps are timezone-aware UTC:

``` python
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)
```

This avoids Python 3.13 deprecation warnings.

## Known-Good Runtime Checks

### Verify control API is running

``` bash
ss -ltnp | grep 5001
```

### Check control status

``` bash
curl http://127.0.0.1:5001/status
```

### Manual actuator test

``` bash
curl -X POST http://127.0.0.1:5001/actuators \
  -H "Content-Type: application/json" \
  -d '{"fan":"on"}'
```

Expected:

- State switches to MANUAL
- Relays click
- Fan responds physically

### Common Failure Modes (Already Solved)

| Symptom                              | Root Cause                         | Fix                                               |
|--------------------------------------|------------------------------------|---------------------------------------------------|
| Fan does not run                     | venv missing system packages       | Recreate venv with `--system-site-packages`          |
| API works but hardware doesn’t       | GPIO in mock mode                  | Ensure `lgpio` visible in venv                       |
| `ModuleNotFoundError: meteocalc`       | system Python used                 | Fix `ExecStart`                                     |
| `GPIO busy`                            | Pin already claimed                | Normal behaviour                                  |


## Current Status (Baseline)
- AllSky camera running
- Safety Monitor active
- GPIO functional
- Relays clicking
- Fan and heater responding
- Services stable
