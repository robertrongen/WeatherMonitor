import requests
import json
import time
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENWEATHERMAP_API_KEY")
station_id = os.getenv("OPENWEATHERMAP_ID")

previous_data = None

def should_send_data(new_data, old_data, threshold=0.5):
    if old_data is None:
        return True
    return abs(new_data["rain"] - old_data["rain"]) > threshold or \
        abs(new_data["light"] - old_data["light"]) > threshold or \
        abs(new_data["air_temperature"] - old_data["air_temperature"]) > threshold or \
        abs(new_data["sky_temperature"] - old_data["sky_temperature"]) > threshold or \
        abs(new_data["ambient_temperature"] - old_data["ambient_temperature"]) > threshold or \
        abs(new_data["humidity"] - old_data["humidity"]) > threshold

def send_data_to_openweathermap(data):
    url = f"http://api.openweathermap.org/data/3.0/measurements?appid={api_key}"
    headers = {"Content-Type": "application/json"}

    # Convert string to float, and use None if the string is empty
    def to_float(s):
        return float(s) if s else None

    payload = [{
        "station_id": station_id,
        "dt": int(time.time()),
        "temperature": to_float(data.get("air_temperature")),
        "humidity": to_float(data.get("humidity")),
        "sky_temperature": to_float(data.get("sky_temperature")),
        "ambient_temperature": to_float(data.get("ambient_temperature")),
        "rain": to_float(data.get("rain")),
        "light": to_float(data.get("light"))
    }]
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 204:
            print("Successfully sent data to OpenWeatherMap.")
        else:
            print(f"Failed to send data. HTTP Status Code: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    previous_data = None
    while True:
        # Fetch data from ESP
        esp_data = fetch_data_from_esp()
        if esp_data:
            print("Received data from ESP:")
            print(json.dumps(esp_data, indent=4))
            
            if should_send_data(esp_data, previous_data):
                send_data_to_openweathermap(esp_data)
                previous_data = esp_data
        else:
            print("Failed to fetch data from ESP.")
        
        # Fetch data from Meetjestad
        meetjestad_data = fetch_data_from_meetjestad()
        if meetjestad_data:
            print("Received data from Meetjestad:")
            print(json.dumps(meetjestad_data, indent=4))
        else:
            print("Failed to fetch data from Meetjestad.")
        
        time.sleep(90)