# Systemd Service Configuration (HTTP-only Architecture)

**Last Updated:** 2025-12-21
**Architecture:** HTTP polling, no database, minimal disk I/O

---

## Critical: GPIO and Virtual Environment Setup

### System Requirements

The [`control.service`](control.service) requires **GPIO access with system-level packages**.

**Virtual environment MUST be created with `--system-site-packages`:**
```bash
python3 -m venv venv --system-site-packages
```

### Why This Is Required

- **lgpio** is installed system-wide via APT (`python3-rpi-lgpio`)
- **Python dependencies** (meteocalc, Flask, requests) are installed in venv via pip
- **Without `--system-site-packages`:** venv cannot see lgpio
- **Result:** [`control.py`](../safety-monitor/control.py) silently falls back to mock mode
- **Symptom:** API works, logs look normal, but relays never click

### Verification

Before installing services, verify GPIO is accessible in the venv:

```bash
source /home/robert/github/skymonitor/venv/bin/activate
python -c "import lgpio; print('lgpio OK')"
```

If this fails, recreate the venv:
```bash
cd /home/robert/github/skymonitor
rm -rf venv
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r safety-monitor/requirements.txt
```

### Service File Requirements

The [`control.service`](control.service) **must use venv Python** (not system Python):

```ini
ExecStart=/home/robert/github/skymonitor/venv/bin/python3 /home/robert/github/skymonitor/safety-monitor/control.py
```

**Why not system Python?**
- System Python lacks venv-installed dependencies (meteocalc, Flask, requests)
- Will fail to start or miss critical calculations

---

## Architecture Overview

The refactored Skymonitor system uses only TWO services:

1. **control.service** - Primary runtime service (CRITICAL)
   - HTTP polling with primary/fallback endpoints
   - Data validation and freshness checks
   - Safety logic and relay control
   - Exposes local API on localhost:5001

2. **app.service** - Optional Flask UI (NON-CRITICAL)
   - Reads state from control.service API
   - Writes settings.json only
   - Can be stopped without affecting safety

### Services REMOVED

The following services are **deprecated and must be disabled**:

- ~~store_data.service~~ - Historical storage removed
- ~~system_monitor.service~~ - Background monitoring removed

---

## Installation Steps

### 1. Remove Old Services

```bash
# Stop and disable deprecated services
sudo systemctl stop store_data.service system_monitor.service
sudo systemctl disable store_data.service system_monitor.service

# Optional: Remove old service files
sudo rm -f /etc/systemd/system/store_data.service
sudo rm -f /etc/systemd/system/system_monitor.service
```

### 2. Install New Service Files

```bash
# Copy new service files
sudo cp /home/robert/github/skymonitor/admin/control.service /etc/systemd/system/
sudo cp /home/robert/github/skymonitor/admin/app.service /etc/systemd/system/

# Set correct permissions
sudo chmod 644 /etc/systemd/system/control.service
sudo chmod 644 /etc/systemd/system/app.service

# Reload systemd
sudo systemctl daemon-reload
```

### 3. Enable and Start Services

```bash
# Enable services to start on boot
sudo systemctl enable control.service
sudo systemctl enable app.service

# Start services
sudo systemctl start control.service
sudo systemctl start app.service

# Check status
sudo systemctl status control.service
sudo systemctl status app.service
```

---

## Service Details

### control.service

**Purpose:** Core safety monitor - handles HTTP polling, validation, control logic, and relay control.

**Key Features:**
- Runs continuously with 10-second loop
- HTTP polling with 2-second timeout
- Primary/fallback endpoint switching
- Fail-safe defaults: Fan ON, Heater OFF
- Exposes local API on http://127.0.0.1:5001

**Endpoints:**
- `GET /status` - Current snapshot, age, mode, relay states
- `GET /health` - Service health and uptime

**Must Run:** YES - Safety-critical service

**Dependencies:** network-online.target

**Service File Location:** `/etc/systemd/system/control.service`

---

### app.service

**Purpose:** Flask UI for viewing status and editing settings.

**Key Features:**
- Reads data from control.service API (no direct sensor access)
- Updates settings.json only
- Serves UI on http://0.0.0.0:5000

**Must Run:** NO - Optional UI, does not affect safety

**Dependencies:** control.service (soft dependency)

**Service File Location:** `/etc/systemd/system/app.service`

---

## Verification

### Check Service Status

```bash
# View running services
sudo systemctl status control.service
sudo systemctl status app.service

# Check logs (last 50 lines)
sudo journalctl -u control.service -n 50 -f
sudo journalctl -u app.service -n 50 -f
```

### Test Control API

```bash
# Check control service health
curl http://127.0.0.1:5001/health

# Get current status
curl http://127.0.0.1:5001/status | jq
```

### Test Flask UI

Open browser to: `http://allsky.local:5000`

---

## Troubleshooting

### Fan Does Not Run / Relays Do Not Click

**This is the most common issue.** If the service runs but hardware doesn't respond:

1. **Check for mock mode:**
   ```bash
   journalctl -u control.service -n 100 | grep -i mock
   ```
   If you see "mock mode", GPIO is not accessible.

2. **Verify lgpio in venv:**
   ```bash
   source /home/robert/github/skymonitor/venv/bin/activate
   python -c "import lgpio; print('lgpio OK')"
   ```

3. **Check venv configuration:**
   ```bash
   cat /home/robert/github/skymonitor/venv/pyvenv.cfg | grep system-site-packages
   # Should show: include-system-site-packages = true
   ```

4. **If false, recreate venv:**
   ```bash
   cd /home/robert/github/skymonitor
   rm -rf venv
   python3 -m venv venv --system-site-packages
   source venv/bin/activate
   pip install -r safety-monitor/requirements.txt
   sudo systemctl restart control.service
   ```

### Control Service Won't Start

1. Check Python path and venv:
   ```bash
   /home/robert/github/skymonitor/venv/bin/python3 --version
   ```

2. Check working directory:
   ```bash
   ls -la /home/robert/github/skymonitor/safety-monitor/
   ```

3. Check settings.json exists:
   ```bash
   cat /home/robert/github/skymonitor/safety-monitor/settings.json
   ```

4. Check GPIO permissions (if on Raspberry Pi):
   ```bash
   groups robert
   # Ensure 'gpio' group membership
   sudo usermod -a -G gpio robert
   # Logout and login again
   ```

### Dependency Issues

If missing modules:
```bash
cd /home/robert/github/skymonitor
source venv/bin/activate
pip install -r safety-monitor/requirements.txt
```

### Network Polling Issues

1. Test primary endpoint manually:
   ```bash
   curl -s "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1"
   ```

2. Check settings.json endpoints:
   ```bash
   cat safety-monitor/settings.json | grep endpoint
   ```

---

## Emergency Recovery

If control service fails and relays are in unsafe state:

1. **Stop service immediately:**
   ```bash
   sudo systemctl stop control.service
   ```

2. **Manually set safe relay states** (fans ON, heater OFF):
   ```bash
   # Run emergency script (if available)
   python3 safety-monitor/emergency_safe_mode.py
   
   # OR manually via GPIO (on Raspberry Pi):
   # GPIO 26, 21 = LOW (fans ON)
   # GPIO 20 = HIGH (heater OFF)
   ```

3. **Check logs for errors:**
   ```bash
   sudo journalctl -u control.service -n 200 | grep ERROR
   ```

4. **Restart after fixing issues:**
   ```bash
   sudo systemctl start control.service
   ```

---

## Performance Monitoring

### CPU Usage

```bash
# Check control service CPU usage
top -p $(pgrep -f "control.py") -n 1
```

### Disk I/O

```bash
# Monitor disk writes (should be minimal)
iotop -p $(pgrep -f "control.py")
```

### Memory Usage

```bash
# Check memory footprint
ps aux | grep control.py
```

---

## Configuration

Settings are stored in: `/home/robert/github/skymonitor/safety-monitor/settings.json`

**To modify settings:**
1. Stop control service: `sudo systemctl stop control.service`
2. Edit settings.json
3. Restart control service: `sudo systemctl start control.service`

**OR** use the Flask UI at `/settings` (changes applied on next control loop iteration).

---

## Key Differences from Old Architecture

| Aspect | Old (v1) | New (v2) |
|--------|----------|----------|
| **Services** | 3 services | 2 services |
| **Data Source** | Serial port | HTTP polling |
| **Storage** | SQLite historical data | In-memory + state.json |
| **Disk Writes** | Continuous | Minimal (10-minute interval) |
| **Control Loop** | 60-300 seconds | 10 seconds |
| **Logging** | DEBUG level | WARN/ERROR only |
| **Flask Dependency** | Direct DB access | API calls to control service |
| **Fail-safe** | GPIO defaults | Explicit enforcement in code |

---

## Validation Checklist

After installation, verify:

- [ ] control.service is running
- [ ] app.service is running (optional)
- [ ] Control API responds on port 5001
- [ ] Flask UI accessible on port 5000
- [ ] Deprecated services are stopped and disabled
- [ ] Logs show HTTP polling activity
- [ ] No frequent disk writes (check iotop)
- [ ] CPU usage < 5% on Raspberry Pi
- [ ] Relays respond to temperature changes
- [ ] Heater enforces dew point threshold
- [ ] Fan defaults to ON during data loss

---

## Support

For issues, check:
1. Service logs: `journalctl -u control.service`
2. Control API: `curl http://127.0.0.1:5001/status`
3. Settings validity: `cat safety-monitor/settings.json | jq`
4. Python environment: `which python3` (should be in venv)

---

**Note:** This architecture is designed for low-power, sealed-enclosure deployment on Raspberry Pi. All changes prioritize safety, reliability, and minimal resource usage.
