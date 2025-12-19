# system_monitor.py
# === PARTIALLY DEPRECATED ===
# Database storage and background monitoring removed.
# Only get_cpu_temperature() is retained and used by control.py.
# All other functions are deprecated stubs.
# ================================

import logging
import warnings

warnings.warn("Most functions in system_monitor.py are deprecated", DeprecationWarning, stacklevel=2)

logger = logging.getLogger('system_monitor')
logger.setLevel(logging.WARNING)

def get_cpu_temperature():
    """Fetch the CPU temperature of the system (ACTIVE - used by control.py)"""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = f.read()
        return round(float(temp) / 1000, 2)  # Convert millidegree Celsius to degree Celsius
    except Exception as e:
        logger.warning(f"Failed to fetch CPU temperature: {e}")
        return None

# === DEPRECATED FUNCTIONS (stubs) ===

def get_cpu_usage():
    """DEPRECATED: No longer used"""
    return None

def get_memory_usage():
    """DEPRECATED: No longer used"""
    return None

def get_disk_usage():
    """DEPRECATED: No longer used"""
    return None

def collect_system_metrics():
    """DEPRECATED: No longer used"""
    return {}

def get_db_connection():
    """DEPRECATED: Database removed"""
    raise NotImplementedError("Database functionality removed")

def create_metrics_table():
    """DEPRECATED: Database removed"""
    logger.warning("create_metrics_table() called but is deprecated")
    pass

def store_system_metrics(metrics):
    """DEPRECATED: Database removed"""
    pass

def monitor_and_log():
    """DEPRECATED: Background monitoring removed"""
    pass

def background_metrics_collector():
    """DEPRECATED: Background monitoring removed"""
    pass

def start_background_metrics_collector():
    """DEPRECATED: Background monitoring removed"""
    logger.warning("start_background_metrics_collector() called but is deprecated - no action taken")
    pass

if __name__ == '__main__':
    print("system_monitor.py: Most functionality deprecated")
    print("Only get_cpu_temperature() is active and used by control.py")
    cpu_temp = get_cpu_temperature()
    if cpu_temp:
        print(f"Current CPU temperature: {cpu_temp}°C")
