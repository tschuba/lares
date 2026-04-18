import unittest
from unittest.mock import patch, MagicMock
from pymodbus.client import ModbusTcpClient
import sys
import os

# Add the parent directory to path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sungrow2mqtt import read_modbus_registers

class TestModbusCommunication(unittest.TestCase):
    @patch('pymodbus.client.ModbusTcpClient')
    def test_read_modbus_registers_success(self, mock_client):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.read_holding_registers.return_value.registers = [100, 200, 300]
        mock_instance.isError.return_value = False
        mock_client.return_value = mock_instance
        
        # Act
        result = read_modbus_registers(
            host="127.0.0.1",
            port=5020,
            unit_id=1,
            slave_id=0,
            function_code=0x03,
            register_count=100
        )
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 100)
        mock_client.assert_called_once()

    @patch('pymodbus.client.ModbusTcpClient')
    def test_read_modbus_registers_failure(self, mock_client):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.read_holding_registers.side_effect = Exception("Modbus error")
        mock_client.return_value = mock_instance
        
        # Act & Assert
        with self.assertRaises(Exception):
            read_modbus_registers(
                host="127.0.0.1",
                port=5020,
                unit_id=1,
                slave_id=0,
                function_code=0x03,
                register_count=100
            )

if __name__ == '__main__':
    unittest.main()