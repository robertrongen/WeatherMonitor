import serial
import json
from app_logging import setup_logger
logger = setup_logger('fetch_data', 'fetch_data.log')

def fetch_and_print_first_json(serial_port='/dev/ttyUSB0', baud_rate=115200):
    """
    Reads from a serial port until it receives a valid JSON string, prints it, and then stops.
    """
    # Open the serial port
    ser = serial.Serial(serial_port, baud_rate, timeout=1)
    logger.info(f"Opened serial port {serial_port} at {baud_rate} baud rate.")
    
    # Open the serial port
    ser = serial.Serial(serial_port, baud_rate, timeout=1)
    logger.info(f"er serial port {serial_port} at {baud_rate} baud rate.")
    
    try:
        while True:
            line = ser.readline().decode('utf-8').strip()
            if line:
                logger.debug(f"Received line: {line}")
                try:
                    # Try to parse the line as JSON
                    data = json.loads(line)
                    print("Received JSON data:", json.dumps(data, indent=4))
                    logger.info("Valid JSON data received and printed.")
                    break  # Stop after successfully receiving and printing a JSON object
                except json.JSONDecodeError:
                    # Ignore lines that are not valid JSON
                    logger.debug("Line is not valid JSON, skipping.")
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        ser.close()
        loggerc.info("Closed serial port.")

if __name__ == '__main__':
    setup_logging()
    fetch_and_print_first_json()
