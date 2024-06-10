import unittest
from unittest.mock import patch
import rain_alarm  # Import the module that contains the rain detection and notification code

class TestRainAlarm(unittest.TestCase):
    def setUp(self):
        # Load settings and prepare environment variables if necessary
        rain_alarm.load_settings()
        self.user_key = "test_user_key"  # Example user key
        self.api_token = "test_api_token"  # Example API token

    @patch('rain_alarm.send_pushover_notification')
    def test_rain_alert_triggered(self, mock_notification):
        # Simulate rain alert scenario
        average_rain = rain_alarm.settings["raining_threshold"] + 1  # Set rain above threshold

        with patch.dict('os.environ', {'PUSHOVER_USER_KEY': self.user_key, 'PUSHOVER_API_TOKEN': self.api_token}):
            rain_alarm.check_rain_alert(average_rain)
            mock_notification.assert_called_once_with(
                self.user_key,
                self.api_token,
                f"Alert: It's raining! Rain intensity: {average_rain}"
            )

    @patch('rain_alarm.send_pushover_notification')
    def test_rain_alert_not_triggered_below_threshold(self, mock_notification):
        # Simulate no rain alert scenario
        average_rain = rain_alarm.settings["raining_threshold"] - 1  # Set rain below threshold

        with patch.dict('os.environ', {'PUSHOVER_USER_KEY': self.user_key, 'PUSHOVER_API_TOKEN': self.api_token}):
            rain_alarm.check_rain_alert(average_rain)
            mock_notification.assert_not_called()

    @patch('rain_alarm.send_pushover_notification')
    def test_no_rain_data_received(self, mock_notification):
        # Test behavior when no valid rain data is received
        average_rain = None

        with patch.dict('os.environ', {'PUSHOVER_USER_KEY': self.user_key, 'PUSHOVER_API_TOKEN': self.api_token}):
            rain_alarm.check_rain_alert(average_rain)
            mock_notification.assert_not_called()

if __name__ == '__main__':
    unittest.main()
