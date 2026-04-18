import unittest
import sys
import os

# Add the parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sungrow2mqtt import parse_sungrow_data

class TestDataParsing(unittest.TestCase):
    def test_parse_sungrow_data_success(self):
        # Arrange
        # Using realistic register values for Sungrow inverter
        registers = [2300, 0, 0, 20000, 0, 5000, 0, 100, 0, 1000]
        
        # Act
        result = parse_sungrow_data(registers)
        
        # Assert
        self.assertEqual(result['voltage'], 230.0)  # 2300 / 10
        self.assertEqual(result['current'], 20.0)  # (0 * 65536 + 20000) / 1000
        self.assertEqual(result['power'], 50.0)  # (0 * 65536 + 5000) / 100
        self.assertEqual(result['energy_today'], 100)  # 0 * 65536 + 100
        self.assertEqual(result['energy_total'], 1000)  # 0 * 65536 + 1000

    def test_parse_sungrow_data_invalid_data(self):
        # Arrange
        registers = [None] * 10
        
        # Act & Assert
        result = parse_sungrow_data(registers)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()