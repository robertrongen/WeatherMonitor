# send_alerts.py

import requests

def send_alert(message):
    url = "YOUR_NINA_ENDPOINT"
    payload = {
        "alert": message
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Alert sent successfully!")
    else:
        print(f"Failed to send alert. HTTP Status Code: {response.status_code}")
