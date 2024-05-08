# rain_alarm.py
import os
import time
import requests
from statistics import mean
from settings import load_settings
from fetch_data import get_serial_data  # Import the function to get serial data including rain data
from dotenv import load_dotenv
from app_logging import setup_logger

logger = setup_logger('rain', 'rain.log')
load_dotenv()  # Load environment variables from .env file
settings = load_settings()  # Refresh settings on each call
alert_active = False

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
    _, average_rain = get_serial_data(settings["serial_port"], settings["baud_rate"])
    logger.info("average_rain measured: %s", average_rain)
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
        try:
            check_rain_alert()
            time.sleep(10)
        except Exception as e:
            logger.error("An error occurred: %s", e)
            time.sleep(60)  # Wait a bit longer after an error to prevent rapid failures
