# fetch_data.py
import requests
import serial
import json
import time
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
                        try:
                            data = json.loads(line)
                            logger.info(f"Received valid sky data: {data}")
                            return data
                        except json.JSONDecodeError:
                            message = f"Invalid JSON or no JSON: {line}"
                            if should_log(message):
                                logger.debug(message)
                except Exception as e:
                    message = f"Error reading from serial: {e}"
                    if should_log(message):
                        logger.warning(message)
                    time.sleep(1)
            logger.warning("Timeout reached without receiving valid JSON data.")
    except serial.SerialException as e:
        message = f"Serial port exception: {e}"
        if should_log(message):
            logger.error(message)
    return None

def get_rain_wind_data(port, rate, timeout=35, retry_delay=5):
    """
    Reads rain and wind sensor data samples from the serial port.
    Waits until both RainSensor and WindSensor data are available or the timeout expires.
    Retries if the serial port is busy or if data is incomplete.
    """
    end_time = time.time() + timeout
    rain_intensity = None
    wind_intensity = None

    while time.time() < end_time:
        try:
            with serial.Serial(port, rate, timeout=1) as ser:
                while time.time() < end_time:
                    line = ser.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        try:
                            if "RainSensor," in line:
                                try:
                                    _, rain_value = line.split(',')
                                    rain_intensity = float(rain_value)
                                except ValueError:
                                    message = f"Error parsing RainSensor data: {line}"
                                    if should_log(message):
                                        logger.warning(message)
                            elif "WindSensor," in line:
                                try:
                                    _, wind_value = line.split(',')
                                    wind_intensity = float(wind_value)
                                except ValueError:
                                    message = f"Error parsing WindSensor data: {line}"
                                    if should_log(message):
                                        logger.warning(message)

                            # If both values are collected, return them
                            if rain_intensity is not None and wind_intensity is not None:
                                return rain_intensity, wind_intensity

                        except Exception as e:
                            message = f"Error parsing sensor data: {line} - {e}"
                            if should_log(message):
                                logger.error(message)

                    time.sleep(0.1)

        except serial.SerialException as e:
            message = f"Serial exception on port {port}: {e}"
            if should_log(message):
                logger.warning(message)
            time.sleep(retry_delay)  # Wait before retrying

    logger.error("Timeout reached without receiving complete sensor data.")
    return rain_intensity if rain_intensity is not None else 0, wind_intensity if wind_intensity is not None else 0


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

        data = response.json()
        if data:
            temperature = data[0]['temperature']
            humidity = data[0]['humidity']
            return round(temperature, 2), round(humidity, 2)
        else:
            message = "Received empty data from API"
            if should_log(message):
                logger.warning(message)
            return None, None
    except requests.exceptions.RequestException as e:
        message = f"Network-related error when fetching temperature and humidity: {e}"
        if should_log(message):
            logger.warning(message)
        return None, None
    except Exception as e:
        message = f"Failed to fetch temperature and humidity: {e}"
        if should_log(message):
            logger.warning(message)
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
