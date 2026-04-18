import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sungrow2mqtt import publish_to_mqtt

class TestMQTPublishing(unittest.TestCase):
    @patch('paho.mqtt.client.Client')
    def test_publish_to_mqtt_success(self, mock_client):
        # Arrange
        mock_publish = MagicMock()
        mock_client.return_value.publish = mock_publish
        
        # Act
        publish_to_mqtt(
            mqtt_client=mock_client(),
            topic_prefix="test/energy/sungrow",
            data={"voltage": 120.0}
        )
        
        # Assert
        mock_publish.assert_called_once_with("test/energy/sungrow/voltage", "120.0")
        mock_client.assert_called_once()

    @patch('paho.mqtt.client.Client')
    def test_publish_to_mqtt_failure(self, mock_client):
        # Arrange
        mock_client.return_value.publish.side_effect = Exception("MQTT error")
        
        # Act & Assert
        with self.assertRaises(Exception):
            publish_to_mqtt(
                mqtt_client=mock_client(),
                topic_prefix="test/energy/sungrow",
                data={"voltage": 120.0}
            )

if __name__ == '__main__':
    unittest.main()