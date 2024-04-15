# store_data.py

import sqlite3

DATABASE_NAME = "weather_data.db"

def setup_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Create the weather_data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            timestamp DATETIME PRIMARY KEY,
            raining TEXT,
            light TEXT,
            sky_temperature TEXT,
            ambient_temperature TEXT,
            humidity TEXT,
            longitude TEXT,
            latitude TEXT,
            sqm_ir INTEGER,
            sqm_full INTEGER,
            sqm_visible INTEGER,
            sqm_lux REAL,
            cloud_coverage REAL,
            cloud_coverage_indicator REAL,
            brightness REAL,
            bortle REAL
        )
    """)

    # Create the observations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            cloud_condition TEXT,
            rain_condition TEXT,
            moon_visibility TEXT,
            temperature REAL,
            sky_temperature REAL,
            cloud_coverage_indicator REAL,
            sqm_lux REAL,
            brightness REAL,
            bortle REAL
            dewpoint REAL,
            fan_status TEXT,
            heater_status TEXT,
        );
    """)

    conn.commit()
    conn.close()

def store_weather_data(data):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    print("data stored: " + str(data))
    # Insert combined data into the weather_data table with the current timestamp
    cursor.execute("""
        INSERT INTO weather_data (
            timestamp, 
            raining, 
            light, 
            sky_temperature, 
            ambient_temperature, 
            humidity, 
            longitude, 
            latitude, 
            sqm_ir, 
            sqm_full, 
            sqm_visible, 
            sqm_lux, 
            cloud_coverage, 
            cloud_coverage_indicator, 
            brightness, 
            bortle
        )
        VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
            data["raining"], 
            data["light"], 
            data["sky_temperature"], 
            data["ambient_temperature"], 
            data["humidity"], 
            data["longitude"], 
            data["latitude"], 
            data["sqm_ir"], 
            data["sqm_full"], 
            data["sqm_visible"], 
            data["sqm_lux"],
            data["cloud_coverage"],
            data["cloud_coverage_indicator"],
            data["brightness"],
            data["bortle"],
            data["dewpoint"],
            data["fan_status"],
            data["heater_status"],
        )
    )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()  # Set up the database once at the start