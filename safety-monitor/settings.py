import os
import json
import logging
from app_logging import setup_logger

logger = setup_logger(
    name="settings",
    log_file="settings.log",
    level=logging.INFO
)

def load_settings():
    default_settings = {
        "raining_threshold": 100,
        "ambient_temp_threshold": 20,
        "dewpoint_threshold": 2,
        "cpu_temp_threshold": 65,
        "memory_usage_threshold": 65,
        "sleep_time": 10,
        "control_port": 5001,
        "primary_endpoint": "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1",
        "fallback_endpoint": "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1",
        "primary_failure_threshold": 3,
        "max_data_age_seconds": 300,
        "http_timeout_seconds": 2,
        "retry_backoff_seconds": 2,
        "fallback_retry_interval_seconds": 300,
        "heater_min_off_time_seconds": 600,
        "temp_hum_url": "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1",
        "serial_port_rain": "/dev/ttyUSB1",
        "serial_port_json": "/dev/ttyUSB0",
        "baud_rate": 115200
    }

    settings_path = 'settings.json'
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            logger.warning(f"Error decoding JSON from settings file: {e}. Using default settings.")
            return default_settings
    else:
        logger.info("Settings file not found. Using default settings.")
        return default_settings