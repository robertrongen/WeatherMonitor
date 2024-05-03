import sqlite3
import time
from datetime import datetime
import psutil
from fetch_data import get_cpu_temperature

# Database setup
conn = sqlite3.connect('sky_data.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS metrics (
    timestamp TEXT,
    cpu_temp REAL,
    cpu_usage REAL,
    memory_usage REAL,
    disk_usage REAL
)
''')
conn.commit()

def get_cpu_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp = f.read()
    return round(float(temp) / 1000, 0)

def log_metrics():
    cpu_temp = get_cpu_temperature()
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent

    c.execute('INSERT INTO metrics (timestamp, cpu_temp, cpu_usage, memory_usage, disk_usage) VALUES (?, ?, ?, ?, ?)',
        (datetime.now(), cpu_temp, cpu_usage, memory_usage, disk_usage))
    conn.commit()

    print(f"Logged at {datetime.now()}: CPU Temp: {cpu_temp}°C, CPU Usage: {cpu_usage}%, Memory Usage: {memory_usage}%, Disk Usage: {disk_usage}%")

try:
    while True:
        log_metrics()
        time.sleep(60)  # Log every minute
except KeyboardInterrupt:
    print("Stopped by user.")
finally:
    conn.close()
