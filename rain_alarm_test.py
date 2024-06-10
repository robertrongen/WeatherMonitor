# rain_alarm.py
import unittest
from unittest.mock import patch
import rain_alarm

# Assuming the rain_alarm.py contains a function `set_alert_active(state)` 
# and `send_pushover_notification(user_key, api_token, message)` as previously discussed.
initial_setting = rain_alarm.get_alert_active() 

class TestRainAlert(unittest.TestCase):
    def setUp(self):
        # Assuming you have a function to write the alert status to a file
        self.initial_setting = rain_alarm.get_alert_active() 
        print(f"Initial alert status: {self.initial_setting}")
        rain_alarm.set_alert_active(True)  # Enable the alert
        print("Alert status set to active")
        rain_alarm.load_dotenv()
        self.settings = rain_alarm.load_settings()

        # Set user key and API token from environment variables
        self.user_key = rain_alarm.os.getenv('PUSHOVER_USER_KEY')
        self.api_token = rain_alarm.os.getenv('PUSHOVER_API_TOKEN')
        self.rain_threshold = rain_alarm.settings["raining_threshold"]

    @patch('rain_alarm.send_pushover_notification')
    def test_rain_alert_triggered(self, mock_notification):
        # Set an average rain value above the threshold
        average_rain = self.rain_threshold + 1
        print(f"Average rain: {average_rain}")
        with patch.dict('os.environ', {'PUSHOVER_USER_KEY': self.user_key, 'PUSHOVER_API_TOKEN': self.api_token}):
            rain_alarm.check_rain_alert(average_rain)
            # Assert that the notification was triggered
            mock_notification.assert_called_once_with(
                self.user_key,
                self.api_token,
                f"Alert: It's raining! Rain intensity: {average_rain}"
            )

    def tearDown(self):
        rain_alarm.set_alert_active(self.initial_setting) # Restore the initial alert status

if __name__ == '__main__':
    unittest.main()
