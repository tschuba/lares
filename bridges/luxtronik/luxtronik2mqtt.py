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
            
            def calc(name):
                entry = lux.calculations.get(name)
                return entry.value if entry else None

            def calc_kwh(name):
                """Wert aus kWh/10-Register in kWh umrechnen."""
                v = calc(name)
                return round(v / 10.0, 1) if v is not None else None

            data = {
                # Temperaturen
                "temperature_outside": calc("ID_WEB_Temperatur_TA"),
                "temperature_hot_water": calc("ID_WEB_Temperatur_TBW"),
                "temperature_flow": calc("ID_WEB_Temperatur_TVL"),
                "temperature_return": calc("ID_WEB_Temperatur_TRL"),
                # Wärmemengen (kWh, alle 2 h vom Controller aktualisiert)
                "heat_energy_heating": calc_kwh("ID_WEB_WMZ_Heizung"),
                "heat_energy_hot_water": calc_kwh("ID_WEB_WMZ_Brauchwasser"),
                "heat_energy_total": calc_kwh("ID_WEB_WMZ_Seit"),
                # Betriebsstunden / Laufzeiten (Sekunden)
                "runtime_compressor": calc("ID_WEB_Zaehler_BetrZeitVD1"),
                "runtime_compressor_starts": calc("ID_WEB_Zaehler_BetrZeitImpVD1"),
                "runtime_heating": calc("ID_WEB_Zaehler_BetrZeitHz"),
                "runtime_hot_water": calc("ID_WEB_Zaehler_BetrZeitBW"),
                "runtime_total": calc("ID_WEB_Zaehler_BetrZeitWP"),
                # Betriebsmodus
                "operating_mode": calc("ID_WEB_WP_BZ_akt"),
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
