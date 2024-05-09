import os
import json

def load_settings():
    default_settings = {
        "raining_threshold": 100,
        "ambient_temp_threshold": 20,
        "dewpoint_threshold": 2,
        "cpu_temp_threshold": 65,
        "memory_usage_threshold": 65,
        "interval_time": 300,  # seconds
        "sleep_time": 60,  # seconds
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