# rain_alarm.py
import os
import requests
from settings import load_settings
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

def check_rain_alert(average_rain):
    """Check for rain alerts from the serial port and send notifications."""
    global alert_active
    if not alert_active:
        return

    global settings
    settings = load_settings()
    user_key = os.getenv('PUSHOVER_USER_KEY')
    api_token = os.getenv('PUSHOVER_API_TOKEN')
    rain_threshold = settings["raining_threshold"]
    print("average_rain measured: %s", average_rain)
    logger.info("average_rain measured: %s", average_rain)
    if average_rain is not None:
        logger.info("Average rain intensity: %s", average_rain)
        if average_rain < rain_threshold:
            message = "Alert: It's raining! Rain intensity: {}".format(average_rain)
            send_pushover_notification(user_key, api_token, message)
            print(f"Rain alert sent. Rain intensity: %s", average_rain)
            logger.info(f"Rain alert sent. Rain intensity: %s", average_rain)
            alert_active = False  # Disable alert until re-enabled manually
    else:
        print(f"No valid rain data received: {average_rain}")
        logger.info(f"No valid rain data received: {average_rain}")
