# weather_indicators.py
from math import log, log10

def calculate_indicators(ambient_temperature, sky_temperature, sqm_lux):
    cloud_coverage = None
    cloud_coverage_indicator = None
    brightness = None
    bortle = None

    try:
        ambient_temperature = float(ambient_temperature)
        sky_temperature = float(sky_temperature)
        sqm_lux = float(sqm_lux)
    except ValueError as e:
        print(f"Error: Invalid input data - {e}")
        return cloud_coverage, cloud_coverage_indicator, brightness, bortle

    if sky_temperature is not None and ambient_temperature is not None:
        cloud_coverage = (sky_temperature - ambient_temperature) / ambient_temperature
        cloud_coverage_indicator = ambient_temperature - sky_temperature
    else:
        print("Error: Missing sky_temperature or ambient_temperature.")

    if sqm_lux is not None and sqm_lux > 0:
        brightness = 22.0 - 2.512 * log10(sqm_lux)
        bortle = 1539.7 * 2.7 ** (-0.28 * brightness)
    else:
        print("Error: Invalid sqm_lux data.")

    return cloud_coverage, cloud_coverage_indicator, brightness, bortle

# def calculate_dewPoint(T, RH):
#     b = 17.62
#     c = 243.12
#     gamma = (b * T / (c + T)) + log(RH / 100.0)
#     dewPoint = (c * gamma) / (b - gamma)
#     return dewPoint

