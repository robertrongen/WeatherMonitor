#fetch_data.py
import requests
import serial
import json

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
                logging.debug(f"Received line: {line}")
                try:
                    data = json.loads(line)
                    logging.info(f"Received valid JSON data: {data}")
                    return data
                except json.JSONDecodeError:
                    logging.debug("Failed to decode JSON, skipping line.")
    except Exception as e:
        logging.error(f"Error reading from serial port: {e}")
    finally:
        ser.close()
    return None

def get_temperature_humidity(url):
    """
    Fetch temperature and humidity from an external API or sensor.
    Returns a tuple (temperature, humidity).
    """
    try:
        response = requests.get(url)
        data = response.json()
        temperature = data['current']['temp_c']
        humidity = data['current']['humidity']
        return temperature, humidity
    except Exception as e:
        print(f"Failed to fetch temperature and humidity: {e}")
        logger.warning("Failed to fetch data")
        return None, None

def get_cpu_temperature():
    """
    Fetch the CPU temperature of the system, useful for monitoring and control.
    Returns the CPU temperature as a float.
    """
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = f.read()
        return float(temp) / 1000  # Convert millidegree Celsius to degree Celsius
    except Exception as e:
        print(f"Failed to fetch CPU temperature: {e}")
        return None

if __name__ == "__main__":
    read_serial_data(serial_port)

