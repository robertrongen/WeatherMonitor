# rain_alarm.py
import os
import requests
from settings import load_settings
from dotenv import load_dotenv
from app_logging import setup_logger
from app import get_alert_active, set_alert_active
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

def check_rain_alert(average_rain):
    """Check for rain alerts from the serial port and send notifications."""
    alert_active = get_alert_active()  # Get the current alert state from the file
    if not alert_active:
        logger.info("Rain alert not active")
        return

    settings = load_settings()
    user_key = os.getenv('PUSHOVER_USER_KEY')
    api_token = os.getenv('PUSHOVER_API_TOKEN')
    rain_threshold = settings["raining_threshold"]

    if average_rain is not None:
        logger.info(f"Average rain intensity: {average_rain}")
        if average_rain < rain_threshold:
            message = "Alert: It's raining! Rain intensity: {}".format(average_rain)
            send_pushover_notification(user_key, api_token, message)
            logger.info(f"Rain alert sent. Rain intensity: {average_rain}")
            set_alert_active(False) # Disable alert after sending notification
    else:
        logger.info(f"No valid rain data received: {average_rain}")
