# test_pushover_notification.py
from dotenv import load_dotenv
import os
from rain_alarm import send_pushover_notification  # Ensure this is correctly imported from your main script

load_dotenv()  # Load environment variables from .env file

def test_send_pushover_notification():
    user_key = os.getenv('PUSHOVER_USER_KEY')
    api_token = os.getenv('PUSHOVER_API_TOKEN')
    message = "Test message: Hello from Pushover!"

    response = send_pushover_notification(user_key, api_token, message)
    print("Pushover response:", response)

if __name__ == "__main__":
    test_send_pushover_notification()
