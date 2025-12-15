# fetch_data.py
import requests
import serial
import json
import time
import logging
from app_logging import setup_logger, should_log

logger = setup_logger('fetch_data', 'fetch_data.log', level=logging.DEBUG)
ser = None

def get_sky_data(port, rate, timeout=35):
    """
    Fetches JSON data from a serial device. Ensures at least one reading before returning.
    """
    start_time = time.time()
    try:
        with serial.Serial(port, rate, timeout=1) as ser:
            while time.time() - start_time < timeout:
                try:
                    line = ser.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        # Only process lines containing both "{" and "}" and check for "raining"
                        if "{" in line and "}" in line and "raining" in line:
                            try:
                                data = json.loads(line)
                                logger.info(f"Received valid sky data: {data}")
                                return data
                            except json.JSONDecodeError:
                                message = f"Invalid JSON data: {line}"
                                if should_log(message):
                                    logger.debug(message)
                except Exception as e:
                    message = f"Error reading from serial: {e}"
                    if should_log(message):
                        logger.warning(message)
                    time.sleep(1)
            # logger.warning("Timeout reached without receiving valid JSON data.")
    except serial.SerialException as e:
        message = f"Serial port exception: {e}"
        if should_log(message):
            logger.error(message)
    return None

def get_rain_wind_data(port, rate, timeout=35):
    """
    Fetches JSON data from the Arduino Nano's serial output.
    Waits until valid JSON is received or the timeout expires.
    """
    logger.debug(f"Attempting to fetch rain/wind data at {time.time()}")
    start_time = time.time()
    try:
        with serial.Serial(port, rate, timeout=35) as ser:
            while time.time() - start_time < timeout:
                try:
                    line = ser.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        # Check for JSON structure
                        if "{" in line and "}" in line and ("wind_speed" in line or "rain_intensity" in line):
                            try:
                                data = json.loads(line)
                                logger.info(f"Received rain/wind data: {data}")
                                wind_speed = data.get("wind_speed", 0.0)
                                rain_intensity = data.get("rain_intensity", 0.0)
                                return rain_intensity, wind_speed
                            except json.JSONDecodeError:
                                message = f"Invalid JSON data: {line}"
                                if should_log(message):
                                    logger.debug(message)
                except Exception as e:
                    message = f"Error reading from serial: {e}"
                    if should_log(message):
                        logger.warning(message)
                    time.sleep(0.5)
        logger.warning("Timeout reached without receiving valid rain/wind data.")
    except serial.SerialException as e:
        message = f"Serial port exception: {e}"
        if should_log(message):
            logger.error(message)
    return None, None

def get_sky_data(port, rate, timeout=35):
    """
    Fetches JSON data from the ESP8266 (D1 Mini) serial output.
    Waits until valid JSON is received or the timeout expires.
    """
    start_time = time.time()
    try:
        with serial.Serial(port, rate, timeout=35) as ser:
            while time.time() - start_time < timeout:
                try:
                    line = ser.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        # Check for JSON structure
                        if "{" in line and "}" in line and ("sky_temperature" in line or "sqm_ir" in line):
                            try:
                                data = json.loads(line)
                                logger.info(f"Received sky data: {data}")
                                return data
                            except json.JSONDecodeError:
                                message = f"Invalid JSON data: {line}"
                                if should_log(message):
                                    logger.debug(message)
                except Exception as e:
                    message = f"Error reading from serial: {e}"
                    if should_log(message):
                        logger.warning(message)
                    time.sleep(1)
        logger.warning("Timeout reached without receiving valid sky data.")
    except serial.SerialException as e:
        message = f"Serial port exception: {e}"
        if should_log(message):
            logger.error(message)
    return None

def get_temperature_humidity(url):
    """
    Fetch temperature and humidity from an external API or sensor.
    Returns a tuple (temperature, humidity).
    """
    if not url.startswith('http'):
        message = f"Invalid URL passed to get_temperature_humidity: {url}"
        if should_log(message):
            logger.error(message)
        return None, None

    try:
        retries = 3
        response = None
        for i in range(retries):
            try:
                response = requests.get(url)
                response.raise_for_status()  # Will raise an exception for 4XX/5XX responses
                break
            except requests.exceptions.RequestException:
                if i < retries - 1:
                    time.sleep(2 ** i)  # Backoff
                else:
                    message = "Max retries reached for temperature/humidity API"
                    if should_log(message):
                        logger.warning(message)

        if response:
            try:
                data = response.json()
                if data:
                    temperature = data[0].get('temperature')
                    humidity = data[0].get('humidity')
                    return round(temperature, 2), round(humidity, 2)
                else:
                    logger.warning("Received empty data from API")
            except Exception as e:
                logger.warning(f"JSON parse failed: {e}")
        return None, None
    except Exception as e:
        message = f"Failed to fetch temperature/humidity data: {e}"
        if should_log(message):
            logger.error(message)
        return None, None

def get_allsky_data(file_path='/home/robert/allsky/tmp/allskydata.json'):
    """
    Reads the allsky data.
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
