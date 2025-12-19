#!/usr/bin/env python3
# control.py - Standalone Safety Monitor Control Service
# Handles HTTP polling, validation, safety logic, relay control, and local API

import time
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from settings import load_settings
from fetch_data import fetch_sensor_data_http, validate_snapshot
from weather_indicators import calculate_indicators, calculate_dewPoint
from meteocalc import heat_index, Temp

# Minimal logging - WARN and ERROR only
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('control')

# GPIO setup
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    logger.warning("GPIO library not available, running in mock mode")
    GPIO_AVAILABLE = False

# Relay GPIO pins (Waveshare RPi Relay Board)
RELAY_FAN_IN = 26
RELAY_HEATER = 20
RELAY_FAN_OUT = 21

def setup_gpio():
    """Initialize GPIO pins for relay control"""
    if GPIO_AVAILABLE:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        # Initialize all relays to safe defaults: fans ON (LOW), heater OFF (HIGH)
        GPIO.setup([RELAY_FAN_IN, RELAY_HEATER, RELAY_FAN_OUT], GPIO.OUT, initial=GPIO.HIGH)
        GPIO.output(RELAY_FAN_IN, GPIO.LOW)   # Fan ON
        GPIO.output(RELAY_FAN_OUT, GPIO.LOW)  # Fan ON
        GPIO.output(RELAY_HEATER, GPIO.HIGH)  # Heater OFF
        logger.warning("GPIO initialized - safe defaults applied (fans ON, heater OFF)")

def set_relays(fan_on, heater_on):
    """Set relay states - fail-safe defaults if GPIO unavailable"""
    if GPIO_AVAILABLE:
        try:
            # Relays are active LOW
            GPIO.output(RELAY_FAN_IN, GPIO.LOW if fan_on else GPIO.HIGH)
            GPIO.output(RELAY_FAN_OUT, GPIO.LOW if fan_on else GPIO.HIGH)
            GPIO.output(RELAY_HEATER, GPIO.LOW if heater_on else GPIO.HIGH)
        except Exception as e:
            logger.error(f"GPIO operation failed: {e}")

# Global state for control service
state = {
    "snapshot": None,
    "mode": "INITIALIZING",  # NORMAL | FALLBACK | STALE | ERROR
    "last_heater_off_time": None,
    "fan_status": "ON",
    "heater_status": "OFF",
    "primary_failure_count": 0,
    "last_primary_attempt": None,
    "last_error": None,
    "control_start_time": datetime.utcnow(),
    "cycle_count": 0,
    "fan_override": None,  # None = AUTO, True = MANUAL ON, False = MANUAL OFF
    "heater_override": None  # None = AUTO, True = MANUAL ON, False = MANUAL OFF
}

def get_cpu_temperature():
    """Fetch CPU temperature from system"""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = f.read()
        return round(float(temp) / 1000, 2)
    except Exception as e:
        logger.warning(f"Failed to fetch CPU temperature: {e}")
        return None

def compute_derived_values(snapshot, settings):
    """Compute dew point, heat index, and weather indicators"""
    try:
        temp = snapshot.get("temperature")
        humidity = snapshot.get("humidity")
        
        # Dew point and heat index
        if temp is not None and humidity is not None and 0 <= humidity <= 100:
            try:
                snapshot["dew_point"] = round(calculate_dewPoint(temp, humidity), 2)
                temp_obj = Temp(temp, 'c')
                snapshot["heat_index"] = round(heat_index(temp_obj, humidity).c, 1)
            except Exception as e:
                logger.warning(f"Failed to compute dew point or heat index: {e}")
        
        # Weather indicators (cloud coverage, brightness, bortle)
        ambient_temp = snapshot.get("ambient_temperature")
        sky_temp = snapshot.get("sky_temperature")
        sqm_lux = snapshot.get("sqm_lux")
        
        if ambient_temp is not None and sky_temp is not None and sqm_lux is not None:
            try:
                cloud_coverage, cloud_indicator, brightness, bortle = calculate_indicators(
                    ambient_temp, sky_temp, sqm_lux
                )
                if cloud_coverage is not None:
                    snapshot["cloud_coverage"] = round(cloud_coverage, 2)
                if cloud_indicator is not None:
                    snapshot["cloud_coverage_indicator"] = round(cloud_indicator, 2)
                if brightness is not None:
                    snapshot["brightness"] = round(brightness, 2)
                if bortle is not None:
                    snapshot["bortle"] = round(bortle, 2)
            except Exception as e:
                logger.warning(f"Failed to compute weather indicators: {e}")
        
        # CPU temperature
        cpu_temp = get_cpu_temperature()
        if cpu_temp is not None:
            snapshot["cpu_temperature"] = cpu_temp
            
    except Exception as e:
        logger.error(f"Error in compute_derived_values: {e}")

def apply_safety_logic(snapshot, settings):
    """
    Apply safety control logic to determine fan and heater states.
    CRITICAL: Fail-safe defaults are Fan ON, Heater OFF
    Manual overrides are respected but validated for safety.
    """
    fan_on = True  # Default: always ON
    heater_on = False  # Default: always OFF
    
    # If snapshot is invalid or stale, enforce safe defaults
    if not snapshot or not snapshot.get("valid", False):
        logger.warning("Invalid or stale snapshot - enforcing safe defaults (fan ON, heater OFF)")
        state["mode"] = "STALE"
        state["fan_status"] = "ON"
        state["heater_status"] = "OFF"
        return fan_on, heater_on
    
    # Extract values
    temp = snapshot.get("temperature")
    dew_point = snapshot.get("dew_point")
    cpu_temp = snapshot.get("cpu_temperature")
    camera_temp = snapshot.get("camera_temp")
    raining = snapshot.get("raining")
    
    # Fan logic: ON if any threshold exceeded (AUTO mode)
    if state["fan_override"] is None:
        # AUTO mode
        if cpu_temp is not None and cpu_temp > settings["cpu_temp_threshold"]:
            fan_on = True
        if camera_temp is not None and camera_temp > 25:
            fan_on = True
        if temp is not None and temp > settings["ambient_temp_threshold"]:
            fan_on = True
        if temp is not None and dew_point is not None:
            if temp < (dew_point + settings["dewpoint_threshold"]):
                fan_on = True
    else:
        # MANUAL mode - apply override but validate safety
        fan_on = state["fan_override"]
        # Safety override: force fan ON if critical conditions
        if cpu_temp is not None and cpu_temp > settings["cpu_temp_threshold"] + 10:
            fan_on = True
            logger.warning(f"Fan manual override rejected: CPU temp critical ({cpu_temp}°C)")
        if temp is not None and temp > settings["ambient_temp_threshold"] + 10:
            fan_on = True
            logger.warning(f"Fan manual override rejected: ambient temp critical ({temp}°C)")
    
    # Heater logic: only ON if safe conditions met
    heater_on = False
    if state["heater_override"] is None:
        # AUTO mode
        if temp is not None and dew_point is not None:
            dew_risk = temp < (dew_point + settings["dewpoint_threshold"])
            no_rain = (raining is None or raining == 0)
            min_off_time_passed = True
            
            # Check minimum off time
            if state["last_heater_off_time"] is not None:
                elapsed = (datetime.utcnow() - state["last_heater_off_time"]).total_seconds()
                min_off_time_passed = elapsed >= settings["heater_min_off_time_seconds"]
            
            if dew_risk and no_rain and min_off_time_passed:
                heater_on = True
    else:
        # MANUAL mode - apply override with strict safety validation
        heater_on = state["heater_override"]
        # Safety override: force heater OFF if unsafe conditions
        if raining is not None and raining > 0:
            heater_on = False
            logger.warning("Heater manual override rejected: rain detected")
        if temp is not None and temp > 30:
            heater_on = False
            logger.warning(f"Heater manual override rejected: temp too high ({temp}°C)")
        # Check minimum off time even in manual mode
        if heater_on and state["last_heater_off_time"] is not None:
            elapsed = (datetime.utcnow() - state["last_heater_off_time"]).total_seconds()
            if elapsed < settings["heater_min_off_time_seconds"]:
                heater_on = False
                logger.warning(f"Heater manual override rejected: min off time not met ({elapsed}s < {settings['heater_min_off_time_seconds']}s)")
    
    # Record heater state change
    if not heater_on and state["heater_status"] == "ON":
        state["last_heater_off_time"] = datetime.utcnow()
    
    state["fan_status"] = "ON" if fan_on else "OFF"
    state["heater_status"] = "ON" if heater_on else "OFF"
    
    return fan_on, heater_on

def fetch_and_update_snapshot(settings):
    """
    Fetch sensor data via HTTP with primary/fallback logic.
    Returns True if successful, False otherwise.
    """
    use_primary = True
    now = datetime.utcnow()
    
    # Check if we should retry primary after fallback period
    if state["mode"] == "FALLBACK":
        if state["last_primary_attempt"]:
            elapsed = (now - state["last_primary_attempt"]).total_seconds()
            if elapsed >= settings["fallback_retry_interval_seconds"]:
                use_primary = True
                logger.warning("Retrying primary endpoint after fallback interval")
            else:
                use_primary = False
    
    endpoint = settings["primary_endpoint"] if use_primary else settings["fallback_endpoint"]
    
    try:
        # Fetch sensor data via HTTP
        snapshot = fetch_sensor_data_http(endpoint, settings)
        
        if snapshot and snapshot.get("valid"):
            # Success - update state
            compute_derived_values(snapshot, settings)
            state["snapshot"] = snapshot
            
            if use_primary:
                state["mode"] = "NORMAL"
                state["primary_failure_count"] = 0
                logger.warning(f"Primary endpoint successful - mode: NORMAL")
            else:
                state["mode"] = "FALLBACK"
                logger.warning(f"Fallback endpoint successful - mode: FALLBACK")
            
            state["last_error"] = None
            return True
        else:
            # Fetch failed or invalid
            if use_primary:
                state["primary_failure_count"] += 1
                state["last_primary_attempt"] = now
                logger.warning(f"Primary endpoint failed (count: {state['primary_failure_count']})")
                
                if state["primary_failure_count"] >= settings["primary_failure_threshold"]:
                    logger.error("Primary failure threshold exceeded - switching to fallback")
                    state["mode"] = "FALLBACK"
            else:
                logger.error("Fallback endpoint also failed")
            
            state["last_error"] = "Sensor data fetch failed or invalid"
            return False
            
    except Exception as e:
        logger.error(f"Exception fetching sensor data from {endpoint}: {e}")
        state["last_error"] = str(e)
        
        if use_primary:
            state["primary_failure_count"] += 1
            state["last_primary_attempt"] = now
        
        return False

def control_loop_iteration(settings):
    """Single iteration of the control loop"""
    state["cycle_count"] += 1
    
    # Fetch and update snapshot
    fetch_success = fetch_and_update_snapshot(settings)
    
    # Apply safety logic (will enforce fail-safe defaults if needed)
    fan_on, heater_on = apply_safety_logic(state["snapshot"], settings)
    
    # Set physical relays
    set_relays(fan_on, heater_on)
    
    # Log status periodically
    if state["cycle_count"] % 10 == 0:
        logger.warning(f"Control loop #{state['cycle_count']}: mode={state['mode']}, "
                      f"fan={state['fan_status']}, heater={state['heater_status']}")

# Flask API for local status
app = Flask(__name__)
app.logger.setLevel(logging.ERROR)  # Suppress Flask info logs

@app.route('/status', methods=['GET'])
def api_status():
    """Return current snapshot and control state"""
    snapshot = state.get("snapshot") or {}
    age = None
    if snapshot.get("received_timestamp"):
        try:
            received_dt = datetime.fromisoformat(snapshot["received_timestamp"])
            age = (datetime.utcnow() - received_dt).total_seconds()
        except:
            pass
    
    # Determine control mode for each actuator
    fan_mode = "AUTO" if state["fan_override"] is None else "MANUAL"
    heater_mode = "AUTO" if state["heater_override"] is None else "MANUAL"
    
    return jsonify({
        "snapshot": snapshot,
        "age_seconds": age,
        "mode": state["mode"],
        "fan_status": state["fan_status"],
        "heater_status": state["heater_status"],
        "fan_mode": fan_mode,
        "heater_mode": heater_mode,
        "last_error": state["last_error"],
        "cycle_count": state["cycle_count"],
        "uptime_seconds": (datetime.utcnow() - state["control_start_time"]).total_seconds()
    })

@app.route('/actuators', methods=['POST'])
def api_actuators():
    """
    Manual actuator control endpoint with safety validation.
    Accepts: { "fan": "on"|"off"|"auto", "heater": "on"|"off"|"auto" }
    Safety rules enforced even in manual mode.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        fan_command = data.get("fan")
        heater_command = data.get("heater")
        response = {"fan": None, "heater": None}
        
        # Process fan command
        if fan_command is not None:
            fan_command = fan_command.lower()
            if fan_command == "auto":
                state["fan_override"] = None
                response["fan"] = {"mode": "AUTO", "message": "Fan set to AUTO mode"}
                logger.warning("Fan set to AUTO mode via API")
            elif fan_command == "on":
                state["fan_override"] = True
                response["fan"] = {"mode": "MANUAL", "state": "ON", "message": "Fan manually set ON"}
                logger.warning("Fan manually set ON via API")
            elif fan_command == "off":
                state["fan_override"] = False
                response["fan"] = {"mode": "MANUAL", "state": "OFF", "message": "Fan manually set OFF (will be validated for safety)"}
                logger.warning("Fan manually set OFF via API (safety validation applies)")
            else:
                response["fan"] = {"error": f"Invalid fan command: {fan_command}"}
        
        # Process heater command
        if heater_command is not None:
            heater_command = heater_command.lower()
            if heater_command == "auto":
                state["heater_override"] = None
                response["heater"] = {"mode": "AUTO", "message": "Heater set to AUTO mode"}
                logger.warning("Heater set to AUTO mode via API")
            elif heater_command == "on":
                state["heater_override"] = True
                response["heater"] = {"mode": "MANUAL", "state": "ON", "message": "Heater manually set ON (safety rules apply)"}
                logger.warning("Heater manually set ON via API (safety validation applies)")
            elif heater_command == "off":
                state["heater_override"] = False
                response["heater"] = {"mode": "MANUAL", "state": "OFF", "message": "Heater manually set OFF"}
                logger.warning("Heater manually set OFF via API")
            else:
                response["heater"] = {"error": f"Invalid heater command: {heater_command}"}
        
        # Immediately apply safety logic with new overrides
        settings = load_settings()
        fan_on, heater_on = apply_safety_logic(state["snapshot"], settings)
        set_relays(fan_on, heater_on)
        
        response["applied_state"] = {
            "fan_status": state["fan_status"],
            "heater_status": state["heater_status"],
            "fan_mode": "AUTO" if state["fan_override"] is None else "MANUAL",
            "heater_mode": "AUTO" if state["heater_override"] is None else "MANUAL"
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in /actuators endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def api_health():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "mode": state["mode"],
        "active_endpoint": "primary" if state["mode"] == "NORMAL" else "fallback",
        "uptime_seconds": (datetime.utcnow() - state["control_start_time"]).total_seconds()
    })

def save_state_snapshot():
    """Save last known good snapshot to disk (optional persistence)"""
    try:
        if state["snapshot"] and state["snapshot"].get("valid"):
            with open("state.json.tmp", "w") as f:
                json.dump({
                    "snapshot": state["snapshot"],
                    "mode": state["mode"],
                    "timestamp": datetime.utcnow().isoformat()
                }, f, indent=2)
            # Atomic write
            import os
            os.replace("state.json.tmp", "state.json")
    except Exception as e:
        logger.error(f"Failed to save state snapshot: {e}")

def run_control_service():
    """Main entry point for control service"""
    logger.warning("=== Skymonitor Control Service Starting ===")
    
    settings = load_settings()
    setup_gpio()
    
    # Enforce safe defaults at startup
    set_relays(fan_on=True, heater_on=False)
    
    logger.warning(f"Control loop interval: {settings['sleep_time']} seconds")
    logger.warning(f"Primary endpoint: {settings['primary_endpoint']}")
    logger.warning(f"Fallback endpoint: {settings['fallback_endpoint']}")
    
    # Start Flask API in background thread
    from threading import Thread
    api_thread = Thread(target=lambda: app.run(
        host='127.0.0.1',
        port=settings['control_port'],
        debug=False,
        use_reloader=False
    ))
    api_thread.daemon = True
    api_thread.start()
    logger.warning(f"Local API started on http://127.0.0.1:{settings['control_port']}")
    
    # Main control loop
    try:
        while True:
            start_time = time.time()
            
            # Reload settings each iteration
            settings = load_settings()
            
            # Run control logic
            control_loop_iteration(settings)
            
            # Save state periodically (every 10th cycle)
            if state["cycle_count"] % 10 == 0:
                save_state_snapshot()
            
            # Sleep for configured interval
            elapsed = time.time() - start_time
            sleep_time = max(settings["sleep_time"] - elapsed, 0)
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.warning("Control service stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in control loop: {e}")
        raise
    finally:
        if GPIO_AVAILABLE:
            # Enforce safe defaults on shutdown
            GPIO.output(RELAY_FAN_IN, GPIO.LOW)   # Fan ON
            GPIO.output(RELAY_FAN_OUT, GPIO.LOW)  # Fan ON
            GPIO.output(RELAY_HEATER, GPIO.HIGH)  # Heater OFF
            GPIO.cleanup()
        logger.warning("Control service shutdown complete")

if __name__ == '__main__':
    run_control_service()
