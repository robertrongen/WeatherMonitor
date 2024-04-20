from math import log10

def calculate_indicators(ambient_temperature, sky_temperature, sqm_lux):
    try:
        ambient_temperature = float(ambient_temperature)
        sky_temperature = float(sky_temperature)
        sqm_lux = float(sqm_lux)
    except ValueError as e:
        print(f"Error: Invalid input data - {e}")
        return None, None, None, None

    if sky_temperature is None or ambient_temperature is None:
        print("Error: Missing temperature data.")
        return None, None, None, None

    if sqm_lux is None or sqm_lux == "" or sqm_lux == 0:
        print("Error: Invalid sqm_lux data.")
        return None, None, None, None

    cloud_coverage = (sky_temperature - ambient_temperature) / ambient_temperature
    cloud_coverage_indicator = ambient_temperature - sky_temperature
    brightness = 22.0 - 2.512 * log10(sqm_lux)
    bortle = 1539.7 * 2.7 ** (-0.28 * brightness)

    return cloud_coverage, cloud_coverage_indicator, brightness, bortle

def calculate_dew_point(T, RH):
    b = 17.62
    c = 243.12
    gamma = (b * T / (c + T)) + math.log(RH / 100.0)
    dew_point = (c * gamma) / (b - gamma)
    return dew_point
