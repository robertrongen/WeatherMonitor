#fetch_data.py
import requests
import serial
import json

ser = none

def get_serial_data(port, rate):
    """
    Fetch data from a serial device. This could be an Arduino or similar device collecting local sensor data.
    Returns a dictionary with sky_temperature and sqm_lux.
    """
    global ser
    try:
        if ser is None:
            ser = serial.Serial(port, rate, timeout=1)
        line = ser.readline().decode('utf-8').strip()
        return json.loads(line) if line else {}
    except Exception as e:
        print(f"Failed to read serial data: {e}")
        logger.warning(f"Failed to read serial data: {e}")
        return {}

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

