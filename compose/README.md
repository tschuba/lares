# Phase 1: Infrastruktur-Grundlage

## Setup-Anleitung

### 1. Vorbereitung

```bash
# Ins Projektverzeichnis wechseln
cd /Users/thomas/Projects/lares

# Environment-Datei erstellen
cp config/.env.template config/.env
# config/.env mit echten Werten ausfüllen
```

### 2. Docker-Netzwerk erstellen

```bash
# Docker-Netzwerk erstellen
docker network create --driver bridge --subnet 172.20.0.0/16 lares

# Verifizieren
docker network ls | grep lares
```

### 3. Mosquitto MQTT Broker部署

```bash
# Verzeichnisse erstellen
mkdir -p data/mosquitto logs/mosquitto

# Mosquitto-Passwort-Datei erstellen
docker run --rm -v $(pwd)/config/mosquitto:/mosquitto/config eclipse-mosquitto:2.0 mosquitto_passwd -c /mosquitto/config/passwd $MQTT_USERNAME
# Passwort eingeben wenn prompted

# Mosquitto starten
docker compose -f compose/mosquitto.yml up -d

# Verifizieren
docker ps | grep mosquitto
docker logs lares-mosquitto
```

### 4. InfluxDB auf NAS部署

**Hinweis**: InfluxDB läuft auf dem NAS, nicht auf dem Pi. Diese Schritte sind für NAS-Deployment.

```bash
# Auf NAS: Verzeichnisse erstellen
mkdir -p data/influxdb config/influxdb

# Environment-Datei auf NAS erstellen (Werte aus config/.env übernehmen)

# InfluxDB starten
docker compose -f compose/influxdb.yml up -d

# Verifizieren
docker ps | grep influxdb
docker logs lares-influxdb

# Initialisierung verifizieren (Browser)
http://<NAS_LAN_IP>:8086
```

### 5. Verbindungen testen

```bash
# MQTT-Verbindung testen (von einem Container im lares-Netz)
docker run --rm --network lares eclipse-mosquitto:2.0 mosquitto_sub -h lares-mosquitto -t test -u $MQTT_USERNAME -P $MQTT_PASSWORD

# InfluxDB-Verbindung vom Pi testen
curl -I http://<NAS_LAN_IP>:8086/health
```

## Abnahmekriterien

- [ ] Docker-Netzwerk `lares` existiert
- [ ] Mosquitto läuft und ist im `lares`-Netz erreichbar
- [ ] InfluxDB läuft und akzeptiert Verbindungen vom Pi
- [ ] Platzhalter-Werte sind definiert oder durch echte Werte ersetzt

## Fehlersuche

### Mosquitto startet nicht
- Logs prüfen: `docker logs lares-mosquitto`
- Passwort-Datei prüfen: `config/mosquitto/passwd` muss existieren
- Netzwerk prüfen: `docker network inspect lares`

### InfluxDB startet nicht
- Logs prüfen: `docker logs lares-influxdb`
- Verzeichnis-Berechtigungen prüfen
- Environment-Variablen prüfen

### Netzwerk-Probleme
- Firewall prüfen (Ports 1883, 8086)
- IP-Adressen in config/.env prüfen
- Docker-Netzwerk-Inspektion: `docker network inspect lares`

## Nächster Schritt

Wenn Phase 1 abgeschlossen ist, mit **Phase 2: Modbus-Proxy und Sungrow-Integration** fortfahren.
