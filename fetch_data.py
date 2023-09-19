import requests
import json

def fetch_data_from_esp():
    url = "http://skymonitor.local/json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = json.loads(response.text)
            return data
        else:
            print(f"Failed to get data. HTTP Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    data = fetch_data_from_esp()
    if data:
        print("Received data:")
        print(json.dumps(data, indent=4))
    else:
        print("Failed to fetch data.")
