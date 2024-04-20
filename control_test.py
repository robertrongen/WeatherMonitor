import unittest
from unittest.mock import patch
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

if __name__ == '__main__':
    unittest.main()
