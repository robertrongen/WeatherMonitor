# simulate_serial.py
import time
from unittest.mock import MagicMock
import serial

# Mock the serial port to simulate rain data
serial.Serial = MagicMock(return_value=MagicMock())
serial_port = serial.Serial('/dev/ttyUSB0', 11500, timeout=1)
serial_port.readline = MagicMock(side_effect=[
    b"raining,120\n",
    b"raining,130\n",
    b"raining,125\n",
    b"raining,122\n",
    b"raining,118\n",
])

# Example usage in your actual script
def read_rain_data(serial_port, num_samples=5):
    readings = []
    for _ in range(num_samples):
        line = serial_port.readline().decode().strip()
        _, value = line.split(',')
        readings.append(float(value))
        time.sleep(1)  # Simulate delay
    return readings

if __name__ == "__main__":
    readings = read_rain_data(serial_port)
    print("Simulated readings:", readings)
