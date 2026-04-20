#!/bin/sh
# Entrypoint script for WeeWX to substitute environment variables in weewx.conf

TEMPLATE_FILE="/home/weewx/weewx.conf.template"
CONFIG_FILE="/data/weewx.conf"

# If template exists, generate config from it
if [ -f "$TEMPLATE_FILE" ]; then
    envsubst < "$TEMPLATE_FILE" > "$CONFIG_FILE"
    echo "Generated weewx.conf from template"
fi

# Start WeeWX with original entrypoint (change to working directory first)
cd /home/weewx
exec ./entrypoint.sh
