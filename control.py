# control.py
#!/usr/bin/python
# -*- coding:utf-8 -*-
try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    print("GPIO library can only be run on a Raspberry Pi, importing mock GPIO")
    GPIO = None
import time
from settings import load_settings
from fetch_data import get_temperature_humidity, get_serial_json, get_serial_rainsensor, get_cpu_temperature, get_memory_usage
from weather_indicators import calculate_indicators, calculate_dewPoint
from meteocalc import heat_index, Temp#, dew_point
from store_data import store_sky_data, setup_database
from app_logging import setup_logger
from rain_alarm import check_rain_alert
from app import notify_new_data, get_db_connection

logger = setup_logger('control', 'control.log')
settings = load_settings()  # Initial load of settings

if GPIO:
    # Relay GPIO pins on the Raspberry Pi as per Waveshare documentation https://www.waveshare.com/wiki/RPi_Relay_Board
    Relay_Ch1 = 26  # Fan
    Relay_Ch2 = 20  # Dew Heater
    # Relay_Ch3 = 21  # Available for future use
    GPIO.setwarnings(False)     # Set GPIO warnings to false (optional, to avoid nuisance warnings)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup([Relay_Ch1, Relay_Ch2], GPIO.OUT, initial=GPIO.HIGH)

def control_fan_heater():
    # Function to control fan and heater and store data
    print("controlling fan heater")
    global settings
    temp_hum_url = settings["temp_hum_url"]
    settings = load_settings()  # Refresh settings on each call
    data = {}

    if not isinstance(temp_hum_url, str) or 'http' not in temp_hum_url:
        print(f"Invalid URL passed: {temp_hum_url}, using default URL instead")
        logger.error(f"Invalid URL passed: {temp_hum_url}, using default URL instead")
        temp_hum_url = "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1"

    try:
        temperature, humidity = get_temperature_humidity(temp_hum_url)
        if temperature is not None:
            data["temperature"] = round(temperature, 1)
        if humidity is not None:
            data["humidity"] = round(humidity, 1)
    except Exception as e:
        logger.error(f"Failed to fetch temperature and humidity: {e}")

    try:
        raining = get_serial_rainsensor(settings["serial_port_rain"], settings["baud_rate"])
        logger.info(f"average rain: {raining}")
        check_rain_alert(raining)
        if raining is not None:
            data["raining"] = raining
    except Exception as e:
        logger.error(f"Failed to fetch rain sensor data: {e}")

    try:
        serial_data = get_serial_json(settings["serial_port_json"], settings["baud_rate"])
        data.update(serial_data)
    except Exception as e:
        logger.error(f"Failed to fetch serial JSON data: {e}")

    try:
        cpu_temperature = get_cpu_temperature()
        if cpu_temperature is not None:
            data["cpu_temperature"] = round(cpu_temperature, 0)
    except Exception as e:
        logger.error(f"Failed to fetch CPU temperature: {e}")

    try:
        memory_usage = get_memory_usage()
        if memory_usage is not None:
            data["memory_usage"] = memory_usage
    except Exception as e:
        logger.error(f"Failed to fetch memory usage: {e}")

    if "temperature" in data and "humidity" in data:
        try:
            dewPoint = round(calculate_dewPoint(data["temperature"], data["humidity"]), 2)
            temp = Temp(data["temperature"], 'c')
            heatIndex = round(heat_index(temp, data["humidity"]).c, 1)
            data["dew_point"] = dewPoint
            data["heat_index"] = heatIndex
            logger.info(f"dew_point: {dewPoint}")
        except Exception as e:
            logger.error(f"Failed to compute dew point or heat index: {e}")

    fan_status = "OFF"
    heater_status = "OFF"
    
    if "temperature" in data:
        fan_status = "ON" if (
            data["temperature"] > settings["ambient_temp_threshold"]
            or data["temperature"] <= data.get("dew_point", float('inf')) + settings["dewpoint_threshold"]
            or data.get("cpu_temperature", 0) > settings["cpu_temp_threshold"]
            or data.get("memory_usage", 0) > settings["memory_usage_threshold"]
        ) else "OFF"

        heater_status = "ON" if data["temperature"] <= (data.get("dew_point", float('inf')) + settings["dewpoint_threshold"]) else "OFF"

    if GPIO:
        GPIO.output(Relay_Ch1, GPIO.LOW if fan_status == "ON" else GPIO.HIGH)
        GPIO.output(Relay_Ch2, GPIO.LOW if heater_status == "ON" else GPIO.HIGH)

    # Get other data, calculate values
    try:
        if "temperature" in data or "humidity" in data or "dew_point" in data:
            ambient_temperature = data.get("temperature")
            sky_temperature = round(float(data.get('sky_temperature')), 1) if data.get('sky_temperature') else None
            sqm_lux = round(float(data.get('sqm_lux')), 2) if data.get('sqm_lux') else None
            cloud_coverage, cloud_coverage_indicator, brightness, bortle = calculate_indicators(ambient_temperature, sky_temperature, sqm_lux)
            data["cloud_coverage"] = round(cloud_coverage, 2) if cloud_coverage is not None else None
            data["cloud_coverage_indicator"] = round(cloud_coverage_indicator, 1) if cloud_coverage_indicator is not None else None
            data["brightness"] = round(brightness, 1) if brightness is not None else None
            data["bortle"] = round(bortle, 1) if bortle is not None else None
    except Exception as e:
        logger.error(f"Failed to calculate additional indicators: {e}")

    # store data
    logger.info("Storing data: %s", data)
    conn = get_db_connection()
    try:
        store_sky_data(data, conn)
        notify_new_data()
    finally:
        conn.close()

if __name__ == '__main__':
    setup_database()
    try:
        control_fan_heater()
        while True:
            time.sleep(settings["sleep_time"])
            control_fan_heater()
    except KeyboardInterrupt:
        logger.info("Program stopped by user")
    finally:
        if GPIO:
            GPIO.cleanup()
        logger.info("GPIO cleanup executed")
