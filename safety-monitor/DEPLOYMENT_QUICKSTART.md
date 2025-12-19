# Skymonitor Safety Monitor - Deployment Quickstart

**Architecture Version:** 2.0 (HTTP-only)  
**Last Updated:** 2025-12-19

---

## Pre-Deployment Checklist

- [ ] Raspberry Pi with Raspbian/Debian OS
- [ ] Python 3.9+ installed
- [ ] Network connectivity verified
- [ ] GPIO access available (user in `gpio` group)
- [ ] Waveshare RPi Relay Board connected
- [ ] Existing database backed up (if migrating from v1)

---

## Quick Deployment (5 minutes)

### Step 1: Prepare Environment

```bash
cd /home/robert/github/skymonitor
source venv/bin/activate
pip install -r safety-monitor/requirements.txt
```

### Step 2: Configure Settings

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

### Step 3: Test Control Service

```bash
# Run control service manually to verify
python3 control.py
# Should see: "=== Skymonitor Control Service Starting ==="
# Press Ctrl+C after 30 seconds if no errors
```

### Step 4: Install Services

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

### Step 5: Verify Operation

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

### Step 6: Disable Old Services (if migrating)

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
