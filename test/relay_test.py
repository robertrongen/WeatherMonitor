# test_relay.py
#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time

# Relay GPIO pins
Relay_Ch1 = 26  # Fan In
Relay_Ch2 = 20  # Dew Heater
Relay_Ch3 = 21  # Fan Out

# Setup GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([Relay_Ch1, Relay_Ch2, Relay_Ch3], GPIO.OUT, initial=GPIO.HIGH)  # Relays off initially

def control_device(pin, action):
    if action == 'on':
        GPIO.output(pin, GPIO.LOW)  # Turn device ON
        print(f"Device on pin {pin} turned ON")
    elif action == 'off':
        GPIO.output(pin, GPIO.HIGH)  # Turn device OFF
        print(f"Device on pin {pin} turned OFF")

def main():
    try:
        while True:
            # User menu for controlling devices
            print("\nAvailable Commands:")
            print("  1. Turn ON Fan In")
            print("  2. Turn OFF Fan In")
            print("  3. Turn ON Dew Heater")
            print("  4. Turn OFF Dew Heater")
            print("  5. Turn ON Fan Out")
            print("  6. Turn OFF Fan Out")
            print("  7. Exit")
            choice = input("Enter your choice: ")

            if choice == '1':
                control_device(Relay_Ch1, 'on')
            elif choice == '2':
                control_device(Relay_Ch1, 'off')
            elif choice == '3':
                control_device(Relay_Ch2, 'on')
            elif choice == '4':
                control_device(Relay_Ch2, 'off')
            elif choice == '5':
                control_device(Relay_Ch3, 'on')
            elif choice == '6':
                control_device(Relay_Ch3, 'off')
            elif choice == '7':
                print("Exiting program")
                break
            else:
                print("Invalid choice. Please try again.")

    except KeyboardInterrupt:
        print("Program terminated manually")
    finally:
        GPIO.cleanup()  # Clean up GPIO to ensure all relays are turned off

if __name__ == "__main__":
    main()
