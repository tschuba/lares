#!/bin/sh
# meross2mqtt entrypoint
#
# 1. Legt config.yml an falls nicht vorhanden
# 2. Injiziert MQTT-Settings aus Env-Variablen (Credentials nicht in config.yml speichern)
# 3. Startet Discovery wenn keine Geraete konfiguriert sind
# 4. Startet die meross2homie Bridge
set -e

CONFIG_FILE="${1:-/config/config.yml}"

# --- 1. config.yml anlegen falls nicht vorhanden ---
if [ ! -f "$CONFIG_FILE" ]; then
    echo "[entrypoint] $CONFIG_FILE nicht gefunden – lege Standardkonfiguration an."
    cat > "$CONFIG_FILE" << 'EOF'
log_level: INFO
mqtt_host: mosquitto
mqtt_port: 1883
enable_http: true
meross_prefix: /appliance
meross_sent_prefix: /appliance
meross_bridge_topic: bridge
homie_prefix: homie
meross_key: ""
devices: {}
EOF
fi

# --- 2. MQTT-Settings aus Env-Variablen injizieren ---
python3 << 'PYEOF'
import yaml, os

path = os.environ.get("_CONFIG_FILE", "/config/config.yml")
with open(path) as f:
    config = yaml.safe_load(f) or {}

overrides = {
    "mqtt_host":     os.environ.get("MQTT_HOST"),
    "mqtt_port":     int(os.environ["MQTT_PORT"]) if os.environ.get("MQTT_PORT") else None,
    "mqtt_username": os.environ.get("MQTT_USERNAME") or None,
    "mqtt_password": os.environ.get("MQTT_PASSWORD") or None,
    "enable_http":   True if os.environ.get("ENABLE_HTTP", "").lower() == "true" else
                     False if os.environ.get("ENABLE_HTTP", "").lower() == "false" else None,
    "homie_prefix":  os.environ.get("HOMIE_PREFIX") or None,
    "log_level":     os.environ.get("LOG_LEVEL") or None,
}
for key, value in overrides.items():
    if value is not None:
        config[key] = value

with open(path, "w") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
PYEOF

# --- 3. Discovery wenn keine Geraete konfiguriert ---
devices_configured() {
    python3 -c "
import yaml, sys, os
path = os.environ.get('_CONFIG_FILE', '/config/config.yml')
try:
    c = yaml.safe_load(open(path))
    sys.exit(0 if c and c.get('devices') else 1)
except Exception:
    sys.exit(1)
" 2>/dev/null
}

if ! devices_configured; then
    echo "[entrypoint] Keine Geraete konfiguriert – starte Discovery..."

    if [ -z "$MEROSS_EMAIL" ] || [ -z "$MEROSS_PASSWORD" ]; then
        echo ""
        echo "[entrypoint] FEHLER: Meross-Credentials fehlen."
        echo "  Bitte in .env ergaenzen:"
        echo "    MEROSS_EMAIL=deine@email.de"
        echo "    MEROSS_PASSWORD=deinPasswort"
        echo "  Dann neu starten:"
        echo "    docker compose restart meross2mqtt"
        echo ""
        exit 1
    fi

    meross_discover "$CONFIG_FILE"
fi

# --- 4. Bridge starten ---
echo "[entrypoint] Starte meross2homie Bridge..."
exec python3 -m meross2homie "$CONFIG_FILE"
