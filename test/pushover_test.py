import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

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

def main():
    # Load user credentials and API token from environment variables
    user_key = os.getenv('PUSHOVER_USER_KEY')
    api_token = os.getenv('PUSHOVER_API_TOKEN')
    
    # Check if the required credentials are available
    if not user_key or not api_token:
        print("User key or API token is missing. Please check your .env file.")
        return

    # Message to send
    message = "This is a test notification from the Pushover console test."

    # Sending the notification
    print("Sending Pushover notification...")
    result = send_pushover_notification(user_key, api_token, message)
    print("Response from Pushover:")
    print(result)

if __name__ == "__main__":
    main()
