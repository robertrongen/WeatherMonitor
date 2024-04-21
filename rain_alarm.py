# rain_alarm.py
import os
import serial
import requests
import settings
from dotenv import load_dotenv
from app_logging import setup_logger

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
    user_key = os.getenv('PUSHOVER_USER_KEY')
    api_token = os.getenv('PUSHOVER_API_TOKEN')
    with serial.Serial(settings["serial_port"], settings["baud_rate"], timeout=1) as ser:
        line = ser.readline().decode().strip()
        if "isRainingDigital: Raining,Yes" in line:
            message = "Alert: It's raining! Please check your surroundings."
            print("Rain detected, sending notification...")
            send_pushover_notification(user_key, api_token, message)
        else:
            print("No rain detected.")

# Example usage
if __name__ == '__main__':
    check_rain_alert()