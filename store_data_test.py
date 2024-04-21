# store_data_test.py
import unittest
import sqlite3
from store_data import store_sky_data, setup_database

class TestDatabaseIntegration(unittest.TestCase):
    def setUp(self):
        # Connect to an in-memory database for testing
        self.connection = sqlite3.connect(":memory:")
        self.cursor = self.connection.cursor()
        setup_database(self.connection)  # Setup database using existing function

    def tearDown(self):
        self.connection.close()

    def test_store_and_retrieve_data(self):
        # Sample data to store
        sample_data = {
            'temperature': 20.5,
            'humidity': 50,
            'dew_point': 10.0,
            'fan_status': 'ON',
            'heater_status': 'OFF',
            'cpu_temperature': 55,
            'raining': 'no',
            'light': 300,
            'sky_temperature': 15.5,
            'ambient_temperature': 20.5,
            'sqm_ir': 100,
            'sqm_full': 200,
            'sqm_visible': 150,
            'sqm_lux': 200,
            'cloud_coverage': 0.1,
            'cloud_coverage_indicator': 5,
            'brightness': 21.98744,
            'bortle': 2
        }

        # Store data using the real function
        store_sky_data(sample_data, self.connection)

        # Query the database to verify the data
        self.cursor.execute("SELECT temperature, humidity, dew_point, fan_status, heater_status FROM sky_data")
        results = self.cursor.fetchone()

        # Check if the stored data matches the input data
        expected = (sample_data['temperature'], sample_data['humidity'], sample_data['dew_point'],
                    sample_data['fan_status'], sample_data['heater_status'])
        self.assertEqual(results, expected)

if __name__ == '__main__':
    unittest.main()
