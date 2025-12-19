# Skymonitor Safety Monitor - HTTP-only Architecture Refactor

**Date:** 2025-12-19  
**Version:** 2.0 (HTTP-only)  
**Target Platform:** Raspberry Pi (sealed enclosure)

---

## Executive Summary

The Skymonitor Safety Monitor has been refactored from a serial-based, database-heavy architecture to an HTTP-only, low-load design optimized for sealed Raspberry Pi enclosures.

### Key Changes

- ✅ **HTTP polling** replaces serial port data collection
- ✅ **Primary + fallback** endpoint architecture for reliability
- ✅ **No historical data** storage (SQLite removed)
- ✅ **Minimal disk I/O** (atomic writes to state.json only)
- ✅ **Two services only**: control.service (critical) + app.service (optional)
- ✅ **Fail-safe enforced**: Fan ON, Heater OFF by default
- ✅ **Low CPU usage**: 10-second control loop, minimal logging
- ✅ **Flask UI** reads from control API (no direct sensor/DB access)

---

## Architecture Overview

### Runtime Services

#### 1. control.service (CRITICAL)
**Purpose:** Core safety monitoring and relay control

**Responsibilities:**
- HTTP polling with 2-second timeout and retry/backoff
- Primary endpoint with automatic fallback on failure
- Data validation and freshness checks (max age: 300s)
- Safety/control logic implementation
- GPIO/relay control (fail-safe defaults)
- Local HTTP API on localhost:5001

**API Endpoints:**
- `GET /status` - Current snapshot, age, mode, relay states, errors
- `GET /health` - Service health, uptime, active endpoint

**Control Loop:** 10 seconds

**Fail-safe Behavior:**
- Fan = ON if data invalid/stale/unavailable
- Heater = OFF if data invalid/stale/unavailable
- Heater ON only if: data fresh, no rain, dew risk met, min off-time passed

---

#### 2. app.service (OPTIONAL)
**Purpose:** Flask UI for status viewing and settings management

**Responsibilities:**
- Read current state from control.service API
- Display sensor data, relay states, mode, age
- Edit and save settings.json
- Serve web UI on port 5000

**Note:** Can be stopped without affecting safety monitoring

---

### Removed Services

- ❌ **store_data.service** - Historical data storage (deprecated)
- ❌ **system_monitor.service** - Background metrics collection (deprecated)

---

## Data Flow

```
┌─────────────────────────────────────────────┐
│  External HTTP Endpoints                    │
│  - Primary:   MeetJeStad API               │
│  - Fallback:  MeetJeStad API (backup)      │
└────────────────┬────────────────────────────┘
                 │ HTTP GET (2s timeout)
                 │ Retry with backoff
                 ▼
┌─────────────────────────────────────────────┐
│  control.py (control.service)               │
│  ┌─────────────────────────────────────┐   │
│  │ fetch_sensor_data_http()            │   │
│  │ - Parse JSON response               │   │
│  │ - Validate required fields          │   │
│  │ - Check data age                    │   │
│  │ - Return normalized snapshot        │   │
│  └──────────────┬──────────────────────┘   │
│                 │                            │
│  ┌─────────────▼──────────────────────┐   │
│  │ compute_derived_values()            │   │
│  │ - Dew point, heat index             │   │
│  │ - Weather indicators                │   │
│  │ - CPU temperature                   │   │
│  └──────────────┬──────────────────────┘   │
│                 │                            │
│  ┌─────────────▼──────────────────────┐   │
│  │ apply_safety_logic()                │   │
│  │ - Fan: ON if thresholds exceeded    │   │
│  │ - Heater: ON if dew risk + safe     │   │
│  │ - Enforce fail-safe defaults        │   │
│  └──────────────┬──────────────────────┘   │
│                 │                            │
│  ┌─────────────▼──────────────────────┐   │
│  │ set_relays()                        │   │
│  │ - GPIO control (Waveshare board)    │   │
│  │ - Fail-safe: Fan ON, Heater OFF     │   │
│  └──────────────┬──────────────────────┘   │
│                 │                            │
│  ┌─────────────▼──────────────────────┐   │
│  │ Flask API (localhost:5001)          │   │
│  │ - /status: current snapshot         │   │
│  │ - /health: service status           │   │
│  └─────────────────────────────────────┘   │
└────────────────┬────────────────────────────┘
                 │ HTTP GET
                 ▼
┌─────────────────────────────────────────────┐
│  app.py (app.service)                       │
│  - Fetch status from control API            │
│  - Render Flask UI                          │
│  - Edit/save settings.json                  │
│  - Serve on port 5000                       │
└─────────────────────────────────────────────┘
```

---

## File Changes Summary

### Modified Files

| File | Changes | Status |
|------|---------|--------|
| **control.py** | Complete rewrite - HTTP polling, fallback logic, local API | ✅ Active |
| **fetch_data.py** | Added HTTP fetch functions with retry/backoff | ✅ Active (HTTP), ⚠️ Serial deprecated |
| **app.py** | Removed SQLite, now calls control API | ✅ Active |
| **settings.py** | Added HTTP endpoint settings, removed DB defaults | ✅ Active |
| **settings.json** | Added primary/fallback endpoints, control_port, timeouts | ✅ Active |
| **store_data.py** | Deprecated - all functions stubbed | ⚠️ Deprecated |
| **system_monitor.py** | Partial deprecation - only get_cpu_temperature() active | ⚠️ Partial |

### New Files

| File | Purpose |
|------|---------|
| **admin/control.service** | Systemd service for control.py |
| **admin/app.service** | Systemd service for app.py |
| **safety-monitor/README_REFACTOR.md** | This document |

### Updated Files

| File | Changes |
|------|---------|
| **admin/UPDATE_SERVICES.md** | Complete rewrite with new architecture |

---

## Configuration

### settings.json Structure

```json
{
  "raining_threshold": 60,
  "ambient_temp_threshold": 25,
  "dewpoint_threshold": 10,
  "cpu_temp_threshold": 70,
  "sleep_time": 10,
  "control_port": 5001,
  "primary_endpoint": "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1",
  "fallback_endpoint": "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1",
  "primary_failure_threshold": 3,
  "max_data_age_seconds": 300,
  "http_timeout_seconds": 2,
  "retry_backoff_seconds": 2,
  "fallback_retry_interval_seconds": 300,
  "heater_min_off_time_seconds": 600
}
```

### Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `sleep_time` | 10 | Control loop interval (seconds) |
| `control_port` | 5001 | Local API port |
| `primary_endpoint` | MeetJeStad URL | Primary HTTP data source |
| `fallback_endpoint` | MeetJeStad URL | Fallback if primary fails |
| `primary_failure_threshold` | 3 | Failures before switching to fallback |
| `max_data_age_seconds` | 300 | Max age before data considered stale |
| `http_timeout_seconds` | 2 | HTTP request timeout |
| `retry_backoff_seconds` | 2 | Backoff multiplier for retries |
| `fallback_retry_interval_seconds` | 300 | How long on fallback before retrying primary |
| `heater_min_off_time_seconds` | 600 | Minimum heater off time |

---

## Safety Logic

### Fan Control

**State:** Always ON by default

**Turns ON if:**
- CPU temperature > cpu_temp_threshold (default: 70°C)
- Camera temperature > 25°C
- Ambient temperature > ambient_temp_threshold (default: 25°C)
- Temperature within dewpoint_threshold of dew point (default: 10°C)

**Turns OFF if:**
- All conditions are safe AND
- Data is valid and fresh

### Heater Control

**State:** Always OFF by default

**Turns ON only if ALL conditions met:**
- Data is valid and fresh (age < 300s)
- Temperature < (dew_point + dewpoint_threshold)
- No rain (raining = 0 or None)
- Minimum off-time has passed (default: 600s)

**Turns OFF if:**
- Any condition fails OR
- Data is invalid/stale/unavailable

---

## Deployment Guide

### Prerequisites

1. Python 3.9+ with venv
2. Raspberry Pi with GPIO access
3. Waveshare RPi Relay Board
4. Network connectivity

### Installation Steps

1. **Update dependencies:**
   ```bash
   cd /home/robert/github/skymonitor
   source venv/bin/activate
   pip install -r safety-monitor/requirements.txt
   ```

2. **Configure settings:**
   ```bash
   cd safety-monitor
   cp settings_example.json settings.json
   nano settings.json  # Edit endpoints and thresholds
   ```

3. **Test control service:**
   ```bash
   python3 control.py
   # Press Ctrl+C to stop after verifying it runs
   ```

4. **Install systemd services:**
   ```bash
   sudo cp admin/control.service /etc/systemd/system/
   sudo cp admin/app.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable control.service app.service
   sudo systemctl start control.service app.service
   ```

5. **Verify operation:**
   ```bash
   # Check service status
   sudo systemctl status control.service
   sudo systemctl status app.service
   
   # Test control API
   curl http://127.0.0.1:5001/status | jq
   
   # Open Flask UI
   # Navigate to http://allsky.local:5000
   ```

6. **Disable deprecated services:**
   ```bash
   sudo systemctl stop store_data.service system_monitor.service
   sudo systemctl disable store_data.service system_monitor.service
   ```

---

## Testing & Validation

### Unit Tests

```bash
cd safety-monitor/test
python3 -m pytest control_test.py
python3 -m pytest fetch_data_test.py
```

### Integration Tests

1. **Test HTTP polling:**
   ```bash
   curl "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1"
   ```

2. **Test control API:**
   ```bash
   curl http://127.0.0.1:5001/health
   curl http://127.0.0.1:5001/status
   ```

3. **Test Flask UI:**
   - Open browser to http://allsky.local:5000
   - Verify data display
   - Edit settings and save
   - Check control service reloads settings

4. **Test failover:**
   - Temporarily block primary endpoint (firewall rule)
   - Watch logs: `journalctl -u control.service -f`
   - Verify switch to fallback mode
   - Restore primary endpoint
   - Verify return to primary after fallback_retry_interval

5. **Test fail-safe behavior:**
   - Stop control service
   - Verify relays in safe state (fans ON, heater OFF)
   - Check GPIO states with multimeter or LED indicators

---

## Performance Metrics

### Expected Performance on Raspberry Pi 4

| Metric | Target | Measured |
|--------|--------|----------|
| CPU Usage | < 5% | TBD |
| Memory Usage | < 100 MB | TBD |
| Disk I/O | < 1 KB/s | TBD |
| Network I/O | < 1 KB/s | TBD |
| Control Loop Time | < 1 second | TBD |
| API Response Time | < 50 ms | TBD |

### Monitoring Commands

```bash
# CPU usage
top -p $(pgrep -f control.py) -n 1

# Memory usage
ps aux | grep control.py

# Disk I/O
sudo iotop -p $(pgrep -f control.py)

# Network I/O
sudo nethogs

# Service logs
journalctl -u control.service -f
```

---

## Troubleshooting

### Common Issues

#### 1. Control service won't start
**Symptoms:** systemctl status shows failed state

**Solutions:**
- Check Python path: `/home/robert/github/skymonitor/venv/bin/python3`
- Verify settings.json exists and is valid JSON
- Check GPIO permissions: `sudo usermod -a -G gpio robert`
- Review logs: `journalctl -u control.service -n 100`

#### 2. HTTP polling fails
**Symptoms:** Mode stuck in STALE or ERROR

**Solutions:**
- Test endpoint manually: `curl [primary_endpoint]`
- Check DNS resolution: `ping meetjestad.net`
- Verify firewall rules: `sudo iptables -L`
- Increase http_timeout_seconds in settings.json

#### 3. Flask UI shows "ERROR"
**Symptoms:** Dashboard displays error message

**Solutions:**
- Verify control service is running: `systemctl status control.service`
- Test control API: `curl http://127.0.0.1:5001/status`
- Check control_port setting matches service
- Review app service logs: `journalctl -u app.service -n 50`

#### 4. Relays not responding
**Symptoms:** Physical relays don't click

**Solutions:**
- Check GPIO availability: `gpio readall`
- Verify user in gpio group: `groups robert`
- Test GPIO manually: `gpio write 26 0` (fan on)
- Check power supply to relay board

#### 5. High CPU usage
**Symptoms:** CPU usage > 10%

**Solutions:**
- Check sleep_time setting (should be ≥ 10)
- Review for infinite loops in logs
- Verify logging level is WARNING (not DEBUG)
- Check for network timeout issues

---

## Migration from V1 (Serial + Database)

### Prerequisites

1. Backup existing database: `cp sky_data.db sky_data.db.backup`
2. Note current settings from settings.json
3. Stop all V1 services

### Migration Steps

1. **Pull latest code:**
   ```bash
   cd /home/robert/github/skymonitor
   git pull
   ```

2. **Update settings.json:**
   - Add new HTTP settings (see Configuration section)
   - Keep existing thresholds

3. **Stop V1 services:**
   ```bash
   sudo systemctl stop control.service app.service store_data.service system_monitor.service
   ```

4. **Install V2 services:**
   ```bash
   sudo cp admin/control.service /etc/systemd/system/
   sudo cp admin/app.service /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

5. **Disable deprecated services:**
   ```bash
   sudo systemctl disable store_data.service system_monitor.service
   ```

6. **Start V2 services:**
   ```bash
   sudo systemctl start control.service
   sudo systemctl start app.service
   ```

7. **Verify operation:**
   ```bash
   sudo systemctl status control.service app.service
   curl http://127.0.0.1:5001/status
   ```

### Rollback Plan

If V2 fails, rollback to V1:

```bash
# Stop V2 services
sudo systemctl stop control.service app.service

# Restore V1 code
cd /home/robert/github/skymonitor
git checkout [v1-commit-hash]

# Restart V1 services
sudo systemctl start control.service app.service store_data.service system_monitor.service
```

---

## API Documentation

### Control Service API

**Base URL:** `http://127.0.0.1:5001`

#### GET /status

Returns current snapshot and control state.

**Response:**
```json
{
  "snapshot": {
    "valid": true,
    "received_timestamp": "2025-12-19T19:00:00",
    "measurement_timestamp": "2025-12-19T18:59:45",
    "age_seconds": 15,
    "temperature": 18.5,
    "humidity": 65.2,
    "dew_point": 11.8,
    "heat_index": 18.3,
    "cpu_temperature": 45.2,
    "raining": 0,
    "wind": null,
    "sky_temperature": null,
    "ambient_temperature": null,
    "sqm_lux": null,
    "cloud_coverage": null,
    "brightness": null,
    "bortle": null,
    "camera_temp": null,
    "star_count": null,
    "day_or_night": null
  },
  "age_seconds": 15,
  "mode": "NORMAL",
  "fan_status": "OFF",
  "heater_status": "OFF",
  "last_error": null,
  "cycle_count": 1234,
  "uptime_seconds": 12345
}
```

#### GET /health

Returns service health status.

**Response:**
```json
{
  "status": "running",
  "mode": "NORMAL",
  "active_endpoint": "primary",
  "uptime_seconds": 12345
}
```

---

## Future Improvements

### Potential Enhancements

1. **WebSocket support** for real-time UI updates
2. **MQTT integration** for IoT platform compatibility
3. **Prometheus metrics** for advanced monitoring
4. **Multi-sensor support** (multiple temperature/humidity sources)
5. **Advanced forecasting** using historical trends (without full DB)
6. **Alert system** via email/Pushover (currently stubbed)
7. **Emergency GPIO script** for manual relay control
8. **Grafana dashboard** for visualization
9. **Automatic failover** to local sensor if HTTP fails
10. **Configuration UI** without service restart

---

## Credits

**Author:** Robert  
**Project:** Skymonitor Safety Monitor  
**Repository:** github.com/robertrongen/skymonitor  
**License:** [Your License]

---

## Changelog

### Version 2.0 (2025-12-19)

- ✅ HTTP polling with primary/fallback architecture
- ✅ Removed SQLite historical storage
- ✅ Minimal disk I/O (state.json only)
- ✅ Reduced from 3 to 2 services
- ✅ 10-second control loop
- ✅ Fail-safe enforcement in code
- ✅ Flask UI reads from control API
- ✅ Deprecated store_data.py and system_monitor.py
- ✅ WARNING/ERROR logging only

### Version 1.0 (Historical)

- Serial port sensor data collection
- SQLite historical storage
- 3 systemd services
- 60-300 second control loop
- DEBUG logging

---

**End of Document**
