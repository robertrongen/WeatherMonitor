# rain_alarm.py
import os
import time
import requests
from settings import load_settings
from dotenv import load_dotenv
from app_logging import setup_logger
from fetch_data import get_serial_data

logger = setup_logger('control', 'control.log')
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

def check_rain_alert():
    """Check for rain alerts from the serial port and send notifications."""
    global alert_active
    if not alert_active:
        return

    user_key = os.getenv('PUSHOVER_USER_KEY')
    api_token = os.getenv('PUSHOVER_API_TOKEN')
    global settings
    settings = load_settings()
    rainThreshold = settings["raining_threshold"]
    serial_data = get_serial_data(settings["serial_port"], settings["baud_rate"])

    if serial_data.get('raining'):
        rain = float(serial_data.get('raining'))
        if rain < rainThreshold:
            logger.info("It's raining: %s", rain)
            message = "Alert: It's raining!!!!"
            send_pushover_notification(user_key, api_token, message)
            flash('Rain alert sent!', 'info')  # Flash a message
            # Disable alert until re-enabled manually
            alert_active = False
    else:
        print("No valid data received.")

if __name__ == '__main__':
    while True:
        check_rain_alert()
        time.sleep(30)