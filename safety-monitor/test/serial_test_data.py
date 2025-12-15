import os
import pty
import serial
import time
import random
import json

def generate_json():
    data = {
        'raining': str(random.randint(400, 500)),
        'light': str(random.randint(27000, 29000)),
        'sky_temperature': f"{random.uniform(-2, 0):.2f}",
        'ambient_temperature': f"{random.uniform(50, 60):.2f}",
        'sqm_ir': 65535,
        'sqm_full': 65575,
        'sqm_visible': 40,
        'sqm_lux': 20
    }
    return json.dumps(data)

def send_serial_data(master_fd, x, y):
    while True:
        # Send JSON data every 20 seconds
        os.write(master_fd, (generate_json() + '\n').encode())
        time.sleep(20)

        # Send rainsensor data every second
        for _ in range(20):
            rainsensor_value = f"Rainsensor,{random.randint(x, y)}\n"
            os.write(master_fd, rainsensor_value.encode())
            time.sleep(1)

def main():
    x = int(input("Enter the lower bound for Rainsensor value (X): "))
    y = int(input("Enter the upper bound for Rainsensor value (Y): "))

    master_fd, slave_fd = pty.openpty()  # Open a pseudoterminal
    serial_port = os.ttyname(slave_fd)  # Get the name of the slave device

    print(f"Writing to virtual serial port at {serial_port}. Connect your program to this port.")

    try:
        send_serial_data(master_fd, x, y)
    except KeyboardInterrupt:
        print("Terminated by user")
    finally:
        os.close(master_fd)
        os.close(slave_fd)

if __name__ == "__main__":
    main()
