import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vallox2mqtt import ValloxAPI, parse_vallox_data

SAMPLE_METRICS = {
    'A_CYC_FAN_SPEED': 29,
    'A_CYC_EXTR_FAN_SPEED': 1450,
    'A_CYC_SUPP_FAN_SPEED': 1380,
    'A_CYC_TEMP_SUPPLY_AIR': 20.9,
    'A_CYC_TEMP_EXHAUST_AIR': 23.5,
    'A_CYC_TEMP_EXTRACT_AIR': 24.3,
    'A_CYC_TEMP_OUTDOOR_AIR': 19.6,
    'A_CYC_TEMP_SUPPLY_CELL_AIR': 20.4,
    'A_CYC_RH_VALUE': 45,
    'A_CYC_CO2_VALUE': 620,
    'A_CYC_MODE': 0,
    'A_CYC_REMAINING_TIME_FOR_FILTER': 180,
}


class TestValloxAPI(unittest.TestCase):
    def test_get_metrics_success(self):
        api = ValloxAPI('192.168.1.100')
        api.client = MagicMock()
        api.client.fetch_metric_data = AsyncMock(return_value=SAMPLE_METRICS)

        result = asyncio.run(api.get_metrics())

        self.assertIsNotNone(result)
        self.assertEqual(result['A_CYC_FAN_SPEED'], 29)
        api.client.fetch_metric_data.assert_called_once()

    def test_get_metrics_failure(self):
        api = ValloxAPI('192.168.1.100')
        api.client = MagicMock()
        api.client.fetch_metric_data = AsyncMock(side_effect=Exception("Connection error"))

        result = asyncio.run(api.get_metrics())

        self.assertIsNone(result)


class TestDataParsing(unittest.TestCase):
    def test_parse_vallox_data_correct_keys(self):
        result = parse_vallox_data(SAMPLE_METRICS)

        self.assertIsNotNone(result)
        self.assertEqual(result['humidity'], 45)
        self.assertEqual(result['co2_level'], 620)
        self.assertEqual(result['operating_mode'], 0)

    def test_parse_vallox_data_new_metrics(self):
        result = parse_vallox_data(SAMPLE_METRICS)

        self.assertEqual(result['extract_fan_speed'], 1450)
        self.assertEqual(result['supply_fan_speed'], 1380)
        self.assertEqual(result['remaining_filter_days'], 180)

    def test_parse_vallox_data_temperatures(self):
        result = parse_vallox_data(SAMPLE_METRICS)

        self.assertEqual(result['temperature_supply_air'], 20.9)
        self.assertEqual(result['temperature_exhaust_air'], 23.5)
        self.assertEqual(result['temperature_extract_air'], 24.3)
        self.assertEqual(result['temperature_outdoor_air'], 19.6)
        self.assertEqual(result['temperature_supply_cell_air'], 20.4)

    def test_parse_vallox_data_empty(self):
        result = parse_vallox_data(None)

        self.assertIsNone(result)

    def test_parse_vallox_data_missing_fields(self):
        result = parse_vallox_data({'A_CYC_FAN_SPEED': 2})

        self.assertIsNotNone(result)
        self.assertEqual(result['fan_speed'], 2)
        self.assertEqual(result['temperature_supply_air'], 0.0)
        self.assertEqual(result['humidity'], 0)
        self.assertEqual(result['co2_level'], 0)
        self.assertEqual(result['operating_mode'], 0)

    def test_parse_vallox_data_operating_mode_is_numeric(self):
        result = parse_vallox_data(SAMPLE_METRICS)

        self.assertIsInstance(result['operating_mode'], (int, float))


class TestAlarmCount(unittest.TestCase):
    def test_get_alarm_count_zero(self):
        api = ValloxAPI('192.168.1.100')
        api.client = MagicMock()
        api.client.get_alarms = AsyncMock(return_value=[])

        result = asyncio.run(api.get_alarm_count())

        self.assertEqual(result, 0)

    def test_get_alarm_count_n_alarms(self):
        api = ValloxAPI('192.168.1.100')
        api.client = MagicMock()
        alarm = MagicMock()
        api.client.get_alarms = AsyncMock(return_value=[alarm, alarm, alarm])

        result = asyncio.run(api.get_alarm_count())

        self.assertEqual(result, 3)
        api.client.get_alarms.assert_called_once_with(skip_solved=True)

    def test_get_alarm_count_api_failure_returns_none(self):
        api = ValloxAPI('192.168.1.100')
        api.client = MagicMock()
        api.client.get_alarms = AsyncMock(side_effect=Exception("Connection error"))

        result = asyncio.run(api.get_alarm_count())

        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
