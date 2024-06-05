#fetch_data.py
import requests
import serial
import json
import psutil
import time
from statistics import mean
from app_logging import setup_logger
logger = setup_logger('fetch_data', 'fetch_data.log')

ser = None

def get_sky_data(port, rate, timeout=120):
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
                        # print(f"Received valid JSON data: {line}")
                        logger.info(f"Received valid JSON data: {line}")
                        return data
                    except json.JSONDecodeError:
                        logger.debug(f"Failed to decode JSON or no JSON: {line}, skipping line.")
                time.sleep(2)
    except serial.serialutil.SerialException:
        # print("Serial port for json is busy, waiting...")
        logger.info("Serial port for json is busy, waiting...")
        time.sleep(10)  # Wait a bit before trying to access the port again
    # print("Timeout reached without receiving valid JSON data.")
    logger.error("Timeout reached without receiving valid JSON data.")
    return None

def get_rain_wind_data(port, rate, num_samples=10, timeout=120, retry_delay=10):
    """
    Reads multiple rain and wind sensor data samples from the serial port and returns the averages.
    Waits until enough samples are collected or the timeout expires.
    Retries if the serial port is busy.
    """
    end_time = time.time() + timeout
    rain_readings = []
    wind_readings = []

    while time.time() < end_time:
        try:
            with serial.Serial(port, rate, timeout=1) as ser:
                while time.time() < end_time and (len(rain_readings) < num_samples or len(wind_readings) < num_samples):
                    line = ser.readline().decode('utf-8').strip()
                    if "Rainsensor," in line:
                        try:
                            _, value = line.split(',')
                            rain_readings.append(float(value))
                            if len(rain_readings) == num_samples:
                                average_rain = mean(rain_readings)
                                logger.info(f"Average rain intensity: {average_rain}")
                        except ValueError:
                            logger.error("Failed to parse rain data")
                    elif "WindSensor," in line:
                        try:
                            _, value = line.split(',')
                            wind_readings.append(float(value))
                            if len(wind_readings) == num_samples:
                                average_wind = mean(wind_readings)
                                logger.info(f"Average wind intensity: {average_wind}")
                        except ValueError:
                            logger.error("Failed to parse wind data")
                    time.sleep(2)
                if len(rain_readings) >= num_samples and len(wind_readings) >= num_samples:
                    return average_rain, average_wind
        except serial.SerialException:
            logger.info("Serial port is busy, waiting for retry...")
            time.sleep(retry_delay)  # Wait before trying again
            continue  # Retry after waiting

    logger.error("Timeout reached or insufficient data for average calculation.")
    return None, None

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

def get_cpu_temperature():
    """
    Fetch the CPU temperature of the system, useful for monitoring and control.
    Returns the CPU temperature as a float.
    """
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = f.read()
        return round(float(temp) / 1000, 2)  # Convert millidegree Celsius to degree Celsius
    except Exception as e:
        logger.warning(f"Failed to fetch CPU temperature: {e}")
        return None

def get_cpu_usage():
    """
    Fetch the current CPU usage of the system.
    Returns the CPU usage as a percentage.
    """
    try:
        return psutil.cpu_percent(interval=1)
    except Exception as e:
        logger.warning(f"Failed to fetch CPU usage: {e}")
        return None

def get_memory_usage():
    """
    Fetch the current memory usage of the system.
    Returns memory usage as a percentage of total available memory.
    """
    try:
        memory = psutil.virtual_memory()
        return memory.percent
    except Exception as e:
        logger.warning(f"Failed to fetch memory usage: {e}")
        return None

def get_disk_usage():
    """
    Fetch the disk usage for the root directory.
    Returns the disk usage as a percentage of total capacity.
    """
    try:
        partition = psutil.disk_usage('/')
        return partition.percent
    except Exception as e:
        logger.warning(f"Failed to fetch disk usage: {e}")
        return None
