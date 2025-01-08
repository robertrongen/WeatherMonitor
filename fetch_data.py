# fetch_data.py
import requests
import serial
import json
import time
from app_logging import setup_logger

# Configure logger
logger = logging.getLogger("fetch_data")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

ser = None

def get_sky_data(port, rate, timeout=35):
    """
    Fetches JSON data from a serial device. Handles decoding errors gracefully.
    """
    start_time = time.time()
    last_error_time = 0  # Track the last time an error was logged
    error_log_interval = 30  # Log decoding errors at most every 30 seconds

    try:
        with serial.Serial(port, rate, timeout=1) as ser:
            while time.time() - start_time < timeout:
                try:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()  # Use 'ignore' to skip invalid bytes
                    if line:
                        try:
                            data = json.loads(line)
                            logger.info(f"Received valid sky data: {data}")
                            return data
                        except json.JSONDecodeError:
                            # Log decoding errors less frequently
                            if time.time() - last_error_time > error_log_interval:
                                logger.debug(f"Invalid JSON or no JSON: {line}")
                                last_error_time = time.time()
                except Exception as e:
                    logger.warning(f"Error reading from serial: {e}")
                    time.sleep(1)  # Small delay before retrying to avoid rapid looping

            logger.warning("Timeout reached without receiving valid JSON data.")
    except serial.SerialException as e:
        logger.error(f"Serial port exception: {e}")
    
    return None

    
    return None

def get_rain_wind_data(port, rate, timeout=120, retry_delay=10):
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
                                    # logger.debug(f"RainSensor data: {rain_intensity}")
                                except ValueError:
                                    logger.warning(f"Error parsing RainSensor data: {line}")
                            elif "WindSensor," in line:
                                try:
                                    _, wind_value = line.split(',')
                                    wind_intensity = float(wind_value)
                                    # logger.debug(f"WindSensor data: {wind_intensity}")
                                except ValueError:
                                    logger.warning(f"Error parsing WindSensor data: {line}")
                            
                            # If both values are collected, return them
                            if rain_intensity is not None and wind_intensity is not None:
                                return rain_intensity, wind_intensity

                        except Exception as e:
                            logger.error(f"Error parsing sensor data: {line} - {e}")

                    time.sleep(0.1)

        except serial.SerialException as e:
            logger.warning(f"Serial exception on port {port}: {e}")
            time.sleep(retry_delay)  # Wait before retrying

    logger.error("Timeout reached without receiving complete sensor data.")
    return rain_intensity if rain_intensity is not None else 0, wind_intensity if wind_intensity is not None else 0

def get_temperature_humidity(url):
    """
    Fetch temperature and humidity from an external API or sensor.
    Returns a tuple (temperature, humidity).
    """
    if not url.startswith('http'):
        logger.error(f"Invalid URL passed to get_temperature_humidity: {url}")
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
                    logger.warning("Max retries reached for temperature/humidity API")

        data = response.json()
        if data:
            temperature = data[0]['temperature']
            humidity = data[0]['humidity']
            return round(temperature, 2), round(humidity, 2)
        else:
            logger.warning("Received empty data from API")
            return None, None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Network-related error when fetching temperature and humidity: {e}")
        return None, None
    except Exception as e:
        logger.warning(f"Failed to fetch temperature and humidity: {e}")
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
                logger.warning("Allsky data is empty.")
            # logger.info(f"Read allsky data: camera_temp = {camera_temp}, star_count = {star_count}, day_or_night = {day_or_night}")
            return camera_temp, star_count, day_or_night
    except FileNotFoundError:
        logger.error(f"Allsky data file not found: {file_path}")
        return None, None, None
    except ValueError as e:
        logger.error(f"Invalid value in allsky data: {e}")
        return None, None, None
    except Exception as e:
        logger.error(f"Failed to read allsky data: {e}")
        return None, None, None