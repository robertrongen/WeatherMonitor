# system_monitor.py
import sqlite3
import time
from threading import Thread
import psutil
from app_logging import setup_logger

logger = setup_logger('system_monitor', 'system_monitor.log')

def get_cpu_temperature():
    """Fetch the CPU temperature of the system, useful for monitoring and control."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = f.read()
        return round(float(temp) / 1000, 2)  # Convert millidegree Celsius to degree Celsius
    except Exception as e:
        logger.warning(f"Failed to fetch CPU temperature: {e}")
        return None

def get_cpu_usage():
    """Fetch the current CPU usage of the system."""
    try:
        return psutil.cpu_percent(interval=1)
    except Exception as e:
        logger.warning(f"Failed to fetch CPU usage: {e}")
        return None

def get_memory_usage():
    """Fetch the current memory usage of the system."""
    try:
        memory = psutil.virtual_memory()
        return memory.percent
    except Exception as e:
        logger.warning(f"Failed to fetch memory usage: {e}")
        return None

def get_disk_usage():
    """Fetch the disk usage for the root directory."""
    try:
        partition = psutil.disk_usage('/')
        return partition.percent
    except Exception as e:
        logger.warning(f"Failed to fetch disk usage: {e}")
        return None

def collect_system_metrics():
    """Collect system metrics like CPU temp, CPU usage, memory usage, and disk usage."""
    metrics = {
        'cpu_temp': get_cpu_temperature(),
        'cpu_usage': get_cpu_usage(),
        'memory_usage': get_memory_usage(),
        'disk_usage': get_disk_usage()
    }
    return metrics

def get_db_connection():
    """Establish a connection to the database."""
    conn = sqlite3.connect('sky_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_metrics_table():
    """Create the Metrics table if it doesn't exist."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Metrics (
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_temp REAL,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL
            )
        """)
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to create Metrics table: {e}")
    finally:
        conn.close()

def store_system_metrics(metrics):
    """Store collected system metrics in the Metrics table."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Metrics (timestamp, cpu_temp, cpu_usage, memory_usage, disk_usage)
            VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?)
        """, (metrics['cpu_temp'], metrics['cpu_usage'], metrics['memory_usage'], metrics['disk_usage']))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to store system metrics: {e}")
    finally:
        conn.close()

def monitor_and_log():
    metrics = collect_system_metrics()
    if metrics['cpu_temp'] > 85:  # Threshold for CPU temperature
        logger.warning(f"High CPU temperature: {metrics['cpu_temp']}°C")
    if metrics['disk_usage'] > 90:  # Threshold for disk usage in percentage
        logger.error(f"High disk usage: {metrics['disk_usage']}%")
    logger.info(f"Metrics collected: {metrics}")
    store_system_metrics(metrics)

def background_metrics_collector():
    """Run the metrics collector in the background."""
    while True:
        try:
            monitor_and_log()
            time.sleep(300)   
        except Exception as e:
            logger.error(f"Error in background_metrics_collector: {e}")

def start_background_metrics_collector():
    metrics_thread = Thread(target=background_metrics_collector)
    metrics_thread.daemon = True  # Ensure it exits when the main program exits
    metrics_thread.start()

if __name__ == '__main__':
    create_metrics_table()
    start_background_metrics_collector()

    try:
        while True:
            monitor_and_log()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("System monitor service interrupted by user")