#fetch_data.py
import requests
import serial
import json
import psutil
from app_logging import setup_logger
logger = setup_logger('fetch_data', 'fetch_data.log')

ser = None

def get_serial_data(port, rate, num_samples=5):
    """
    Fetches data from a serial device, attempting to parse JSON strings.
    Also handles specific non-JSON data like rain sensor readings.
    """
    with serial.Serial(port, rate, timeout=1) as ser:
        rain_readings = []
        json_data = {}
        for _ in range(num_samples):
            line = ser.readline().decode('utf-8').strip()
            if line:
                if "Rainsensor," in line:
                    try:
                        _, value = line.split(',')
                        rain_readings.append(float(value))
                    except ValueError:
                        logger.error("Failed to parse raining data")
                else:
                    try:
                        data = json.loads(line)
                        json_data.update(data)
                        logger.info(f"Received valid JSON data: {data}")
                    except json.JSONDecodeError:
                        logger.debug("Failed to decode JSON, skipping line.")
            time.sleep(1)  # Adjust based on how frequently data is sent
        average_rain = mean(rain_readings) if rain_readings else None
        return json_data, average_rain

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

if __name__ == "__main__":
    read_serial_data(serial_port)

