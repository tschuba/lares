import os
import time
import json
import logging
import paho.mqtt.client as mqtt
from luxtronik import Luxtronik

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("luxtronik2mqtt")

LUXTRONIK_IP = os.getenv("NOVELAN_IP")
LUXTRONIK_PORT = int(os.getenv("NOVELAN_PORT", 8889))
MQTT_HOST = os.getenv("MQTT_HOST", "lares-mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))

def main():
    if not LUXTRONIK_IP:
        logger.error("NOVELAN_IP environment variable is required")
        return

    logger.info(f"Connecting to MQTT broker at {MQTT_HOST}:{MQTT_PORT}...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="luxtronik2mqtt")
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        logger.error(f"Failed to connect to MQTT: {e}")
        return

    logger.info(f"Connecting to Luxtronik at {LUXTRONIK_IP}:{LUXTRONIK_PORT}...")
    try:
        lux = Luxtronik(LUXTRONIK_IP, LUXTRONIK_PORT)
    except Exception as e:
        logger.error(f"Failed to connect to Luxtronik: {e}")
        return

    while True:
        try:
            logger.info("Reading data from Luxtronik...")
            lux.read()
            
            data = {
                "temperature_outside": lux.parameters.get("ID_WEB_Temperatur_TA").value if lux.parameters.get("ID_WEB_Temperatur_TA") else None,
                "temperature_hot_water": lux.parameters.get("ID_WEB_Temperatur_TBW").value if lux.parameters.get("ID_WEB_Temperatur_TBW") else None,
                "temperature_flow": lux.parameters.get("ID_WEB_Temperatur_TVL").value if lux.parameters.get("ID_WEB_Temperatur_TVL") else None,
                "temperature_return": lux.parameters.get("ID_WEB_Temperatur_TRL").value if lux.parameters.get("ID_WEB_Temperatur_TRL") else None,
            }
            
            data = {k: v for k, v in data.items() if v is not None}
            
            topic = "heating/novelan/state"
            client.publish(topic, json.dumps(data), retain=True)
            logger.info(f"Published to {topic}: {data}")

        except Exception as e:
            logger.error(f"Error reading or publishing data: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
