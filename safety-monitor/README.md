# AllSky Safety Monitor - Raspberry Pi Application

This directory contains the Safety Monitor application that runs on the Raspberry Pi 4B.

## Overview

The Safety Monitor integrates data from multiple sources:
- **LoRa sensor node** (allsky-sensors, future): Environmental sensors via TTN/Chirpstack
- **Allsky camera software** (upstream): Camera temperature, star count, day/night status
- **Meet je Stad Node 580** (external API): Temperature and humidity
- **Legacy USB serial sensors** (deprecated): Arduino Nano + ESP8266 (will be removed in Phase 4)

## Services

### app.service
Flask web server providing:
- Dashboard UI at `http://allsky.local:5000`
- REST API endpoints (`/api/sky_data`, `/api/metrics_data`)
- Settings management
- Real-time WebSocket updates

### control.service
Main orchestration loop:
- Fetches sensor data from all sources
- Computes derived values (dew point, cloud coverage, sky quality)
- Controls Waveshare RPi Relay Board (fan/heater via GPIO 26, 20, 21)
- Stores data in SQLite database
- Triggers rain alerts

### system_monitor.service
Collects Raspberry Pi metrics (CPU temp, memory, disk usage)

## Installation

See root [`README.md`](../README.md) for setup instructions.

## File Structure

- [`app.py`](app.py) - Flask web server
- [`control.py`](control.py) - Main control loop
- [`fetch_data.py`](fetch_data.py) - Data acquisition (sensors, APIs)
- [`store_data.py`](store_data.py) - SQLite database operations
- [`settings.py`](settings.py) - Configuration loader
- [`weather_indicators.py`](weather_indicators.py) - Cloud coverage and sky quality calculations
- [`rain_alarm.py`](rain_alarm.py) - Rain alert notifications (Pushover)
- [`system_monitor.py`](system_monitor.py) - System metrics collection
- [`app_logging.py`](app_logging.py) - Logging utilities
- [`requirements.txt`](requirements.txt) - Python dependencies
- [`settings.json`](settings.json) - Active configuration (user-managed)
- [`settings_example.json`](settings_example.json) - Configuration template
- `templates/` - Flask HTML templates
- `static/` - Web UI assets
- `test/` - Test scripts

## Running Locally

```bash
cd safety-monitor
source ../venv/bin/activate  # Activate Python virtual environment
python app.py                 # Start Flask web server
python control.py             # Start control loop (separate terminal)
```

## References

- Architecture: [`../docs/architecture/ARCHITECTURE_PLAN_V2.md`](../docs/architecture/ARCHITECTURE_PLAN_V2.md)
- Wiring: [`../docs/architecture/HARDWARE_WIRING_STRATEGY.md`](../docs/architecture/HARDWARE_WIRING_STRATEGY.md)
