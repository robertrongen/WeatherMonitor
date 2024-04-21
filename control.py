# control.py
#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time
import schedule
from fetch_data import get_temperature_humidity, get_serial_data, get_cpu_temperature
from weather_indicators import calculate_indicators, calculate_dew_point
from store_data import store_sky_data  # Import your data storage module
from app_logging import setup_logger

logger = setup_logger('control', 'control.log')

# Settings
ambient_temp_threshold = 20
cpu_temp_threshold = 65
interval_time = 5 # minutes
sleep_time = 60 # seconds

serial_port = '/dev/ttyUSB0'
baud_rate = 115200

temp_hum_url = 'https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1'

# Relay GPIO pins on the Raspberry Pi as per Waveshare documentation https://www.waveshare.com/wiki/RPi_Relay_Board
Relay_Ch1 = 26  # Fan
Relay_Ch2 = 20  # Dew Heater
# Relay_Ch3 = 21  # Available for future use

# Set GPIO warnings to false (optional, to avoid nuisance warnings)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Setup Relay GPIOs as outputs
GPIO.setup(Relay_Ch1, GPIO.OUT)
GPIO.setup(Relay_Ch2, GPIO.OUT)

# Function to control fan and heater based on temperature and humidity
def control_fan_heater():
    temperature, humidity = get_temperature_humidity(temp_hum_url)
    serial_data = get_serial_data(serial_port, baud_rate)
    cpu_temperature = get_cpu_temperature()

    if temperature and humidity and serial_data:
        # Extract required fields from serial_data or other sources
        ambient_temperature = temperature  # Assuming ambient temperature comes from get_temperature_humidity
        sky_temperature = serial_data.get('sky_temperature')
        sqm_lux = serial_data.get('sqm_lux')
        cloud_coverage, cloud_coverage_indicator, brightness, bortle = calculate_indicators(ambient_temperature, sky_temperature, sqm_lux)

        dew_point = calculate_dew_point(temperature, humidity)
        dew_point_threshold = temperature - 2
        # Update fan status logic to include CPU temperature check
        fan_status = "ON" if (temperature > ambient_temp_threshold or temperature <= dew_point + 1 or cpu_temperature > cpu_temp_threshold) else "OFF"
        heater_status = "ON" if temperature <= dew_point_threshold else "OFF"
        
        GPIO.output(Relay_Ch1, GPIO.LOW if fan_status == "ON" else GPIO.HIGH)
        GPIO.output(Relay_Ch2, GPIO.LOW if heater_status == "ON" else GPIO.HIGH)

        # Package data for storage, including CPU temperature
        conn = sqlite3.connect('path_to_your_database.db')

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
schedule.every(interval_time).minutes.do(control_fan_heater)

logger.info("Setup complete, running automated tasks.")

if __name__ == '__main__':
    try:
        schedule.run_pending()
        time.sleep(sleep_time)
    finally:
        GPIO.cleanup()
