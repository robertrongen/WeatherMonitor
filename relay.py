# relay.py
#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time
import requests
import schedule
import math
from store_data import store_weather_data  # Import your data storage module

# Settings
temp_fan_threshold = 20

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
GPIO.setup(Relay_Ch3, GPIO.OUT)

# Function to calculate dew point
def calculate_dew_point(T, RH):
    b = 17.62
    c = 243.12
    gamma = (b * T / (c + T)) + math.log(RH / 100.0)
    dew_point = (c * gamma) / (b - gamma)
    return dew_point

# Function to fetch temperature and humidity
def fetch_temp_humidity():
    url = 'https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1'
    try:
        response = requests.get(url)
        data = response.json()
        temperature = data[0]['data']['temperature']
        humidity = data[0]['data']['humidity']
        return temperature, humidity
    except:
        print("Failed to fetch data")
        return None, None  # Return None if there's an error

# Function to control fan and heater based on temperature and humidity
def control_fan_heater():
    temperature, humidity = fetch_temp_humidity()
    if temperature is not None and humidity is not None:
        # Define your temperature and humidity thresholds
        dew_point = calculate_dew_point(temperature, humidity)
        dew_point_threshold = temperature - 2  # Heater activation threshold
        fan_status = "OFF"
        heater_status = "OFF"

        # Control the fan (Relay Channel 1)
        if temperature > temp_threshold:
            GPIO.output(Relay_Ch1, GPIO.LOW)  # Turn fan ON
            fan_status = "ON"
        else:
            GPIO.output(Relay_Ch1, GPIO.HIGH)  # Turn fan OFF
            fan_status = "OFF"

        # Activate fan when close to dew point
        if temperature <= dew_point + 1:  # Adjust as needed
            GPIO.output(Relay_Ch1, GPIO.LOW)  # Turn fan ON
            fan_status = "ON"
    else:
            GPIO.output(Relay_Ch1, GPIO.HIGH)  # Turn fan OFF
            fan_status = "OFF"

        # Activate heater when temperature is below or at dew point threshold
        if temperature <= dew_point_threshold:
            GPIO.output(Relay_Ch2, GPIO.LOW)  # Turn heater ON
            heater_status = "ON"
        else:
            GPIO.output(Relay_Ch2, GPIO.HIGH)  # Turn heater OFF
            heater_status = "OFF"

# Schedule to check temperature and humidity every 10 minutes
schedule.every(10).minutes.do(control_fan_heater)

print("Setup complete, running automated tasks.")
# Main loop to run scheduled tasks
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("Program stopped by user")
    GPIO.cleanup()  # Clean up GPIO assignments on exit
