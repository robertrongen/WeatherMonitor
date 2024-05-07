# rain_alarm.py
import os
import time
import requests
import serial
from statistics import mean
from settings import load_settings
from dotenv import load_dotenv
from app_logging import setup_logger

logger = setup_logger('rain', 'rain.log')
load_dotenv()  # Load environment variables from .env file
settings = load_settings()  # Refresh settings on each call

def send_pushover_notification(user_key, api_token, message):
    """Send a notification via Pushover."""
    url = 'https://api.pushover.net/1/messages.json'
    data = {
        'token': api_token,
        'user': user_key,
        'message': message,
        'priority': 1,  # Set priority to high
        'sound': 'siren'  # Set to a louder notification sound, if preferred
    }
    response = requests.post(url, data=data)
    return response.text

def read_rain_data(serial_port, baud_rate, num_samples=5):
    """Read multiple rain data samples from the serial port and return the average."""
    with serial.Serial(serial_port, baud_rate, timeout=1) as ser:
        readings = []
        for _ in range(num_samples):
            line = ser.readline().decode().strip()
            if "raining," in line:
                try:
                    _, value = line.split(',')
                    readings.append(float(value))
                except ValueError:
                    logger.error("Failed to parse raining data")
            time.sleep(1)  # Adjust as necessary based on how frequently data is sent
    return mean(readings) if readings else None

def check_rain_alert():
    """Check for rain alerts from the serial port and send notifications."""
    global alert_active
    if not alert_active:
        return

    global settings
    settings = load_settings()
    user_key = os.getenv('PUSHOVER_USER_KEY')
    api_token = os.getenv('PUSHOVER_API_TOKEN')
    rain_threshold = settings["raining_threshold"]
    average_rain = read_rain_data(settings["serial_port"], settings["baud_rate"])

    if average_rain is not None:
        logger.info("Average rain intensity: %s", average_rain)
        if average_rain < rain_threshold:
            message = "Alert: It's raining! Rain intensity: {}".format(average_rain)
            send_pushover_notification(user_key, api_token, message)
            logger.info("Rain alert sent. Rain intensity: %s", average_rain)
            alert_active = False  # Disable alert until re-enabled manually
    else:
        logger.info("No valid rain data received.")

if __name__ == '__main__':
    while True:
        check_rain_alert()
        time.sleep(60)  # Check every minute, adjust as necessary