#weather_monitor.py

import json
import time
from store_data import setup_database, store_weather_data
from fetch_data import fetch_data_from_esp, fetch_data_from_meetjestad, data_has_changed, calculate_indicators

if __name__ == "__main__":
    setup_database()  # Set up the database once at the start
    previous_data = None

    while True:
        esp_data = fetch_data_from_esp()
        meetjestad_data = fetch_data_from_meetjestad()

        # Check if data was successfully fetched from both sources
        if esp_data is None or meetjestad_data is None:
            print("Failed to fetch data from one or both sources. Retrying...")
            time.sleep(10)
            continue

        # Combine the data from both sources
        combined_data = {**esp_data, **meetjestad_data}

        # Check if any data has changed
        if data_has_changed(combined_data, previous_data):
            cloud_coverage, cloud_coverage_indicator, brightness, bortle = calculate_indicators(combined_data)
            combined_data["cloud_coverage"] = cloud_coverage
            combined_data["cloud_coverage_indicator"] = cloud_coverage_indicator
            combined_data["brightness"] = brightness
            combined_data["bortle"] = bortle
            store_weather_data(combined_data)
            previous_data = combined_data  # Update the previous data
            print("Data has changed. New data stored in database: " + str(combined_data))
        # Sleep for 10 seconds before fetching again
        time.sleep(10)


