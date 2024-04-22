#fetch_data.py
import requests
import serial
import json
from app_logging import setup_logger
logger = setup_logger('fetch_data', 'fetch_data.log')

ser = None

def get_serial_data(port, rate):
    """
    Fetches data from a serial device, attempting to parse JSON strings.
    Ignores non-JSON messages and continues reading until a valid JSON is found.
    """
    ser = serial.Serial(port, rate, timeout=1)
    try:
        while True:
            line = ser.readline().decode('utf-8').strip()
            if line:
                logger.debug(f"Received line: {line}")
                try:
                    data = json.loads(line)
                    logger.info(f"Received valid JSON data: {data}")
                    return data
                except json.JSONDecodeError:
                    logger.debug("Failed to decode JSON, skipping line.")
    except Exception as e:
        logger.error(f"Error reading from serial port: {e}")
    finally:
        ser.close()
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

if __name__ == "__main__":
    read_serial_data(serial_port)

