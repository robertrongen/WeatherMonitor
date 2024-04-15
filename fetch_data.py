# fetch_data.py

import requests
import json
import time
from math import log10

MEETJESTAD_URL = "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1"
ESP_URL = "http://skymonitor.local/json"

def fetch_data_from_meetjestad():
    expected_keys = ["longitude", "latitude", "temperature", "humidity"]
    try:
        response = requests.get(MEETJESTAD_URL)
        if response.status_code == 200:
            raw_data = response.text
            # print(f"Raw data from Meetjestad: {raw_data}")  # Debugging statement

            data = json.loads(raw_data)[0]  # Assuming the first item in the returned list is the relevant data
            processed_data = {
                "longitude": str(data["longitude"]),
                "latitude": str(data["latitude"]),
                "temperature": str(data["temperature"]),
                "humidity": str(data["humidity"])
            }
            # print(f"Processed data from Meetjestad: {processed_data}")  # Debugging statement
            return processed_data
        else:
            print(f"Failed to get data from Meetjestad. HTTP Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching data from Meetjestad: {e}")
        return None

def fetch_data_from_esp():
    expected_keys = ["rain", "light", "sky_temperature", "ambient_temperature", "sqm_ir", "sqm_full", "sqm_visible", "sqm_lux"]
    try:
        response = requests.get(ESP_URL)
        if response.status_code == 200:
            data = json.loads(response.text)

            # Convert specific data types
            data["sqm_ir"] = int(data["sqm_ir"])
            data["sqm_full"] = int(data["sqm_full"])
            data["sqm_visible"] = int(data["sqm_visible"])
            data["sqm_lux"] = float(data["sqm_lux"])

            return data
        else:
            print(f"Failed to get data. HTTP Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching data from ESP: {e}")
        return None

def data_has_changed(current_data, previous_data):
    if not previous_data:
        return True  # If there's no previous data, assume data has changed

    for key in current_data:
        if current_data[key] != previous_data.get(key):
            return True  # If any value has changed, return True

    return False  # If no values have changed, return False

def calculate_indicators(data):
    # Cloud Coverage Indicator
    ambient_temperature = data.get("temperature")
    if ambient_temperature is None:
        print("Error: Missing temperature data from Meetjestad.")
        return None, None, None, None
    try:
        ambient_temperature = float(ambient_temperature)
    except ValueError:
        print("Error: Invalid temperature data from Meetjestad.")
        return None, None, None, None

    sky_temperature = data.get("sky_temperature")
    if sky_temperature is None:
        print("Error: Missing sky_temperature data from ESP.")
        return None, None, None, None
    try:
        sky_temperature = float(sky_temperature)
    except ValueError:
        print("Error: Invalid sky_temperature data from ESP.")
        return None, None, None, None

    cloud_coverage = (sky_temperature - ambient_temperature) / ambient_temperature
    cloud_coverage_indicator = ambient_temperature - sky_temperature

    # Brightness Indicator
    sqm_lux = data.get("sqm_lux")
    if sqm_lux is None or sqm_lux == "":
        print("Error: Missing sqm_lux data.")
        return None, None, None, None
    try:
        sqm_lux = float(sqm_lux)
    except ValueError:
        print("Error: Invalid sqm_lux data.")
        return None, None, None, None

    if sqm_lux == 0:
        print("Error: sqm_lux is 0.")
        return None, None, None, None

    brightness = 22.0 - 2.512 * log10(sqm_lux)
    bortle = 1539.7 * 2.7 ** (-0.28 * brightness)

    return cloud_coverage, cloud_coverage_indicator, brightness, bortle

