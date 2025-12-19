# fetch_data.py
# HTTP-only sensor data fetching
# ALL serial port functionality has been REMOVED

import requests
import json
import time
import logging
from datetime import datetime
from app_logging import setup_logger, should_log

logger = setup_logger('fetch_data', 'fetch_data.log', level=logging.WARNING)

# === HTTP Polling Functions ===

def fetch_sensor_data_http(endpoint_url, settings, max_retries=3):
    """
    Fetch sensor data via HTTP with retry and backoff.
    Returns a normalized snapshot dict with validity flag.
    """
    timeout = settings.get("http_timeout_seconds", 2)
    backoff = settings.get("retry_backoff_seconds", 2)
    max_age = settings.get("max_data_age_seconds", 300)
    
    snapshot = {
        "valid": False,
        "errors": [],
        "received_timestamp": datetime.utcnow().isoformat(),
        "measurement_timestamp": None,
        "age_seconds": None,
        "temperature": None,
        "humidity": None,
        "dew_point": None,
        "heat_index": None,
        "raining": None,
        "wind": None,
        "sky_temperature": None,
        "ambient_temperature": None,
        "sqm_ir": None,
        "sqm_full": None,
        "sqm_visible": None,
        "sqm_lux": None,
        "camera_temp": None,
        "star_count": None,
        "day_or_night": None
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(endpoint_url, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            if not data or not isinstance(data, list) or len(data) == 0:
                snapshot["errors"].append("Empty or invalid JSON response")
                if attempt < max_retries - 1:
                    time.sleep(backoff * (attempt + 1))
                continue
            
            # Parse MeetJeStad-style JSON
            record = data[0]
            
            # Extract and validate required fields
            temp = record.get("temperature")
            humidity = record.get("humidity")
            timestamp_str = record.get("timestamp")
            
            if temp is None or humidity is None:
                snapshot["errors"].append("Missing required fields (temperature or humidity)")
                if attempt < max_retries - 1:
                    time.sleep(backoff * (attempt + 1))
                continue
            
            # Parse timestamp and check age
            if timestamp_str:
                try:
                    measurement_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    snapshot["measurement_timestamp"] = measurement_dt.isoformat()
                    age = (datetime.utcnow() - measurement_dt.replace(tzinfo=None)).total_seconds()
                    snapshot["age_seconds"] = age
                    
                    if age > max_age:
                        snapshot["errors"].append(f"Data too old: {age:.0f}s > {max_age}s")
                        if attempt < max_retries - 1:
                            time.sleep(backoff * (attempt + 1))
                        continue
                except Exception as e:
                    snapshot["errors"].append(f"Timestamp parse error: {e}")
            
            # Data is valid - populate snapshot
            snapshot["temperature"] = round(float(temp), 1) if temp is not None else None
            snapshot["humidity"] = round(float(humidity), 1) if humidity is not None else None
            snapshot["valid"] = True
            
            # Optional fields
            if "rain" in record or "rain_intensity" in record:
                snapshot["raining"] = record.get("rain") or record.get("rain_intensity")
            if "wind_speed" in record:
                snapshot["wind"] = record.get("wind_speed")
            
            logger.warning(f"HTTP fetch successful: temp={snapshot['temperature']}, humid={snapshot['humidity']}, age={snapshot.get('age_seconds', 'N/A')}s")
            return snapshot
            
        except requests.exceptions.Timeout:
            snapshot["errors"].append(f"Timeout on attempt {attempt + 1}")
            logger.warning(f"HTTP request timeout (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.RequestException as e:
            snapshot["errors"].append(f"Request error: {e}")
            logger.warning(f"HTTP request failed (attempt {attempt + 1}/{max_retries}): {e}")
        except Exception as e:
            snapshot["errors"].append(f"Unexpected error: {e}")
            logger.error(f"Unexpected error in HTTP fetch: {e}")
        
        # Backoff before retry
        if attempt < max_retries - 1:
            time.sleep(backoff * (attempt + 1))
    
    # All retries failed
    snapshot["valid"] = False
    logger.error(f"HTTP fetch failed after {max_retries} attempts: {snapshot['errors']}")
    return snapshot

def validate_snapshot(snapshot, settings):
    """
    Validate snapshot freshness and completeness.
    Returns True if snapshot is valid and fresh.
    """
    if not snapshot or not snapshot.get("valid"):
        return False
    
    # Check age
    age = snapshot.get("age_seconds")
    max_age = settings.get("max_data_age_seconds", 300)
    if age is not None and age > max_age:
        logger.warning(f"Snapshot too old: {age}s > {max_age}s")
        return False
    
    # Check required fields
    if snapshot.get("temperature") is None or snapshot.get("humidity") is None:
        logger.warning("Snapshot missing required fields")
        return False
    
    return True

def get_allsky_data(file_path='/home/robert/allsky/tmp/allskydata.json'):
    """
    Reads allsky camera data from JSON file.
    This is NOT serial data - it's a file read from AllSky software.
    """
    try:
        with open(file_path, 'r') as file:
            camera_temp, star_count, day_or_night = None, None, None
            data = json.load(file)
            if data is not None:
                if 'AS_TEMPERATURE_C' in data and data['AS_TEMPERATURE_C'] is not None: 
                    camera_temp = int(data['AS_TEMPERATURE_C'])
                if 'DAY_OR_NIGHT' in data and data['DAY_OR_NIGHT'] is not None:
                    day_or_night = data['DAY_OR_NIGHT']
                if day_or_night == 'NIGHT' and 'AS_STARCOUNT' in data and data['AS_STARCOUNT'] is not None:      
                    star_count = int(data['AS_STARCOUNT'])
                else:
                    star_count = 0
            else:
                message = "Allsky data is empty."
                if should_log(message):
                    logger.warning(message)
            return camera_temp, star_count, day_or_night
    except FileNotFoundError:
        message = f"Allsky data file not found: {file_path}"
        if should_log(message):
            logger.error(message)
        return None, None, None
    except ValueError as e:
        message = f"Invalid value in allsky data: {e}"
        if should_log(message):
            logger.error(message)
        return None, None, None
    except Exception as e:
        message = f"Failed to read allsky data: {e}"
        if should_log(message):
            logger.error(message)
        return None, None, None
