import unittest
from unittest.mock import patch, MagicMock
import rain_alarm  # Assuming your main script is named rain_alarm.py

class TestRainAlarm(unittest.TestCase):
    @patch('rain_alarm.serial.Serial')  # Mock the Serial class in rain_alarm module
    @patch('rain_alarm.send_pushover_notification')  # Mock the notification function
    def test_rain_alert(self, mock_notification, mock_serial):
        # Setup mock for serial port
        mock_ser = MagicMock()
        mock_ser.readline.return_value = b'Raining,Yes\n'
        mock_serial.return_value.__enter__.return_value = mock_ser

        # Call the function that checks for rain and sends notification
        rain_alarm.check_rain_alert()

        # Assert notification was sent
        mock_notification.assert_called_once()
        self.assertTrue(mock_notification.called)
        self.assertIn('Alert: It\'s raining! Please check your surroundings.', mock_notification.call_args[0][2])

if __name__ == '__main__':
    unittest.main()
