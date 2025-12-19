# app.py - Flask UI for Skymonitor Safety Monitor
# Reads live state from control service API, writes settings only

from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, abort
from flask_session import Session
import json
import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv
from settings import load_settings

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SESSION_KEY', 'default-dev-key')
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Minimal logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('app')

def get_control_api_url():
    """Get the control service API base URL"""
    settings = load_settings()
    port = settings.get('control_port', 5001)
    return f"http://127.0.0.1:{port}"

def fetch_control_status():
    """Fetch current status from control service"""
    try:
        url = f"{get_control_api_url()}/status"
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch control status: {e}")
        return {
            "error": str(e),
            "snapshot": {},
            "mode": "ERROR",
            "fan_status": "UNKNOWN",
            "heater_status": "UNKNOWN"
        }

def fetch_control_health():
    """Fetch health status from control service"""
    try:
        url = f"{get_control_api_url()}/health"
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch control health: {e}")
        return {"error": str(e), "status": "unreachable"}

@app.route('/')
def index():
    """Main dashboard page"""
    status = fetch_control_status()
    health = fetch_control_health()
    settings = load_settings()
    
    # Format snapshot data for display
    snapshot = status.get("snapshot", {})
    
    # Calculate age display
    age_seconds = status.get("age_seconds")
    age_display = "N/A"
    if age_seconds is not None:
        if age_seconds < 60:
            age_display = f"{int(age_seconds)}s"
        elif age_seconds < 3600:
            age_display = f"{int(age_seconds / 60)}m"
        else:
            age_display = f"{int(age_seconds / 3600)}h"
    
    # Prepare display data
    display_data = {
        "timestamp": snapshot.get("received_timestamp", "N/A"),
        "age": age_display,
        "mode": status.get("mode", "UNKNOWN"),
        "temperature": snapshot.get("temperature"),
        "humidity": snapshot.get("humidity"),
        "dew_point": snapshot.get("dew_point"),
        "heat_index": snapshot.get("heat_index"),
        "cpu_temperature": snapshot.get("cpu_temperature"),
        "camera_temp": snapshot.get("camera_temp"),
        "fan_status": status.get("fan_status", "UNKNOWN"),
        "heater_status": status.get("heater_status", "UNKNOWN"),
        "raining": snapshot.get("raining"),
        "wind": snapshot.get("wind"),
        "sky_temperature": snapshot.get("sky_temperature"),
        "ambient_temperature": snapshot.get("ambient_temperature"),
        "sqm_lux": snapshot.get("sqm_lux"),
        "cloud_coverage": snapshot.get("cloud_coverage"),
        "brightness": snapshot.get("brightness"),
        "bortle": snapshot.get("bortle"),
        "star_count": snapshot.get("star_count"),
        "day_or_night": snapshot.get("day_or_night"),
        "uptime": health.get("uptime_seconds"),
        "cycle_count": status.get("cycle_count"),
        "last_error": status.get("last_error")
    }
    
    return render_template('index.html', data=display_data)

@app.route('/data')
def data_api():
    """API endpoint to fetch current data"""
    status = fetch_control_status()
    return jsonify(status)

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    """Settings page for editing configuration"""
    settings = load_settings()

    if request.method == 'POST':
        # Update settings based on form data
        try:
            # Integer values
            settings['raining_threshold'] = int(request.form.get('raining_threshold', settings['raining_threshold']))
            settings['ambient_temp_threshold'] = int(request.form.get('ambient_temp_threshold', settings['ambient_temp_threshold']))
            settings['dewpoint_threshold'] = int(request.form.get('dewpoint_threshold', settings['dewpoint_threshold']))
            settings['cpu_temp_threshold'] = int(request.form.get('cpu_temp_threshold', settings['cpu_temp_threshold']))
            settings['sleep_time'] = int(request.form.get('sleep_time', settings['sleep_time']))
            settings['control_port'] = int(request.form.get('control_port', settings['control_port']))
            settings['primary_failure_threshold'] = int(request.form.get('primary_failure_threshold', settings['primary_failure_threshold']))
            settings['max_data_age_seconds'] = int(request.form.get('max_data_age_seconds', settings['max_data_age_seconds']))
            settings['http_timeout_seconds'] = int(request.form.get('http_timeout_seconds', settings['http_timeout_seconds']))
            settings['heater_min_off_time_seconds'] = int(request.form.get('heater_min_off_time_seconds', settings['heater_min_off_time_seconds']))

            # String values
            settings['primary_endpoint'] = request.form.get('primary_endpoint', settings['primary_endpoint'])
            settings['fallback_endpoint'] = request.form.get('fallback_endpoint', settings['fallback_endpoint'])

            # Save updated settings
            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=4)

            flash('Settings have been updated successfully! Control service will reload them on next cycle.', 'success')
            return redirect(url_for('settings_page'))
        except Exception as e:
            flash(f'Error updating settings: {e}', 'error')
            logger.error(f"Settings update error: {e}")
    
    return render_template('settings.html', settings=settings)

@app.route('/dashboard')
def dashboard():
    """Dashboard with metrics"""
    status = fetch_control_status()
    health = fetch_control_health()
    return render_template('dashboard.html', status=status, health=health)

@app.route('/health')
def health():
    """Health check endpoint"""
    health = fetch_control_health()
    if health.get("status") == "running":
        return jsonify(health), 200
    else:
        return jsonify(health), 503

# Legacy alert system (kept for compatibility)
def set_alert_active(state: bool):
    """Set rain alert active state"""
    try:
        with open('alert_status.txt', 'w') as file:
            file.write(str(state))
    except Exception as e:
        logger.error(f"Failed to set alert status: {e}")

def get_alert_active() -> bool:
    """Get rain alert active state"""
    try:
        with open('alert_status.txt', 'r') as file:
            status = file.read().strip().lower() == 'true'
        return status
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.error(f"Failed to read alert status: {e}")
        return False

@app.route('/enable-alert', methods=['POST'])
def enable_alert():
    set_alert_active(True)
    flash('Rain alert enabled', 'success')
    return redirect(url_for('index'))

@app.route('/disable-alert', methods=['POST'])
def disable_alert():
    set_alert_active(False)
    flash('Rain alert disabled', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Ensure alert status file exists
    if not os.path.exists('alert_status.txt'):
        set_alert_active(False)
    
    # Run Flask app
    app.run(debug=False, host='0.0.0.0', port=5000)
