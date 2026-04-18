import unittest
import sys
import os

# Add the parent directory to path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sungrow2mqtt import parse_sungrow_data

class TestDataParsing(unittest.TestCase):
    def test_parse_sungrow_data_success(self):
        # Arrange
        registers = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        
        # Act
        result = parse_sungrow_data(registers)
        
        # Assert
        self.assertEqual(result['voltage'], 100.0)
        self.assertEqual(result['current'], 20.0)
        self.assertEqual(result['power'], 30.0)
        self.assertEqual(result['energy_today'], 7000)
        self.assertEqual(result['energy_total'], 10000)

    def test_parse_sungrow_data_invalid_data(self):
        # Arrange
        registers = [None] * 10
        
        # Act & Assert
        result = parse_sungrow_data(registers)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()