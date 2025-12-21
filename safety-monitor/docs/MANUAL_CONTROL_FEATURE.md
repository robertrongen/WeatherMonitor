# Manual Actuator Control Feature

## Overview
Manual actuator control feature allows operators to override automatic fan/heater control while maintaining critical safety validation. This feature extends the HTTP-only architecture with user-friendly web UI controls.

## Architecture

### Control Flow
```
User (Browser) → Flask UI (app.py) → Control Service API (control.py) → GPIO/Relays
                      ↓
                 Safety Validation
                      ↓
                 State Update
```

## Components

### 1. Control Service API (`control.py`)

#### State Extensions
```python
state = {
    # ... existing fields ...
    "fan_override": None,     # None=AUTO, True=MANUAL ON, False=MANUAL OFF
    "heater_override": None   # None=AUTO, True=MANUAL ON, False=MANUAL OFF
}
```

#### New Endpoint: `POST /actuators`
**Request Body:**
```json
{
  "fan": "on" | "off" | "auto",
  "heater": "on" | "off" | "auto"
}
```

**Response:**
```json
{
  "fan": {
    "mode": "MANUAL",
    "state": "ON",
    "message": "Fan manually set ON"
  },
  "heater": {
    "mode": "AUTO",
    "message": "Heater set to AUTO mode"
  },
  "applied_state": {
    "fan_status": "ON",
    "heater_status": "OFF",
    "fan_mode": "MANUAL",
    "heater_mode": "AUTO"
  }
}
```

#### Extended Endpoint: `GET /status`
Now includes:
- `fan_mode`: "AUTO" | "MANUAL"
- `heater_mode`: "AUTO" | "MANUAL"

#### Safety Validation Logic

**Fan Safety Rules:**
- Manual OFF can be overridden if:
  - CPU temp > threshold + 10°C
  - Ambient temp > threshold + 10°C
- Manual ON is always allowed (fail-safe direction)

**Heater Safety Rules:**
- Manual ON is rejected if:
  - Rain detected (`raining > 0`)
  - Temperature > 30°C
  - Minimum off-time not elapsed
- Manual OFF is always allowed (fail-safe direction)

### 2. Flask UI (`app.py`)

#### New Routes

**`POST /control/fan`**
- Accepts form parameter: `command` (on|off|auto)
- Forwards to control service `/actuators` endpoint
- Returns with flash message

**`POST /control/heater`**
- Accepts form parameter: `command` (on|off|auto)
- Forwards to control service `/actuators` endpoint
- Returns with flash message

**`POST /control/reset`**
- Resets both fan and heater to AUTO mode
- Convenience endpoint for emergency reset

### 3. Web UI (`templates/index.html`)

#### Manual Control Panel
Located below alert controls, provides:

**Fan Controls:**
- Fan ON button (green)
- Fan OFF button (red)
- Fan AUTO button (blue)
- Status display: mode (AUTO/MANUAL) + state (ON/OFF)

**Heater Controls:**
- Heater ON button (green)
- Heater OFF button (red)
- Heater AUTO button (blue)
- Status display: mode (AUTO/MANUAL) + state (ON/OFF)

**Reset Control:**
- RESET ALL TO AUTO button (orange)

**Safety Notice:**
- Warning message about safety validation
- Color-coded status (green=AUTO, orange=MANUAL)

## Usage Examples

### Via API (Control Service)
```bash
# Set fan to manual ON
curl -X POST http://localhost:5001/actuators \
  -H "Content-Type: application/json" \
  -d '{"fan": "on"}'

# Set heater to manual OFF
curl -X POST http://localhost:5001/actuators \
  -H "Content-Type: application/json" \
  -d '{"heater": "off"}'

# Reset both to AUTO
curl -X POST http://localhost:5001/actuators \
  -H "Content-Type: application/json" \
  -d '{"fan": "auto", "heater": "auto"}'

# Check status
curl http://localhost:5001/status
```

### Via Web UI
1. Navigate to `http://localhost:5000/`
2. Scroll to "Manual Actuator Control" section
3. Click desired button (ON/OFF/AUTO)
4. Observe flash message and updated status

## Safety Features

### 1. Fail-Safe Defaults
- Fan: Default ON (cooling always available)
- Heater: Default OFF (prevent overheating/damage)

### 2. Critical Override Protection
Manual commands are validated against critical thresholds:
- Overheating protection (CPU, ambient temp)
- Weather protection (rain detection)
- Thermal cycle protection (heater min off-time)

### 3. Automatic Reversion
- Invalid/stale sensor data: enforces fail-safe defaults
- Critical conditions: overrides manual settings
- Service restart: returns to AUTO mode

### 4. Audit Trail
All manual control actions are logged:
```
WARNING - Fan manually set ON via API
WARNING - Heater manual override rejected: rain detected
```

## Testing

### Prerequisites
- Control service running on port 5001
- Flask UI running on port 5000
- Valid sensor data available

### Run Test Suite
```bash
cd safety-monitor
python test/manual_control_test.py
```

### Test Scenarios
1. ✓ Status endpoint returns mode information
2. ✓ Fan control (ON/OFF/AUTO)
3. ✓ Heater control (ON/OFF/AUTO)
4. ✓ Reset to AUTO
5. ✓ Invalid command rejection
6. ✓ Safety validation enforcement

## Deployment Notes

### Service Configuration
No changes to systemd services required. Both services continue to run as before:
- `control.service` (port 5001)
- `app.service` (port 5000)

### Settings
No new settings required. Existing thresholds apply to manual control validation:
- `cpu_temp_threshold`
- `ambient_temp_threshold`
- `heater_min_off_time_seconds`

### Backwards Compatibility
- Default behavior: AUTO mode (unchanged)
- Existing safety logic: fully preserved
- No impact on automatic operation

## Future Enhancements

### Potential Additions
1. **Timed Overrides**: Manual control with auto-revert after N minutes
2. **Schedule Mode**: Pre-programmed manual sequences
3. **Remote Access**: API authentication for external control
4. **Command History**: Persistent log of manual interventions
5. **Mobile App**: Native mobile interface for control

### Integration Points
- Rain alarm system: could trigger automatic reversion to AUTO
- Weather forecasts: preemptive manual adjustments
- Maintenance mode: disable safety overrides for testing

## Files Modified

### Core Files
- `safety-monitor/control.py`: Added `/actuators` endpoint, manual override state
- `safety-monitor/app.py`: Added `/control/*` routes
- `safety-monitor/templates/index.html`: Added manual control UI

### Test Files
- `safety-monitor/test/manual_control_test.py`: Comprehensive test suite

### Documentation
- `safety-monitor/MANUAL_CONTROL_FEATURE.md`: This file

## Summary
The manual actuator control feature provides safe, validated operator control over fans and heater while maintaining all critical safety protections. The implementation follows the HTTP-only architecture pattern, with clean separation between control logic (control.py) and user interface (app.py).
