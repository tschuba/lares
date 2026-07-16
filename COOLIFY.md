# Coolify Deployment Guide

## Overview

As of ADR-014, Lares uses a NAS-centric architecture. Coolify on the Pi (192.168.178.69) only hosts public-facing services (Home Assistant, Grafana, Traefik, Authentik). All integration services (Mosquitto, MQTT bridges, WeeWX, Telegraf, InfluxDB) run on the NAS (192.168.178.163).

## Architecture

- **Pi (192.168.178.69, Coolify host)**: Home Assistant, Grafana, Traefik, Authentik (public-facing services only)
- **NAS (192.168.178.163)**: Mosquitto, all MQTT bridges, WeeWX, Telegraf, InfluxDB (integration services)

## Quick Start

### 1. Deploy Integration Services on NAS

On the NAS, deploy `docker-compose.yml`:

```bash
# Clone or copy Lares repository to NAS
cd /path/to/lares-on-nas

# Create required directories
mkdir -p data/mosquitto logs/mosquitto
mkdir -p logs/vallox2mqtt
mkdir -p data/weewx data/influxdb
mkdir -p config/mosquitto config/influxdb config/meross2mqtt config/telegraf

# Configure environment variables in config/.env
cp config/.env.example config/.env
# Edit config/.env with your values

# Deploy with profiles (example: all services)
docker compose --profile sungrow --profile ventilation --profile heating --profile weather --profile meross up -d
```

### 2. Configure Home Assistant on Pi (Coolify)

Home Assistant is already deployed via Coolify. Update the MQTT configuration to point to the NAS:

In Home Assistant configuration (via Coolify or HA UI):
```yaml
mqtt:
  broker: 192.168.178.163
  port: 1883
  username: !secret mqtt_username
  password: !secret mqtt_password
```

### 3. Configure Grafana on Pi (Coolify)

Grafana is already deployed via Coolify. Update the InfluxDB datasource to point to the NAS:

In Grafana datasource configuration:
- URL: `http://192.168.178.163:8086`
- Organization: `lares`
- Bucket: `smart_home`
- Token: Use the InfluxDB admin token from NAS

## Environment Variables

These variables should be configured in `config/.env` on the NAS:

```bash
# MQTT Configuration
MQTT_USERNAME=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password

# Device IPs
SUNGROW_IP=192.168.178.x
NOVELAN_IP=192.168.178.x
VALLOX_IP=192.168.178.x

# InfluxDB Configuration
INFLUX_USERNAME=your_influx_username
INFLUX_PASSWORD=your_influx_password
INFLUX_ORG=lares
INFLUX_BUCKET=smart_home
INFLUX_TOKEN=your_influx_admin_token
INFLUX_HOST=192.168.178.163
INFLUX_PORT=8086

# FritzBox (fritz2mqtt)
FRITZ_HOST=192.168.178.1
FRITZ_USER=your_fritzbox_user
FRITZ_PASSWORD=your_fritzbox_password

# Pushover (Grafana Alerting)
PUSHOVER_API_KEY=your_pushover_app_api_key
PUSHOVER_USER_KEY=your_pushover_user_key

# Weather Service Credentials
AWEKAS_USERNAME=
AWEKAS_PASSWORD=
WINDY_STATION_ID=
WINDY_API_KEY=
WUNDERGROUND_STATION_ID=
WUNDERGROUND_API_KEY=
CWOP_STATION_ID=
CWOP_PASSWORD=
OPENWEATHER_STATION_ID=
OPENWEATHER_API_KEY=
```

## Service Profiles (NAS)

| Profile | Services | Description |
|--------|----------|-------------|
| (none) | mosquitto, influxdb | Core MQTT broker and database only |
| sungrow | modbus-proxy, sungrow2mqtt | Sungrow inverter integration |
| ventilation | vallox2mqtt | Vallox ventilation integration |
| heating | luxtronik2mqtt | Novelan heat pump integration |
| weather | ecowitt2mqtt, weewx | Weather station and external uploads |
| meross | meross2mqtt, telegraf | Meross energy metrics to InfluxDB (ADR-011 hybrid) |
| fritz | fritz2mqtt | FRITZ!Smart Energy 250 Zähler-Integration |

## Network Configuration

- **NAS**: All integration services use the `lares` Docker network (172.20.0.0/16) created by `docker-compose.yml`
- **Pi**: Coolify manages its own networks for Traefik/Authentik
- **Cross-host**: Home Assistant and Grafana on Pi communicate with Mosquitto and InfluxDB on NAS via LAN (192.168.178.0/24)

## Migration from Pi-Centric Deployment

If you're migrating from the old Pi-centric deployment:

1. Stop existing services on Pi (if using old compose files)
2. Remove the old network on Pi (optional): `docker network rm lares`
3. Deploy services on NAS using `docker-compose.yml`
4. Update Home Assistant MQTT configuration to point to NAS IP (192.168.178.163)
5. Update Grafana InfluxDB datasource to point to NAS IP (192.168.178.163)

## Troubleshooting

### Services not starting on NAS
- Check NAS Docker logs: `docker compose logs`
- Verify environment variables in `config/.env`
- Ensure device IPs are reachable from the NAS

### Home Assistant cannot connect to MQTT
- Verify Mosquitto is running on NAS: `ssh nas 'docker ps | grep mosquitto'`
- Test MQTT connection from Pi: `telnet 192.168.178.163 1883`
- Check firewall rules on NAS

### Grafana cannot connect to InfluxDB
- Verify InfluxDB is running on NAS: `ssh nas 'docker ps | grep influxdb'`
- Test InfluxDB connection from Pi: `curl -I http://192.168.178.163:8086/health`
- Check InfluxDB token and bucket configuration

### Network latency issues
- Pi and NAS should be on the same subnet (192.168.178.0/24)
- Verify LAN cable connections
- Check for network congestion

## Advantages of This Approach

1. **Hardware optimization**: NAS (Intel N100, 8GB RAM) handles resource-intensive integration services
2. **Simplified Coolify**: Pi only hosts public-facing services, reducing Coolify complexity
3. **Centralized data processing**: MQTT bus and time-series processing on NAS reduces cross-host traffic
4. **Clear separation**: Data plane (NAS) vs access plane (Pi)
5. **Scalability**: NAS can be upgraded independently for better performance
