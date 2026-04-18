import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vallox2mqtt import ValloxAPI, parse_vallox_data


class TestValloxAPI(unittest.TestCase):
    @patch('vallox2mqtt.requests.get')
    def test_get_metrics_success(self, mock_get):
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {'fanSpeed': 2, 'supplyAirTemperature': 21.5}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        api = ValloxAPI('192.168.1.100')
        result = api.get_metrics()

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result['fanSpeed'], 2)
        mock_get.assert_called_once()

    @patch('vallox2mqtt.requests.get')
    def test_get_metrics_failure(self, mock_get):
        # Arrange
        mock_get.side_effect = Exception("Connection error")

        # Act
        api = ValloxAPI('192.168.1.100')
        result = api.get_metrics()

        # Assert
        self.assertIsNone(result)

    @patch('vallox2mqtt.requests.get')
    def test_get_system_info_success(self, mock_get):
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {'model': 'ValloPlus 350 MV-E', 'serial': '12345'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        api = ValloxAPI('192.168.1.100')
        result = api.get_system_info()

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result['model'], 'ValloPlus 350 MV-E')


class TestDataParsing(unittest.TestCase):
    def test_parse_vallox_data_success(self):
        # Arrange
        metrics = {
            'fanSpeed': 3,
            'supplyAirTemperature': 22.5,
            'exhaustAirTemperature': 20.0,
            'outdoorAirTemperature': 15.0,
            'humidity': 45,
            'co2Level': 600,
            'filterCondition': 80,
            'operatingMode': 'home'
        }

        # Act
        result = parse_vallox_data(metrics)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result['fan_speed'], 3)
        self.assertEqual(result['temperature_supply_air'], 22.5)
        self.assertEqual(result['humidity'], 45)

    def test_parse_vallox_data_empty(self):
        # Arrange
        metrics = None

        # Act
        result = parse_vallox_data(metrics)

        # Assert
        self.assertIsNone(result)

    def test_parse_vallox_data_missing_fields(self):
        # Arrange
        metrics = {'fanSpeed': 2}

        # Act
        result = parse_vallox_data(metrics)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result['fan_speed'], 2)
        self.assertEqual(result['temperature_supply_air'], 0.0)


if __name__ == '__main__':
    unittest.main()
