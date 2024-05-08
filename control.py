# control.py
#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time
import schedule
import sqlite3
from settings import load_settings
from fetch_data import get_temperature_humidity, get_serial_json, get_serial_rainsensor, get_cpu_temperature, get_memory_usage
from weather_indicators import calculate_indicators, calculate_dewPoint
from meteocalc import heat_index, Temp#, dew_point
from store_data import store_sky_data
from app_logging import setup_logger
from rain_alarm import check_rain_alert

logger = setup_logger('control', 'control.log')
settings = load_settings()  # Initial load of settings

# Relay GPIO pins on the Raspberry Pi as per Waveshare documentation https://www.waveshare.com/wiki/RPi_Relay_Board
Relay_Ch1 = 26  # Fan
Relay_Ch2 = 20  # Dew Heater
# Relay_Ch3 = 21  # Available for future use
GPIO.setwarnings(False)     # Set GPIO warnings to false (optional, to avoid nuisance warnings)
GPIO.setmode(GPIO.BCM)
GPIO.setup([Relay_Ch1, Relay_Ch2], GPIO.OUT, initial=GPIO.HIGH)

def control_fan_heater():
    # Function to control fan and heater and store data
    global settings
    temp_hum_url = settings["temp_hum_url"]
    settings = load_settings()  # Refresh settings on each call
    if not isinstance(temp_hum_url, str) or 'http' not in temp_hum_url:
        logger.error(f"Invalid URL passed: {temp_hum_url}, using to default url instead")
        temp_hum_url = "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1"
    temperature, humidity = get_temperature_humidity(temp_hum_url)
    serial_data = get_serial_json(settings["serial_port"], settings["baud_rate"])
    raining = get_serial_rainsensor(settings["serial_port"], settings["baud_rate"])
    logger.info("raining: ", raining)
    check_rain_alert(raining);

    cpu_temperature = get_cpu_temperature()
    memory_usage = get_memory_usage()

    if serial_data:
        print("Processing data:", serial_data)
    else:
        print("No valid data received.")

    if temperature and humidity and serial_data:
        # Control fan and heater
        dewPoint = round(calculate_dewPoint(temperature, humidity), 2)
        temp=Temp(temperature, 'c')
        # dewPoint = round(dew_point(temp, humidity).c, 1)
        logger.info("dew_point: ", dewPoint)
        heatIndex = round(heat_index(temp, humidity).c, 1)
        fan_status = "ON" if (
            temperature > settings["ambient_temp_threshold"] 
            or temperature <= dewPoint + settings["dewpoint_threshold"]
            or cpu_temperature > settings["cpu_temp_threshold"]
            or memory_usage > settings["memory_usage_threshold"]
        ) else "OFF"
        heater_status = "ON" if temperature <= (dewPoint + settings["dewpoint_threshold"]) else "OFF"
        GPIO.output(Relay_Ch1, GPIO.LOW if fan_status == "ON" else GPIO.HIGH)
        GPIO.output(Relay_Ch2, GPIO.LOW if heater_status == "ON" else GPIO.HIGH)

        # Get other data, calculate values
        ambient_temperature = round(temperature, 1)
        sky_temperature = round(float(serial_data.get('sky_temperature')), 1) if serial_data.get('sky_temperature') else None
        sqm_lux = round(float(serial_data.get('sqm_lux')), 2) if serial_data.get('sqm_lux') else None
        cloud_coverage, cloud_coverage_indicator, brightness, bortle = calculate_indicators(ambient_temperature, sky_temperature, sqm_lux)
        cloud_coverage = round(cloud_coverage, 2) if cloud_coverage is not None else None
        cloud_coverage_indicator = round(cloud_coverage_indicator, 1) if cloud_coverage_indicator is not None else None
        brightness = round(brightness, 1) if brightness is not None else None
        bortle = round(bortle, 1) if bortle is not None else None
        
        # store data
        conn = sqlite3.connect('sky_data.db')
        data = {
            "temperature": round(temperature,1),
            "humidity": round(humidity, 1),
            "dew_point": dewPoint,
            "heat_index": heatIndex,
            "fan_status": fan_status,
            "heater_status": heater_status,
            "cpu_temperature": round(cpu_temperature, 0),
            **serial_data,
            "raining": raining,
            "cloud_coverage": cloud_coverage,
            "cloud_coverage_indicator": cloud_coverage_indicator,
            "brightness": brightness,
            "bortle": bortle,
            "sky_temperature": sky_temperature,  # Ensure the rounded value is used
            "sqm_lux": sqm_lux  # Ensure the rounded value is used
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
            time.sleep(settings["sleep_time"])
    except KeyboardInterrupt:
        logger.info("Program stopped by user")
    finally:
        GPIO.cleanup()
        logger.info("GPIO cleanup executed")
