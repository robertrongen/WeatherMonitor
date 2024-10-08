# fetch_data.py
import requests
import serial
import json
import time
from app_logging import setup_logger

logger = setup_logger('fetch_data', 'fetch_data.log')
ser = None

def get_sky_data(port, rate, timeout=240):
    """
    Fetches JSON data from a serial device. Waits until a valid JSON is found or the timeout expires.
    """
    end_time = time.time() + timeout
    try:
        with serial.Serial(port, rate, timeout=1) as ser:
            while time.time() < end_time:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    try:
                        data = json.loads(line)
                        # logger.info(f"Received valid sky_data: {line}")
                        return data
                    except json.JSONDecodeError:
                        logger.debug(f"Failed to decode JSON or no JSON: {line}, skipping line.")
                time.sleep(2)
    except serial.serialutil.SerialException:
        logger.info("Serial port for json is busy, waiting...")
        time.sleep(10)  # Wait a bit before trying to access the port again
    logger.error("Timeout reached without receiving valid JSON data.")
    return None

def get_rain_wind_data(port, rate, timeout=120, retry_delay=10):
    """
    Reads rain and wind sensor data samples from the serial port.
    Waits until both RainSensor and WindSensor data are available or the timeout expires.
    Retries if the serial port is busy.
    """
    end_time = time.time() + timeout
    rain_intensity = None
    wind_intensity = None

    while time.time() < end_time:
        try:
            with serial.Serial(port, rate, timeout=1) as ser:
                while time.time() < end_time:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        try:
                            if "RainSensor," in line:
                                _, rain_value = line.split(',')
                                rain_intensity = float(rain_value)
                            elif "WindSensor," in line:
                                _, wind_value = line.split(',')
                                wind_intensity = float(wind_value)
                            if rain_intensity is not None and wind_intensity is not None:
                                # logger.info(f"Received valid sensor data: rain = {rain_intensity}, wind = {wind_intensity}")
                                return rain_intensity, wind_intensity
                        except ValueError:
                            logger.error(f"Failed to parse sensor data: {line}")
        except serial.SerialException:
            logger.info("Serial port is busy, waiting for retry...")
            time.sleep(retry_delay)  # Wait before trying again

    logger.error("Timeout reached without receiving valid sensor data.")
    return rain_intensity, wind_intensity

def get_temperature_humidity(url):
    """
    Fetch temperature and humidity from an external API or sensor.
    Returns a tuple (temperature, humidity).
    """
    if not url.startswith('http'):
        logger.error(f"Invalid URL passed to get_temperature_humidity: {url}")
        return None, None

    try:
        response = requests.get(url)
        response.raise_for_status()  # Will raise an exception for 4XX/5XX responses
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