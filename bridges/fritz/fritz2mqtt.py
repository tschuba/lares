import json
import logging
import os
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from pyfritzhome import Fritzhome
from pyfritzhome.errors import LoginError

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fritz2mqtt")

FRITZ_HOST = os.getenv("FRITZ_HOST", "fritz.box")
FRITZ_USER = os.getenv("FRITZ_USER")
FRITZ_PASSWORD = os.getenv("FRITZ_PASSWORD")
MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USERNAME")
MQTT_PASS = os.getenv("MQTT_PASSWORD")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))
TOPIC = "energy/fritz/state"
PRODUCTNAME_PREFIX = "FRITZ!Smart Energy 250"


def poll(fritz: Fritzhome) -> dict | None:
    fritz.update_devices()
    devices = fritz.get_devices()

    energy_devices = [d for d in devices if d.productname.startswith(PRODUCTNAME_PREFIX)]
    if not energy_devices:
        logger.warning("No FRITZ!Smart Energy 250 devices found")
        return None

    physical = next((d for d in energy_devices if d.battery_level is not None), None)
    powermeters = [d for d in energy_devices if d.has_powermeter]

    if not physical:
        logger.warning("Physical Energy 250 device not found (no battery_level)")
    if len(powermeters) < 2:
        logger.warning("Expected 2 powermeter entities, found %d", len(powermeters))

    payload: dict = {"last_updated": datetime.now(timezone.utc).isoformat()}

    if physical:
        payload["battery_pct"] = physical.battery_level
        payload["battery_low"] = physical.battery_low

    for pm in powermeters:
        if pm.energy is not None:
            # ponytail: AHA API returns Wh as int; round to 3dp for kWh
            payload[pm.name] = round(pm.energy / 1000, 3)

    return payload


def main() -> None:
    if not FRITZ_USER or not FRITZ_PASSWORD:
        logger.error("FRITZ_USER and FRITZ_PASSWORD are required")
        return

    logger.info("Connecting to MQTT broker at %s:%d", MQTT_HOST, MQTT_PORT)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="fritz2mqtt")
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        logger.error("Failed to connect to MQTT: %s", e)
        return

    logger.info("Connecting to FritzBox at %s", FRITZ_HOST)
    fritz = Fritzhome(FRITZ_HOST, FRITZ_USER, FRITZ_PASSWORD, ssl_verify=False)
    try:
        fritz.login()
    except Exception as e:
        logger.error("FritzBox login failed: %s", e)
        client.loop_stop()
        return

    logger.info("Starting poll loop (interval=%ds)", POLL_INTERVAL)
    while True:
        try:
            payload = poll(fritz)
            if payload:
                client.publish(TOPIC, json.dumps(payload), retain=True)
                logger.info("Published to %s: %s", TOPIC, payload)
        except LoginError:
            logger.error("FritzBox auth error – check FRITZ_USER/FRITZ_PASSWORD. Stopping to avoid account lockout.")
            break
        except Exception as e:
            logger.error("Poll error: %s – attempting re-login", e)
            try:
                fritz.login()
            except LoginError:
                logger.error("Re-login failed with auth error. Stopping to avoid account lockout.")
                break
            except Exception as re_err:
                logger.error("Re-login failed: %s", re_err)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
