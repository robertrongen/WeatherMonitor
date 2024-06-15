# control.py
#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
from settings import load_settings
from system_monitor import get_cpu_temperature
from fetch_data import get_temperature_humidity, get_sky_data, get_rain_wind_data, get_allsky_data
from weather_indicators import calculate_indicators, calculate_dewPoint
from meteocalc import heat_index, Temp
from store_data import store_sky_data, setup_database
from app_logging import setup_logger
from rain_alarm import check_rain_alert
from app import notify_new_data, get_db_connection

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    print("GPIO library can only be run on a Raspberry Pi, importing mock GPIO")
    GPIO_AVAILABLE = False

logger = setup_logger('control', 'control.log')
settings = load_settings()  # Initial load of settings

def setup_gpio():
    if GPIO_AVAILABLE:
        # Relay GPIO pins on the Raspberry Pi as per Waveshare documentation https://www.waveshare.com/wiki/RPi_Relay_Board
        Relay_Ch1 = 26  # Fan In
        Relay_Ch2 = 20  # Dew Heater
        Relay_Ch3 = 21  # Fan Out
        GPIO.setwarnings(False)  # Set GPIO warnings to false (optional, to avoid nuisance warnings)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([Relay_Ch1, Relay_Ch2, Relay_Ch3], GPIO.OUT, initial=GPIO.HIGH)
        logger.info("GPIO setup completed")

if GPIO_AVAILABLE:
    setup_gpio()

def control_fan_heater():
    try:
        global settings
        temp_hum_url = settings["temp_hum_url"]
        settings = load_settings()  # Refresh settings on each call
        data = {
            "temperature": None,
            "humidity": None,
            "dew_point": None,
            "heat_index": None,
            "fan_status": "OFF",
            "heater_status": "OFF",
            "cpu_temperature": None,
            "raining": None,
            "light": None,
            "sky_temperature": None,
            "ambient_temperature": None,
            "sqm_ir": None,
            "sqm_full": None,
            "sqm_visible": None,
            "sqm_lux": None,
            "cloud_coverage": None,
            "cloud_coverage_indicator": None,
            "brightness": None,
            "bortle": None,
            "wind": None,
            "camera_temp": None,
            "star_count": None,
            "day_or_night": None
        }

        if not isinstance(temp_hum_url, str) or 'http' not in temp_hum_url:
            logger.error(f"Invalid URL passed: {temp_hum_url}, using default URL instead")
            temp_hum_url = "https://meetjestad.net/data/?type=sensors&ids=580&format=json&limit=1"
        else:
            try:
                temperature, humidity = get_temperature_humidity(temp_hum_url)
                if temperature is not None:
                    data["temperature"] = round(temperature, 1)
                if humidity is not None:
                    data["humidity"] = round(humidity, 1)
            except Exception as e:
                logger.error(f"Failed to fetch temperature and humidity: {e}")

        try:
            raining, wind = get_rain_wind_data(settings["serial_port_rain"], settings["baud_rate"])
            if raining is not None:
                check_rain_alert(raining)
                data["raining"] = raining
            if wind is not None:
                data["wind"] = wind
        except Exception as e:
            logger.error(f"Failed to fetch rain and wind sensor data: {e}")

        try:
            cpu_temperature = get_cpu_temperature()
            if cpu_temperature is not None:
                data["cpu_temperature"] = round(cpu_temperature, 0)
        except Exception as e:
            logger.error(f"Failed to fetch CPU temperature: {e}")

        try:
            camera_temp, star_count, day_or_night = get_allsky_data()
            if camera_temp is not None:
                data["camera_temp"] = camera_temp
            if star_count is not None:
                data["star_count"] = star_count
            if day_or_night is not None:
                data["day_or_night"] = day_or_night
        except Exception as e:
            logger.error(f"Failed to fetch allsky data: {e}")

        if data["temperature"] is not None and data["humidity"] is not None:
            try:
                dewPoint = round(calculate_dewPoint(data["temperature"], data["humidity"]), 2)
                temp = Temp(data["temperature"], 'c')
                heatIndex = round(heat_index(temp, data["humidity"]).c, 1)
                data["dew_point"] = dewPoint
                data["heat_index"] = heatIndex
            except Exception as e:
                logger.error(f"Failed to compute dew point or heat index: {e}")

        if data["temperature"] is not None:
            data["fan_status"] = "ON" if (
                data["camera_temp"] is not None and data["camera_temp"] > 25
                or data["temperature"] > settings["ambient_temp_threshold"]
                or data["temperature"] < (data.get("dew_point", float('inf')) + settings["dewpoint_threshold"])
                or data["cpu_temperature"] is not None and data["cpu_temperature"] > settings["cpu_temp_threshold"]
            ) else "OFF"

            data["heater_status"] = "OFF" if data["temperature"] > (data.get("dew_point", float('inf')) + settings["dewpoint_threshold"]) else "ON"

        if GPIO_AVAILABLE:
            try:
                GPIO.output(26, GPIO.LOW if data["fan_status"] == "ON" else GPIO.HIGH)
                GPIO.output(21, GPIO.LOW if data["fan_status"] == "ON" else GPIO.HIGH)
                GPIO.output(20, GPIO.LOW if data["heater_status"] == "ON" else GPIO.HIGH)
            except Exception as e:
                logger.error(f"GPIO operation failed: {e}")
                raise

        try:
            serial_data = get_sky_data(settings["serial_port_json"], settings["baud_rate"])
            if serial_data:
                data.update(serial_data)
        except Exception as e:
            logger.error(f"Failed to fetch sky sensor data: {e}")

        try:
            cloud_coverage, cloud_coverage_indicator, brightness, bortle = calculate_indicators(data["ambient_temperature"], data["sky_temperature"], data["sqm_lux"])
            if cloud_coverage is not None:
                data["cloud_coverage"] = round(cloud_coverage, 2)
            if cloud_coverage_indicator is not None:
                data["cloud_coverage_indicator"] = round(cloud_coverage_indicator, 2)
            if brightness is not None:
                data["brightness"] = round(brightness, 2)
            if bortle is not None:
                data["bortle"] = round(bortle, 2)
        except Exception as e:
            logger.error(f"Failed to compute weather indicators: {e}")

        # store data
        conn = get_db_connection()
        try:
            store_sky_data(data, conn)
            notify_new_data()
        except Exception as e:
            logger.error(f"Failed to store data: {e}")
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Unexpected error in control_fan_heater function: {e}")
        raise

if __name__ == '__main__':
    setup_database()
    try:
        logger.info("Starting control loop")
        control_fan_heater()
        while True:
            start_sleep_time = time.time()
            time.sleep(settings["sleep_time"])
            end_sleep_time = time.time()
            logger.info(f"Slept for {end_sleep_time - start_sleep_time} seconds")
            control_fan_heater()
    except KeyboardInterrupt:
        logger.info("Program stopped by user")
    finally:
        if GPIO_AVAILABLE:
            GPIO.cleanup()
