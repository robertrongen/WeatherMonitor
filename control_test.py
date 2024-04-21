import unittest
from math import log10
from unittest.mock import patch
from weather_indicators import calculate_indicators
import control

class TestControlSystem(unittest.TestCase):
    @patch('control.store_sky_data')
    @patch('control.get_cpu_temperature', return_value=55)
    @patch('control.get_serial_data', return_value={'sky_temperature': 15.5, 'sqm_lux': 200})
    @patch('control.get_temperature_humidity', return_value=(20.5, 50))
    def test_data_storage(self, mock_get_temp_humidity, mock_get_serial_data, mock_get_cpu_temperature, mock_store_sky_data):
        # Execute the function that triggers data storage
        control.control_fan_heater()

        # Assert that store_sky_data was called exactly once
        mock_store_sky_data.assert_called_once()

        # Extract the data passed to store_sky_data
        args, kwargs = mock_store_sky_data.call_args
        stored_data = args[0]

        # Verify that the stored data matches expected values
        self.assertEqual(stored_data['temperature'], 20.5)
        self.assertEqual(stored_data['humidity'], 50)
        self.assertEqual(stored_data['cpu_temperature'], 55)
        self.assertEqual(stored_data['fan_status'], 'ON' if 20.5 > 20 or 55 > 65 else 'OFF')
        self.assertEqual(stored_data['heater_status'], 'OFF' if 20.5 >= 18.5 else 'ON')
        # More assertions can be added to cover all fields

class TestWeatherIndicators(unittest.TestCase):
    def test_calculate_indicators(self):
        # Example input data
        ambient_temperature = 20.0  # degrees Celsius
        sky_temperature = 15.0  # degrees Celsius
        sqm_lux = 200.0  # arbitrary lux value

        # Expected outputs calculated manually or with known good data
        expected_cloud_coverage = (sky_temperature - ambient_temperature) / ambient_temperature
        expected_cloud_coverage_indicator = ambient_temperature - sky_temperature
        expected_brightness = 22.0 - 2.512 * log10(sqm_lux)
        expected_bortle = 1539.7 * 2.7 ** (-0.28 * expected_brightness)

        # Execute the function with test data
        cloud_coverage, cloud_coverage_indicator, brightness, bortle = calculate_indicators(
            ambient_temperature, sky_temperature, sqm_lux)

        # Assert that returned values match expected values with detailed messages
        self.assertAlmostEqual(cloud_coverage, expected_cloud_coverage, places=5,
            msg=f"Test for Cloud Coverage Failed: Expected {expected_cloud_coverage}, Got {cloud_coverage}")
        self.assertAlmostEqual(cloud_coverage_indicator, expected_cloud_coverage_indicator, places=5,
            msg=f"Test for Cloud Coverage Indicator Failed: Expected {expected_cloud_coverage_indicator}, Got {cloud_coverage_indicator}")
        self.assertAlmostEqual(brightness, expected_brightness, places=5,
            msg=f"Test for Brightness Failed: Expected {expected_brightness}, Got {brightness}")
        self.assertAlmostEqual(bortle, expected_bortle, places=5,
            msg=f"Test for Bortle Failed: Expected {expected_bortle}, Got {bortle}")

if __name__ == '__main__':
    unittest.main()
