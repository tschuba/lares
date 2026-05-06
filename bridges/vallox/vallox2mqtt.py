#!/usr/bin/env python3
"""
Vallox to MQTT Bridge
Custom bridge for Vallox ValloPlus 350 MV-E ventilation system (ADR-006)
"""

import os
import sys
import logging
import json
import asyncio
from datetime import datetime
from vallox_websocket_api import Vallox, Profile
from paho.mqtt import client as mqtt_client

# Configure logging
log_file = os.getenv('LOG_FILE', '/app/logs/vallox2mqtt.log')
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

try:
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
except (OSError, IOError):
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

logger = logging.getLogger('vallox2mqtt')

# Heat protection — opt-in via VALLOX_HEAT_PROTECTION=true
# Activates AWAY mode when supply air is warmer than indoor (extract) air for a
# sustained period, indicating ventilation is heating the house instead of cooling.
_HEAT_ENABLED = os.getenv('VALLOX_HEAT_PROTECTION', 'false').lower() == 'true'
_HEAT_TRIGGER_DELTA = float(os.getenv('HEAT_TRIGGER_DELTA', '1.0'))         # °C: supply must exceed extract by this
_HEAT_MIN_OUTDOOR = float(os.getenv('HEAT_MIN_OUTDOOR', '20.0'))            # °C: guard against acting on cold days
_HEAT_SUSTAIN_MINUTES = int(os.getenv('HEAT_SUSTAIN_MINUTES', '30'))        # min: condition must hold before acting
_HEAT_RELEASE_DELTA = float(os.getenv('HEAT_RELEASE_DELTA', '0.0'))         # °C: supply must drop to extract + this to release
_HEAT_MIN_OVERRIDE_MINUTES = int(os.getenv('HEAT_MIN_OVERRIDE_MINUTES', '60'))  # min: stay in AWAY at least this long
_HEAT_COOLDOWN_MINUTES = int(os.getenv('HEAT_COOLDOWN_MINUTES', '60'))      # min: wait before re-evaluating after restoring


class HeatProtection:
    """
    State machine: detects when ventilation is heating the house and switches
    the Vallox to AWAY profile until conditions improve.

    States:
      NORMAL       → condition appears → MONITORING
      MONITORING   → sustained long enough → OVERRIDE (activate AWAY)
                   → condition breaks → NORMAL
      OVERRIDE     → condition gone + min time elapsed → COOLING_DOWN (restore HOME)
      COOLING_DOWN → cooldown elapsed → NORMAL
    """

    NORMAL = 'normal'
    MONITORING = 'monitoring'
    OVERRIDE = 'override'
    COOLING_DOWN = 'cooling_down'

    def __init__(self):
        self.state = self.NORMAL
        self._state_since = datetime.now()

    def _minutes_in_state(self) -> float:
        return (datetime.now() - self._state_since).total_seconds() / 60

    def _transition(self, new_state: str) -> None:
        logger.info(f"Heat protection: {self.state} → {new_state}")
        self.state = new_state
        self._state_since = datetime.now()

    @property
    def override_active(self) -> bool:
        return self.state == self.OVERRIDE

    def evaluate(self, supply_temp: float, extract_temp: float, outdoor_temp: float) -> tuple:
        """
        Evaluate current temperatures against heat protection thresholds.
        Returns (should_activate, should_deactivate); at most one is True per call.
        """
        delta = supply_temp - extract_temp
        condition_met = delta > _HEAT_TRIGGER_DELTA and outdoor_temp > _HEAT_MIN_OUTDOOR

        if self.state == self.NORMAL:
            if condition_met:
                self._transition(self.MONITORING)

        elif self.state == self.MONITORING:
            if not condition_met:
                self._transition(self.NORMAL)
            elif self._minutes_in_state() >= _HEAT_SUSTAIN_MINUTES:
                self._transition(self.OVERRIDE)
                return True, False

        elif self.state == self.OVERRIDE:
            release_met = (
                delta < _HEAT_RELEASE_DELTA
                and self._minutes_in_state() >= _HEAT_MIN_OVERRIDE_MINUTES
            )
            if release_met:
                self._transition(self.COOLING_DOWN)
                return False, True

        elif self.state == self.COOLING_DOWN:
            if self._minutes_in_state() >= _HEAT_COOLDOWN_MINUTES:
                self._transition(self.NORMAL)

        return False, False


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

    async def set_profile(self, profile: Profile) -> bool:
        """Set the operating profile on the Vallox unit"""
        try:
            await self.client.set_profile(profile)
            logger.info(f"Vallox profile set to {profile.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set Vallox profile to {profile.name}: {str(e)}")
            return False


def parse_vallox_data(metrics):
    """Parse Vallox WebSocket API metrics into ventilation data"""
    if not metrics:
        return None

    try:
        return {
            'fan_speed': metrics.get('A_CYC_FAN_SPEED', 0),
            'extract_fan_speed': metrics.get('A_CYC_EXTR_FAN_SPEED', 0),
            'supply_fan_speed': metrics.get('A_CYC_SUPP_FAN_SPEED', 0),
            'temperature_supply_air': metrics.get('A_CYC_TEMP_SUPPLY_AIR', 0.0),
            'temperature_exhaust_air': metrics.get('A_CYC_TEMP_EXHAUST_AIR', 0.0),
            'temperature_extract_air': metrics.get('A_CYC_TEMP_EXTRACT_AIR', 0.0),
            'temperature_outdoor_air': metrics.get('A_CYC_TEMP_OUTDOOR_AIR', 0.0),
            'temperature_supply_cell_air': metrics.get('A_CYC_TEMP_SUPPLY_CELL_AIR', 0.0),
            'humidity': metrics.get('A_CYC_RH_VALUE', 0),
            'co2_level': metrics.get('A_CYC_CO2_VALUE', 0),
            'operating_mode': metrics.get('A_CYC_MODE', 0),
            'remaining_filter_days': metrics.get('A_CYC_REMAINING_TIME_FOR_FILTER', 0),
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

        if _HEAT_ENABLED:
            logger.info(
                f"Heat protection enabled — trigger: Δ>{_HEAT_TRIGGER_DELTA}°C outdoor>{_HEAT_MIN_OUTDOOR}°C "
                f"sustain={_HEAT_SUSTAIN_MINUTES}min override_min={_HEAT_MIN_OVERRIDE_MINUTES}min "
                f"cooldown={_HEAT_COOLDOWN_MINUTES}min"
            )

        # Connect to MQTT broker
        mqtt = connect_mqtt(
            broker=mqtt_broker,
            port=mqtt_port,
            client_id=mqtt_client_id,
            username=mqtt_username,
            password=mqtt_password
        )

        heat_protection = HeatProtection()

        # Main polling loop
        logger.info("Starting main polling loop")
        while True:
            try:
                # Fetch metrics from Vallox
                metrics = await vallox_api.get_metrics()

                if metrics:
                    data = parse_vallox_data(metrics)

                    if data:
                        if _HEAT_ENABLED:
                            supply = data['temperature_supply_air']
                            extract = data['temperature_extract_air']
                            outdoor = data['temperature_outdoor_air']
                            # A_CYC_STATE: 0 = HOME, 1 = AWAY — only act when in HOME mode
                            home_away_state = metrics.get('A_CYC_STATE', 0)

                            if home_away_state == 0:
                                activate, deactivate = heat_protection.evaluate(supply, extract, outdoor)
                            else:
                                # Unit is already in AWAY (manually set); don't interfere
                                if heat_protection.state not in (HeatProtection.OVERRIDE, HeatProtection.COOLING_DOWN):
                                    heat_protection = HeatProtection()
                                activate, deactivate = False, False

                            if activate:
                                logger.warning(
                                    f"Heat protection activating AWAY — "
                                    f"supply={supply}°C extract={extract}°C outdoor={outdoor}°C "
                                    f"Δ={supply - extract:.1f}°C"
                                )
                                await vallox_api.set_profile(Profile.AWAY)
                            elif deactivate:
                                logger.info("Heat protection deactivating — restoring HOME profile")
                                await vallox_api.set_profile(Profile.HOME)

                            data['heat_override'] = 1 if heat_protection.override_active else 0

                        publish_to_mqtt(mqtt, mqtt_topic_prefix, data)
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
        if 'mqtt' in locals():
            mqtt.disconnect()
            logger.info("MQTT connection closed")


if __name__ == "__main__":
    asyncio.run(main())
