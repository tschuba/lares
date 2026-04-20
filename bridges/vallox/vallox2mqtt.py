#!/usr/bin/env python3
"""
Vallox to MQTT Bridge
Custom bridge for Vallox ValloPlus 350 MV-E ventilation system (ADR-006)
"""

import os
import sys
import logging
import time
import json
import asyncio
from vallox_websocket_api import Vallox
from paho.mqtt import client as mqtt_client

# Configure logging
log_file = os.getenv('LOG_FILE', '/app/logs/vallox2mqtt.log')
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

try:
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging with both file and stdout handlers
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
except (OSError, IOError):
    # Fallback to stdout only if file logging fails
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

logger = logging.getLogger('vallox2mqtt')


class ValloxAPI:
    """Client for Vallox WebSocket API"""

    def __init__(self, host):
        self.host = host
        self.client = Vallox(host)

    async def get_metrics(self):
        """Fetch current metrics from Vallox unit"""
        try:
            data = await self.client.fetch_metric_data()
            return data
        except Exception as e:
            logger.error(f"Vallox WebSocket API request failed: {str(e)}")
            return None


def parse_vallox_data(metrics):
    """Parse Vallox WebSocket API metrics into ventilation data"""
    if not metrics:
        return None

    try:
        # WebSocket API returns a dictionary with metric keys like A_CYC_TEMP_EXHAUST_AIR
        return {
            'fan_speed': metrics.get('A_CYC_FAN_SPEED', 0),
            'temperature_supply_air': metrics.get('A_CYC_TEMP_SUPPLY_AIR', 0.0),
            'temperature_exhaust_air': metrics.get('A_CYC_TEMP_EXHAUST_AIR', 0.0),
            'temperature_extract_air': metrics.get('A_CYC_TEMP_EXTRACT_AIR', 0.0),
            'temperature_outdoor_air': metrics.get('A_CYC_TEMP_OUTDOOR_AIR', 0.0),
            'temperature_supply_cell_air': metrics.get('A_CYC_TEMP_SUPPLY_CELL_AIR', 0.0),
            'humidity': metrics.get('A_CYC_HUMIDITY', 0),
            'co2_level': metrics.get('A_CYC_CO2_SENSOR', 0),
            'operating_mode': str(metrics.get('A_CYC_MODE', 'unknown'))
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


async def main():
    """Main loop for vallox2mqtt bridge"""
    try:
        # Load configuration from environment
        vallox_host = os.getenv('VALLOX_HOST')
        poll_interval = int(os.getenv('POLL_INTERVAL', '30'))

        mqtt_broker = os.getenv('MQTT_BROKER', 'lares-mosquitto')
        mqtt_port = int(os.getenv('MQTT_PORT', '1883'))
        mqtt_client_id = os.getenv('MQTT_CLIENT_ID', 'vallox2mqtt')
        mqtt_username = os.getenv('MQTT_USERNAME')
        mqtt_password = os.getenv('MQTT_PASSWORD')
        mqtt_topic_prefix = os.getenv('MQTT_TOPIC_PREFIX', 'ventilation/vallox')

        if not vallox_host:
            logger.error("VALLOX_HOST environment variable not set")
            print("ERROR: VALLOX_HOST environment variable not set", file=sys.stderr)
            return

        # Initialize Vallox WebSocket API client
        vallox_api = ValloxAPI(vallox_host)
        logger.info(f"Vallox WebSocket API client initialized for {vallox_host}")

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
                metrics = await vallox_api.get_metrics()

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
                await asyncio.sleep(poll_interval)

            except KeyboardInterrupt:
                logger.info("Shutting down gracefully")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {str(e)}")
                await asyncio.sleep(poll_interval)

    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        raise
    finally:
        if 'mqtt_client' in locals():
            mqtt_client.disconnect()
            logger.info("MQTT connection closed")


if __name__ == "__main__":
    asyncio.run(main())
