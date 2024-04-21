# store_data.py
import sqlite3
from datetime import datetime
from app_logging import setup_logger

logger = setup_logger('store_data', 'store_data.log')

DATABASE_NAME = "sky_data.db"

def setup_database(conn=None):
    if conn is None:
        conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Correctly define the CREATE TABLE SQL with proper data types and comma separations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sky_data (
            timestamp DATETIME PRIMARY KEY,
            temperature REAL,
            humidity REAL,
            dew_point REAL,
            fan_status TEXT,
            heater_status TEXT,
            cpu_temperature REAL,
            raining TEXT,
            light REAL,
            sky_temperature REAL,
            ambient_temperature REAL,
            sqm_ir INTEGER,
            sqm_visible INTEGER,
            sqm_lux REAL,
            cloud_coverage REAL,
            cloud_coverage_indicator REAL,
            brightness REAL,
            bortle REAL
        )
    """)

    conn.commit()
    conn.close()

def store_sky_data(data, conn):
    logger.info(f"Attempting to store data: {data}")
    # conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO sky_data (
                timestamp, 
                temperature, 
                humidity, 
                dew_point, 
                fan_status, 
                heater_status,
                cpu_temperature,
                raining, 
                light, 
                sky_temperature, 
                ambient_temperature, 
                sqm_ir, 
                sqm_visible, 
                sqm_lux, 
                cloud_coverage, 
                cloud_coverage_indicator, 
                brightness, 
                bortle
            )
            VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['temperature'],
            data['humidity'],
            data['dew_point'],
            data['fan_status'],
            data['heater_status'],
            data['cpu_temperature'],
            data['raining'],
            data['light'],
            data['sky_temperature'],
            data['ambient_temperature'],
            data['sqm_ir'],
            data['sqm_visible'],
            data['sqm_lux'],
            data['cloud_coverage'],
            data['cloud_coverage_indicator'],
            data['brightness'],
            data['bortle']
        ))
        conn.commit()
        logger.info("Data stored successfully")
    except Exception as e:
        logger.critical(f"Failed to store data: {e}")

if __name__ == "__main__":
    setup_database()  # Set up the database once at the start
