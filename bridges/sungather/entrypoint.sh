#!/bin/sh
# Entrypoint script for SunGather to substitute environment variables in config.yaml

CONFIG_FILE="/config/config.yaml"
TEMPLATE_FILE="/config/config.yaml.template"

# If template exists, generate config from it
if [ -f "$TEMPLATE_FILE" ]; then
    envsubst < "$TEMPLATE_FILE" > "$CONFIG_FILE"
    echo "Generated config.yaml from template"
elif [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Neither config.yaml nor config.yaml.template found"
    exit 1
fi

# Start SunGather
exec python3 /opt/sungather/SunGather/sungather.py -c /config/config.yaml
