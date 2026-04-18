# Coolify Deployment Guide

## Overview

Lares can be deployed as a single Coolify application with all Pi-hosted services in one compose file. InfluxDB runs separately on the NAS per ADR-005.

## Architecture

- **Pi (Coolify host)**: Mosquitto, all MQTT bridges, WeeWX
- **NAS**: InfluxDB only (separate deployment)

## Quick Start

### 1. Create Coolify Application

1. In Coolify, create a new application
2. Choose "Docker Compose" as the source
3. Connect the Lares repository
4. Select `docker-compose.yml` as the compose file

### 2. Configure Environment Variables

Add these environment variables in Coolify:

```bash
# MQTT Configuration
MQTT_USERNAME=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password

# Device IPs
SUNGROW_IP=192.168.1.x
NOVELAN_IP=192.168.1.x
VALLOX_IP=192.168.1.x
ECOWITT_PUSH_TARGET=http://192.168.1.100:4004

# InfluxDB (for reference, actual deployment on NAS)
INFLUX_USERNAME=your_influx_username
INFLUX_PASSWORD=your_influx_password
INFLUX_ORG=lares
INFLUX_BUCKET=smart_home
INFLUX_TOKEN=your_influx_admin_token
INFLUX_HOST=${NAS_LAN_IP}
NAS_LAN_IP=192.168.1.200

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

### 3. Deploy with Profiles

Coolify supports Docker Compose profiles. Use the `COMPOSE_PROFILES` environment variable to select which services to deploy:

**Full deployment (all bridges):**
```bash
COMPOSE_PROFILES=sungrow,ventilation,heating,weather,meross
```

**Minimal deployment (MQTT only):**
```bash
# Leave COMPOSE_PROFILES empty
```

**Specific services only:**
```bash
COMPOSE_PROFILES=sungrow,ventilation
```

### 4. Deploy InfluxDB on NAS

On the NAS, deploy `docker-compose.nas.yml`:

```bash
# Copy docker-compose.nas.yml and config/.env to NAS
cd /path/to/lares-on-nas
docker compose -f docker-compose.nas.yml up -d
```

## Service Profiles

| Profile | Services | Description |
|--------|----------|-------------|
| (none) | mosquitto | Core MQTT broker only |
| sungrow | modbus-proxy, sungrow2mqtt | Sungrow inverter integration |
| ventilation | vallox2mqtt | Vallox ventilation integration |
| heating | luxtronik2mqtt | Novelan heat pump integration |
| weather | ecowitt2mqtt, weewx | Weather station and external uploads |
| meross | meross2mqtt, telegraf | Meross energy metrics to InfluxDB (ADR-011 hybrid) |

## Network Configuration

All services use the `lares` Docker network (172.20.0.0/16). This network is created automatically by the compose file.

## Volume Setup

Create required directories on the Pi before first deployment:

```bash
mkdir -p data/mosquitto logs/mosquitto
mkdir -p logs/vallox2mqtt
mkdir -p data/weewx
mkdir -p config/meross2mqtt
mkdir -p config/telegraf
```

Coolify will create these automatically if you configure persistent volumes in the application settings.

## Migration from Individual Compose Files

If you're currently using the individual compose files in `compose/`:

1. Stop existing services:
   ```bash
   cd /Users/thomas/Projects/lares
   docker compose -f compose/mosquitto.yml down
   docker compose -f compose/modbus-proxy.yml down
   docker compose -f compose/sungrow2mqtt.yml down
   # ... repeat for all services
   ```

2. Remove the old network (optional, will be recreated):
   ```bash
   docker network rm lares
   ```

3. Deploy via Coolify using the new `docker-compose.yml`

## Troubleshooting

### Services not starting
- Check Coolify logs for each service
- Verify environment variables are set correctly
- Ensure device IPs are reachable from the Pi

### Network issues
- Verify the `lares` network exists: `docker network ls | grep lares`
- Check service connectivity: `docker exec lares-mosquitto ping lares-sungrow2mqtt`

### InfluxDB connection
- Ensure InfluxDB is running on NAS
- Verify NAS IP is correct in environment variables
- Test connectivity: `curl -I http://<NAS_LAN_IP>:8086/health`

## Advantages of This Approach

1. **Single Coolify application**: All Pi services managed together
2. **Profile-based deployment**: Deploy only what you need
3. **Simplified updates**: One compose file to maintain
4. **Coolify-native**: Uses Coolify's environment variable and deployment features
5. **Separation of concerns**: NAS (InfluxDB) remains independent per ADR-005
