import unittest
from unittest.mock import patch, MagicMock
import control  # This assumes your main script is named 'control.py'

class TestControlSystem(unittest.TestCase):
    def setUp(self):
        # Mock data to be used in tests
        self.sample_data = {
            'temperature': 20.5,
            'humidity': 50,
            'sky_temperature': 15.5,
            'sqm_lux': 200,
            'cpu_temperature': 55
        }
        
        # Expected outcomes for the mocked data
        self.expected_indicators = {
            'cloud_coverage': (self.sample_data['sky_temperature'] - self.sample_data['temperature']) / self.sample_data['temperature'],
            'cloud_coverage_indicator': self.sample_data['temperature'] - self.sample_data['sky_temperature'],
            'brightness': 22.0 - 2.512 * (self.sample_data['sqm_lux']**-1),
            'bortle': 1539.7 * 2.7 ** (-0.28 * (22.0 - 2.512 * (self.sample_data['sqm_lux']**-1)))
        }

    @patch('control.GPIO.output')
    @patch('control.store_sky_data')
    @patch('control.get_cpu_temperature')
    @patch('control.get_serial_data')
    @patch('control.get_temperature_humidity')
    def test_control_fan_heater(self, mock_get_temp_humidity, mock_get_serial_data, mock_get_cpu_temperature, mock_store_sky_data, mock_gpio_output):
        # Set return values for mocks
        mock_get_temp_humidity.return_value = (self.sample_data['temperature'], self.sample_data['humidity'])
        mock_get_serial_data.return_value = {'sky_temperature': self.sample_data['sky_temperature'], 'sqm_lux': self.sample_data['sqm_lux']}
        mock_get_cpu_temperature.return_value = self.sample_data['cpu_temperature']
        
        # Run the control function
        control.control_fan_heater()
        
        # Check if data is calculated correctly and stored
        mock_store_sky_data.assert_called_once()
        stored_data = mock_store_sky_data.call_args[0][0]  # Grab the data dict passed to store_sky_data
        
        # Assert calculations
        self.assertAlmostEqual(stored_data['cloud_coverage'], self.expected_indicators['cloud_coverage'])
        self.assertAlmostEqual(stored_data['cloud_coverage_indicator'], self.expected_indicators['cloud_coverage_indicator'])
        self.assertAlmostEqual(stored_data['brightness'], self.expected_indicators['brightness'])
        self.assertAlmostEqual(stored_data['bortle'], self.expected_indicators['bortle'])

        # Check GPIO calls for fan and heater
        fan_status = GPIO.LOW if self.sample_data['temperature'] > 20 or self.sample_data['cpu_temperature'] > 65 else GPIO.HIGH
        heater_status = GPIO.LOW if self.sample_data['temperature'] < (self.sample_data['temperature'] - 2) else GPIO.HIGH
        
        # Assert GPIO calls
        mock_gpio_output.assert_any_call(control.Relay_Ch1, fan_status)
        mock_gpio_output.assert_any_call(control.Relay_Ch2, heater_status)

if __name__ == '__main__':
    unittest.main()
