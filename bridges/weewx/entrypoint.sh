#!/bin/sh
# Entrypoint script for WeeWX to substitute environment variables in weewx.conf

TEMPLATE_FILE="/home/weewx/weewx.conf.template"
CONFIG_FILE="/home/weewx/weewx.conf"

# If template exists, generate config from it
if [ -f "$TEMPLATE_FILE" ]; then
    envsubst < "$TEMPLATE_FILE" > "$CONFIG_FILE"
    echo "Generated weewx.conf from template"
    # Copy to /data/weewx.conf so WeeWX uses it
    cp "$CONFIG_FILE" /data/weewx.conf
    echo "Copied weewx.conf to /data/weewx.conf"
fi

# Start WeeWX with original entrypoint (change to working directory first)
cd /home/weewx
exec ./entrypoint.sh
