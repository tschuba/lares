#!/bin/sh
# meross2mqtt entrypoint
#
# 1. Legt config.yml an falls nicht vorhanden
# 2. Injiziert MQTT- und Meross-Cloud-Settings aus Env-Variablen
# 3. Startet die meross2homie Bridge
set -e

CONFIG_FILE="${1:-/config/config.yml}"

# --- 1. config.yml anlegen falls nicht vorhanden ---
if [ ! -f "$CONFIG_FILE" ]; then
    echo "[entrypoint] $CONFIG_FILE nicht gefunden – lege Standardkonfiguration an."
    cat > "$CONFIG_FILE" << 'EOF'
log_level: INFO
mqtt_host: mosquitto
mqtt_port: 1883
homie_prefix: homie
meross_email: ""
meross_password: ""
devices: {}
EOF
fi

# --- 2. Settings aus Env-Variablen injizieren ---
_CONFIG_FILE="$CONFIG_FILE" python3 << 'PYEOF'
import yaml, os

path = os.environ.get("_CONFIG_FILE", "/config/config.yml")
with open(path) as f:
    config = yaml.safe_load(f) or {}

overrides = {
    "mqtt_host":       os.environ.get("MQTT_HOST") or None,
    "mqtt_port":       int(os.environ["MQTT_PORT"]) if os.environ.get("MQTT_PORT") else None,
    "mqtt_username":   os.environ.get("MQTT_USERNAME") or None,
    "mqtt_password":   os.environ.get("MQTT_PASSWORD") or None,
    "homie_prefix":    os.environ.get("HOMIE_PREFIX") or None,
    "log_level":       os.environ.get("LOG_LEVEL") or None,
    "meross_email":    os.environ.get("MEROSS_EMAIL") or None,
    "meross_password": os.environ.get("MEROSS_PASSWORD") or None,
}
for key, value in overrides.items():
    if value is not None:
        config[key] = value

with open(path, "w") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
PYEOF

# Pruefen ob Meross-Credentials gesetzt sind
_CONFIG_FILE="$CONFIG_FILE" python3 << 'PYEOF'
import yaml, os, sys

path = os.environ.get("_CONFIG_FILE", "/config/config.yml")
c = yaml.safe_load(open(path)) or {}
if not c.get("meross_email") or not c.get("meross_password"):
    print("")
    print("[entrypoint] FEHLER: Meross Cloud Credentials fehlen.")
    print("  Bitte in .env ergaenzen:")
    print("    MEROSS_EMAIL=deine@email.de")
    print("    MEROSS_PASSWORD=deinPasswort")
    print("  Dann neu starten:")
    print("    docker compose restart meross2mqtt")
    print("")
    sys.exit(1)
PYEOF

# --- 3. Bridge starten ---
echo "[entrypoint] Starte meross2homie Bridge..."
exec python3 -m meross2homie "$CONFIG_FILE"
