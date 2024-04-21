# control.py
#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time
import schedule
import sqlite3
import json
import os
from fetch_data import get_temperature_humidity, get_serial_data, get_cpu_temperature
from weather_indicators import calculate_indicators, calculate_dew_point
from store_data import store_sky_data  # Import your data storage module
from app_logging import setup_logger
logger = setup_logger('control', 'control.log')

def load_settings():
    default_settings = {
        "ambient_temp_threshold": 20,
        "cpu_temp_threshold": 65,
        "interval_time": 300,  # seconds
        "sleep_time": 60,  # seconds
        "temp_hum_url": 'https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1',
        "serial_port": '/dev/ttyUSB0',
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

settings = load_settings()  # Initial load of settings

# Relay GPIO pins on the Raspberry Pi as per Waveshare documentation https://www.waveshare.com/wiki/RPi_Relay_Board
Relay_Ch1 = 26  # Fan
Relay_Ch2 = 20  # Dew Heater
# Relay_Ch3 = 21  # Available for future use

# Set GPIO warnings to false (optional, to avoid nuisance warnings)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Setup Relay GPIOs as outputs
GPIO.setup([Relay_Ch1, Relay_Ch2], GPIO.OUT, initial=GPIO.HIGH)

# Function to control fan and heater based on temperature and humidity
def control_fan_heater():
    global settings
    settings = load_settings()  # Refresh settings on each call
    temperature, humidity = get_temperature_humidity(settings["interval_time"])
    serial_data = get_serial_data(settings["interval_time"], settings["baud_rate"])
    cpu_temperature = get_cpu_temperature()
    if serial_data:
        print("Processing data:", serial_data)
    else:
        print("No valid data received.")

    if temperature and humidity and serial_data:
        # Extract required fields from serial_data or other sources
        ambient_temperature = temperature  # Assuming ambient temperature comes from get_temperature_humidity
        sky_temperature = serial_data.get('sky_temperature')
        sqm_lux = serial_data.get('sqm_lux')
        cloud_coverage, cloud_coverage_indicator, brightness, bortle = calculate_indicators(ambient_temperature, sky_temperature, sqm_lux)

        dew_point = calculate_dew_point(temperature, humidity)
        dew_point_threshold = temperature - 2
        # Update fan status logic to include CPU temperature check
        fan_status = "ON" if (temperature > settings["ambient_temp_threshold"] or temperature <= dew_point + 1 or cpu_temperature > settings["cpu_temp_threshold"]) else "OFF"
        heater_status = "ON" if temperature <= dew_point_threshold else "OFF"
        
        GPIO.output(Relay_Ch1, GPIO.LOW if fan_status == "ON" else GPIO.HIGH)
        GPIO.output(Relay_Ch2, GPIO.LOW if heater_status == "ON" else GPIO.HIGH)

        # Package data for storage, including CPU temperature
        conn = sqlite3.connect('sky_data.db')

        data = {
            "temperature": temperature,
            "humidity": humidity,
            "dew_point": dew_point,
            "fan_status": fan_status,
            "heater_status": heater_status,
            "cpu_temperature": cpu_temperature,
            **serial_data,
            "cloud_coverage": cloud_coverage,
            "cloud_coverage_indicator": cloud_coverage_indicator,
            "brightness": brightness,
            "bortle": bortle
        }

        logger.debug("Storing data: %s", data)
        store_sky_data(data, conn)
        conn.close()

# Schedule to check temperature and humidity every 10 minutes
schedule.every(settings["interval_time"]).seconds.do(control_fan_heater)
logger.info("Setup complete, running automated tasks.")

if __name__ == '__main__':
    try:
        while True:
            schedule.run_pending()
            time.sleep(settings["interval_time"])  # sleep_time could be adjusted to match your timing needs
    except KeyboardInterrupt:
        logger.info("Program stopped by user")
    finally:
        GPIO.cleanup()  # Ensure cleanup is called on exit
        logger.info("GPIO cleanup executed")
