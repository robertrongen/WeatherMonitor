# Skymonitor Safety Monitor - Deployment Quickstart

**Architecture Version:** 2.0 (HTTP-only)
**Last Updated:** 2025-12-21

---

## Pre-Deployment Checklist

- [ ] Raspberry Pi with Raspbian/Debian OS (Trixie or newer recommended)
- [ ] Python 3.9+ installed (Python 3.12+ recommended)
- [ ] Network connectivity verified
- [ ] GPIO access available (user in `gpio` group)
- [ ] **System GPIO package installed:** `python3-rpi-lgpio` via APT
- [ ] Waveshare RPi Relay Board connected to GPIO pins 26, 20, 21
- [ ] Existing database backed up (if migrating from v1)

---

## Quick Deployment (5 minutes)

### Step 1: Install System GPIO Package

**Required for hardware relay control:**
```bash
sudo apt update
sudo apt install python3-rpi-lgpio
```

Verify installation:
```bash
python3 -c "import lgpio; print('lgpio installed system-wide')"
```

### Step 2: Create Virtual Environment with System Site Packages

**Critical:** The venv MUST include `--system-site-packages` to access lgpio:

```bash
cd /home/robert/github/skymonitor
python3 -m venv venv --system-site-packages
```

**Why this is required:**
- lgpio is installed system-wide and cannot be pip-installed
- Without `--system-site-packages`, GPIO will silently fall back to mock mode
- This is intentional and required, not optional

### Step 3: Install Python Dependencies

```bash
source venv/bin/activate
pip install -r safety-monitor/requirements.txt
```

### Step 4: Verify GPIO Availability Inside Venv

```bash
source venv/bin/activate
python -c "import lgpio; print('lgpio OK')"
```

If this fails, the venv was not created with `--system-site-packages`. Delete it and recreate:
```bash
rm -rf venv
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r safety-monitor/requirements.txt
```

### Step 5: Configure Settings

```bash
cd safety-monitor
nano settings.json
```

**Minimum required settings:**
```json
{
  "primary_endpoint": "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1",
  "fallback_endpoint": "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1",
  "control_port": 5001,
  "sleep_time": 10,
  "dewpoint_threshold": 10,
  "cpu_temp_threshold": 70
}
```

### Step 6: Test Control Service

```bash
# Run control service manually to verify
python3 control.py
# Should see: "=== Skymonitor Control Service Starting ==="
# Press Ctrl+C after 30 seconds if no errors
```

### Step 7: Install Systemd Services

**Important:** The control.service MUST use venv Python with system site packages access.

Verify the service file uses the correct Python path:
```bash
cat ../admin/control.service | grep ExecStart
# Should show: ExecStart=/home/robert/github/skymonitor/venv/bin/python ...
```

Install services:

```bash
# Copy service files
sudo cp ../admin/control.service /etc/systemd/system/
sudo cp ../admin/app.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable control.service app.service

# Start services
sudo systemctl start control.service
sudo systemctl start app.service
```

### Step 8: Verify Operation

```bash
# Check service status
sudo systemctl status control.service
sudo systemctl status app.service

# Test control API
curl http://127.0.0.1:5001/health
curl http://127.0.0.1:5001/status | jq

# Open browser to Flask UI
# http://[raspberry-pi-ip]:5000
```

### Step 9: Disable Old Services (if migrating)

```bash
sudo systemctl stop store_data.service system_monitor.service
sudo systemctl disable store_data.service system_monitor.service
```

---

## Verification Commands

```bash
# Service status
systemctl status control.service app.service

# View logs (live)
journalctl -u control.service -f

# Check relay states (should click when changing)
# Listen for relay clicks when temperature changes

# Check API response
curl -s http://127.0.0.1:5001/status | jq '.mode, .fan_status, .heater_status'

# Check CPU usage (should be < 5%)
top -p $(pgrep -f control.py) -n 1
```

---

## Troubleshooting

### Fan Does Not Run / Relays Do Not Click

**This is the most common deployment issue.** Hardware will silently fail if GPIO is not properly configured.

Follow this checklist systematically:

#### 1. Check for Mock Mode in Control Logs

```bash
journalctl -u control.service -n 100 | grep -i mock
```

If you see "mock mode" or "MockGPIO", the hardware is not being controlled.

#### 2. Verify lgpio Import Inside Venv

```bash
source /home/robert/github/skymonitor/venv/bin/activate
python -c "import lgpio; print('lgpio OK')"
```

**If this fails with `ModuleNotFoundError`:** The venv does not have system site packages access.

#### 3. Verify Venv Was Created with --system-site-packages

```bash
cat /home/robert/github/skymonitor/venv/pyvenv.cfg | grep system-site-packages
# Should show: include-system-site-packages = true
```

**If it shows `false`:** Recreate the venv correctly:
```bash
cd /home/robert/github/skymonitor
rm -rf venv
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r safety-monitor/requirements.txt
sudo systemctl restart control.service
```

#### 4. Verify GPIO Pin Is Not "Busy"

```bash
journalctl -u control.service -n 100 | grep -i "busy\|claimed"
```

**If GPIO pins show as "busy":** Another process (or previous control instance) has claimed them.

**Solution:**
```bash
sudo systemctl stop control.service
# Wait 5 seconds
sudo systemctl start control.service
```

If still busy after restart, reboot the Raspberry Pi.

#### 5. Verify Systemd Service Uses Venv Python

```bash
systemctl cat control.service | grep ExecStart
# Should show: /home/robert/github/skymonitor/venv/bin/python
```

**If using system Python:** The service will fail because it lacks venv-installed dependencies (meteocalc, Flask, requests).

#### Root Cause Summary

- **lgpio** is installed system-wide via APT
- **Python dependencies** are installed in the venv via pip
- **Without `--system-site-packages`:** venv cannot see lgpio
- **Result:** [`control.py`](../control.py) silently falls back to mock mode
- **Symptom:** API works, logs look normal, but relays never click

---

### Control service fails to start

**Check Python path:**
```bash
/home/robert/github/skymonitor/venv/bin/python3 --version
```

**Check settings.json:**
```bash
cat settings.json | jq
```

**Check GPIO permissions:**
```bash
groups robert  # Should include 'gpio'
sudo usermod -a -G gpio robert
# Logout and login again
```

### HTTP polling fails

**Test endpoint manually:**
```bash
curl "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1"
```

**Check DNS:**
```bash
ping -c 3 meetjestad.net
```

### Flask UI shows error

**Verify control service is running:**
```bash
systemctl status control.service
curl http://127.0.0.1:5001/health
```

**Check port binding:**
```bash
netstat -tuln | grep 5001
```

---

## Emergency Safe Mode

If control service fails and relays need manual control:

```bash
# Stop service
sudo systemctl stop control.service

# Fans ON (relays 26, 21 = LOW)
gpio -g mode 26 out
gpio -g mode 21 out
gpio -g write 26 0
gpio -g write 21 0

# Heater OFF (relay 20 = HIGH)
gpio -g mode 20 out
gpio -g write 20 1
```

---

## Post-Deployment Monitoring

### First 24 Hours

```bash
# Watch logs continuously
journalctl -u control.service -f

# Check stats every hour
curl -s http://127.0.0.1:5001/status | jq '{mode, fan_status, heater_status, age_seconds, cycle_count}'

# Monitor CPU usage
watch -n 10 'top -p $(pgrep -f control.py) -n 1 | tail -1'
```

### Expected Behavior

- Mode should be `NORMAL` (not `FALLBACK` or `STALE`)
- Data age should be < 60 seconds
- CPU usage should be < 5%
- Fans should turn ON when temp exceeds threshold
- Heater should turn ON only when dew risk present and no rain
- Control loop should complete in < 1 second

---

## Performance Targets

| Metric | Target | Command |
|--------|--------|---------|
| CPU Usage | < 5% | `top -p $(pgrep -f control.py)` |
| Memory | < 100 MB | `ps aux \| grep control.py` |
| Disk I/O | < 1 KB/s | `sudo iotop -p $(pgrep -f control.py)` |
| Loop Time | < 1 sec | `journalctl -u control.service -n 50` |
| API Response | < 50 ms | `time curl http://127.0.0.1:5001/health` |

---

## Next Steps

1. **Configure alerts** (if using Pushover/email)
2. **Set up monitoring** (Prometheus, Node Exporter)
3. **Create backups** of settings.json
4. **Document thresholds** specific to your location
5. **Test failover** by blocking primary endpoint
6. **Verify fail-safe** by stopping service and checking relays

---

## Support & Documentation

- **Full documentation:** `safety-monitor/README_REFACTOR.md`
- **Service management:** `admin/UPDATE_SERVICES.md`
- **Architecture details:** `docs/architecture/ARCHITECTURE_PLAN_V2.md` (if exists)

---

## Rollback Plan

If deployment fails, restore v1 architecture:

```bash
# Stop v2 services
sudo systemctl stop control.service app.service

# Restore v1 code (if using git)
git checkout [previous-commit-hash]

# Start v1 services
sudo systemctl start control.service app.service store_data.service system_monitor.service
```

---

**Deployment complete! Monitor for 24 hours before considering stable.**
