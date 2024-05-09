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

def get_serial_json(port, rate, timeout=120):
    """
    Fetches JSON data from a serial device. Waits until a valid JSON is found or the timeout expires.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            with serial.Serial(port, rate, timeout=1) as ser:
                while time.time() < end_time:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        try:
                            data = json.loads(line)
                            print(f"Received valid JSON data: {data}")
                            logger.info(f"Received valid JSON data: {data}")
                            return data
                        except json.JSONDecodeError:
                            print(f"Failed to decode JSON or no JSON: {data}, skipping line.")
                            logger.debug(f"Failed to decode JSON or no JSON: {data}, skipping line.")
                    time.sleep(1)
        except serial.serialutil.SerialException:
            print("Serial port is busy, waiting...")
            logger.info("Serial port is busy, waiting...")
            time.sleep(10)  # Wait a bit before trying to access the port again
    print("Timeout reached without receiving valid JSON data.")
    logger.error("Timeout reached without receiving valid JSON data.")
    return {}

def get_serial_rainsensor(port, rate, num_samples=20, timeout=120):
    """
    Reads multiple rain sensor data samples from the serial port and returns the average.
    Waits until enough samples are collected or the timeout expires.
    """
    end_time = time.time() + timeout
    readings = []
    while time.time() < end_time and len(readings) < num_samples:
        try:
            with serial.Serial(port, rate, timeout=1) as ser:
                while time.time() < end_time and len(readings) < num_samples:
                    line = ser.readline().decode('utf-8').strip()
                    print(f"line = {line}")
                    if "Rainsensor," in line:
                        try:
                            _, value = line.split(',')
                            readings.append(float(value))
                            if len(readings) == num_samples:
                                average_rain = mean(readings)
                                logger.info(f"Average rain intensity: {average_rain}")
                                return average_rain
                        except ValueError:
                            logger.error("Failed to parse raining data")
                    time.sleep(1)
        except serial.serialutil.SerialException:
            print("Serial port is busy, waiting...")
            logger.info("Serial port is busy, waiting...")
            time.sleep(10)  # Wait before trying again
    print("Timeout reached or insufficient data for average calculation.")
    logger.error("Timeout reached or insufficient data for average calculation.")
    return None

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
        print(f"Failed to fetch CPU temperature: {e}")
        return None

def get_cpu_usage():
    """
    Fetch the current CPU usage of the system.
    Returns the CPU usage as a percentage.
    """
    try:
        return psutil.cpu_percent(interval=1)
    except Exception as e:
        print(f"Failed to fetch CPU usage: {e}")
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
        print(f"Failed to fetch memory usage: {e}")
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
        print(f"Failed to fetch disk usage: {e}")
        return None
