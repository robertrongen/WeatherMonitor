# control.py
#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time
import requests
import schedule
import math
import serial
import json
from app_logging import setup_logger
from store_data import store_sky_data  # Import your data storage module

logger = setup_logger('control', 'control.log')

# Threshold Settings
ambient_temp_threshold = 20
cpu_temp_threshold = 65

# Serial setup
serial_port = '/dev/ttyUSB0'
baud_rate = 115200
ser = serial.Serial(serial_port, baud_rate, timeout=1)

# Relay GPIO pins on the Raspberry Pi as per Waveshare documentation https://www.waveshare.com/wiki/RPi_Relay_Board
Relay_Ch1 = 26  # Fan
Relay_Ch2 = 20  # Dew Heater
# Relay_Ch3 = 21  # Available for future use

# Set GPIO warnings to false (optional, to avoid nuisance warnings)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Setup Relay GPIOs as outputs
GPIO.setup(Relay_Ch1, GPIO.OUT)
GPIO.setup(Relay_Ch2, GPIO.OUT)

def calculate_dew_point(T, RH):
    b = 17.62
    c = 243.12
    gamma = (b * T / (c + T)) + math.log(RH / 100.0)
    dew_point = (c * gamma) / (b - gamma)
    return dew_point

def get_cpu_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = float(f.read()) / 1000.0  # Convert millidegree Celsius to degree Celsius
        return temp
    except:
        return None

def fetch_serial_data():
    try:
        line = ser.readline().decode('utf-8').strip()
        if line:
            return json.loads(line)
    except Exception as e:
        logger.warning(f"Failed to read serial data: {e}")
        return {}

def fetch_temp_humidity():
    url = 'https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1'
    try:
        response = requests.get(url)
        data = response.json()
        logger.info("Fetched data:", data)  # Debugging statement
        temperature = data[0]['data']['temperature']
        humidity = data[0]['data']['humidity']
        return temperature, humidity
    except:
        logger.warning("Failed to fetch data")
        return None, None  # Return None if there's an error

# Function to control fan and heater based on temperature and humidity
def control_fan_heater():
    temperature, humidity = fetch_temp_humidity()
    serial_data = fetch_serial_data()
    cpu_temperature = get_cpu_temperature()  # Get the CPU temperature

    if temperature is not None and humidity is not None and serial_data:
        dew_point = calculate_dew_point(temperature, humidity)
        dew_point_threshold = temperature - 2
        # Update fan status logic to include CPU temperature check
        fan_status = "ON" if (temperature > temp_fan_threshold or temperature <= dew_point + 1 or cpu_temperature > cpu_temp_threshold) else "OFF"
        heater_status = "ON" if temperature <= dew_point_threshold else "OFF"
        
        GPIO.output(Relay_Ch1, GPIO.LOW if fan_status == "ON" else GPIO.HIGH)
        GPIO.output(Relay_Ch2, GPIO.LOW if heater_status == "ON" else GPIO.HIGH)

        # Package data for storage, including CPU temperature
        data = {
            "temperature": temperature,
            "humidity": humidity,
            "dew_point": dew_point,
            "fan_status": fan_status,
            "heater_status": heater_status,
            "cpu_temperature": cpu_temperature,
            **serial_data
        }

        logger.info("Data to be stored:", data)  # Debugging statement
        store_sky_data(data)

# Schedule to check temperature and humidity every 10 minutes
schedule.every(10).minutes.do(control_fan_heater)

logger.info("Setup complete, running automated tasks.")

if __name__ == '__main__':
    try:
        schedule.run_pending()
        time.sleep(1)
    finally:
        GPIO.cleanup()
