#!/usr/bin/env python3
"""
Vallox to MQTT Bridge
Custom bridge for Vallox ValloPlus 350 MV-E ventilation system (ADR-006)
"""

import os
import logging
import time
import json
import requests
from paho.mqtt import client as mqtt_client

# Configure logging
log_file = os.getenv('LOG_FILE', '/app/logs/vallox2mqtt.log')
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

try:
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
except (OSError, IOError):
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger('vallox2mqtt')


class ValloxAPI:
    """Client for Vallox TCP API on port 18080"""

    def __init__(self, host, port=18080):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.timeout = 5

    def get_metrics(self):
        """Fetch current metrics from Vallox unit"""
        try:
            # Vallox API endpoint for metrics
            response = requests.get(
                f"{self.base_url}/api/v1/data",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Vallox API request failed: {str(e)}")
            return None

    def get_system_info(self):
        """Fetch system information"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/info",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Vallox system info request failed: {str(e)}")
            return None


def parse_vallox_data(metrics):
    """Parse Vallox metrics into ventilation data"""
    if not metrics:
        return None

    try:
        # Example parsing - adjust based on actual API response structure
        return {
            'fan_speed': metrics.get('fanSpeed', 0),
            'temperature_supply_air': metrics.get('supplyAirTemperature', 0.0),
            'temperature_exhaust_air': metrics.get('exhaustAirTemperature', 0.0),
            'temperature_outdoor_air': metrics.get('outdoorAirTemperature', 0.0),
            'humidity': metrics.get('humidity', 0),
            'co2_level': metrics.get('co2Level', 0),
            'filter_condition': metrics.get('filterCondition', 0),
            'operating_mode': metrics.get('operatingMode', 'unknown')
        }
    except Exception as e:
        logger.error(f"Data parsing error: {str(e)}")
        return None


def connect_mqtt(broker, port, client_id, username, password):
    """Establish MQTT connection"""
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id=client_id)
    client.username_pw_set(username, password)

    try:
        client.connect(broker, port)
        logger.info("Connected to MQTT broker")
        return client
    except Exception as e:
        logger.error(f"MQTT connection failed: {str(e)}")
        raise


def publish_to_mqtt(mqtt_client, topic_prefix, data):
    """Publish parsed data to MQTT topics"""
    for metric, value in data.items():
        topic = f"{topic_prefix}/{metric}"
        mqtt_client.publish(topic, json.dumps(value) if isinstance(value, (dict, list)) else str(value))
        logger.info(f"Published {metric}: {value} to {topic}")


def main():
    """Main loop for vallox2mqtt bridge"""
    try:
        # Load configuration from environment
        vallox_host = os.getenv('VALLOX_HOST')
        vallox_port = int(os.getenv('VALLOX_PORT', '18080'))
        poll_interval = int(os.getenv('POLL_INTERVAL', '30'))

        mqtt_broker = os.getenv('MQTT_BROKER', 'lares-mosquitto')
        mqtt_port = int(os.getenv('MQTT_PORT', '1883'))
        mqtt_client_id = os.getenv('MQTT_CLIENT_ID', 'vallox2mqtt')
        mqtt_username = os.getenv('MQTT_USERNAME')
        mqtt_password = os.getenv('MQTT_PASSWORD')
        mqtt_topic_prefix = os.getenv('MQTT_TOPIC_PREFIX', 'ventilation/vallox')

        if not vallox_host:
            logger.error("VALLOX_HOST environment variable not set")
            return

        # Initialize Vallox API client
        vallox_api = ValloxAPI(vallox_host, vallox_port)
        logger.info(f"Vallox API client initialized for {vallox_host}:{vallox_port}")

        # Connect to MQTT broker
        mqtt_client = connect_mqtt(
            broker=mqtt_broker,
            port=mqtt_port,
            client_id=mqtt_client_id,
            username=mqtt_username,
            password=mqtt_password
        )

        # Main polling loop
        logger.info("Starting main polling loop")
        while True:
            try:
                # Fetch metrics from Vallox
                metrics = vallox_api.get_metrics()

                if metrics:
                    # Parse metrics
                    data = parse_vallox_data(metrics)

                    if data:
                        # Publish to MQTT
                        publish_to_mqtt(mqtt_client, mqtt_topic_prefix, data)
                    else:
                        logger.warning("Failed to parse Vallox metrics")
                else:
                    logger.warning("Failed to fetch Vallox metrics")

                # Wait for next poll
                time.sleep(poll_interval)

            except KeyboardInterrupt:
                logger.info("Shutting down gracefully")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {str(e)}")
                time.sleep(poll_interval)

    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        raise
    finally:
        if 'mqtt_client' in locals():
            mqtt_client.disconnect()
            logger.info("MQTT connection closed")


if __name__ == "__main__":
    main()
