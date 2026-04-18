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

---

# Phase 2: Modbus-Proxy und Sungrow-Integration

## Voraussetzungen

- Phase 1 muss vollständig abgeschlossen sein
- Sungrow IP-Adresse in config/.env definiert sein (SUNGROW_IP)
- MQTT-Verbindungsdaten konfiguriert sein

## Setup-Anleitung

### 1. Modbus-Proxy部署

```bash
# Modbus-Proxy starten
docker compose -f compose/modbus-proxy.yml up -d

# Verifizieren
docker ps | grep modbus-proxy
docker logs lares-modbus-proxy

# Verbindung testen
nc -zv localhost 502
```

### 2. Sungrow2MQTT部署

```bash
# Sungrow2MQTT starten (inkl. Modbus-Proxy und Mosquitto)
docker compose -f compose/sungrow2mqtt.yml up -d

# Verifizieren
docker ps | grep sungrow2mqtt
docker logs lares-sungrow2mqtt

# MQTT-Topics prüfen
docker run --rm --network lares eclipse-mosquitto:2.0 mosquitto_sub -h lares-mosquitto -t "energy/sungrow/#" -u $MQTT_USERNAME -P $MQTT_PASSWORD -v
```

### 3. Home Assistant Konfiguration

**Hinweis**: Home Assistant läuft bereits via Coolify. Nur MQTT-Integration hinzufügen.

1. In HA Settings → Devices & Services → Add Integration → MQTT
2. Broker: `lares-mosquitto` (oder PI_LAN_IP)
3. Port: 1883
4. Username/Password aus config/.env
5. Test-Verbindung herstellen

**Sungrow-Entities konfigurieren:**
- MQTT-Sensor für energy/sungrow/voltage
- MQTT-Sensor für energy/sungrow/current
- MQTT-Sensor für energy/sungrow/power
- MQTT-Sensor für energy/sungrow/energy_today
- MQTT-Sensor für energy/sungrow/energy_total

**Energy Dashboard:**
- Settings → Energy → Add Device
- Sungrow-Entities hinzufügen
- Konfiguration speichern

## Abnahmekriterien

- [ ] modbus-proxy läuft und ist erreichbar
- [ ] sungrow2mqtt publiziert Daten im MQTT
- [ ] Home Assistant zeigt Sungrow-Daten an
- [ ] Energieflüsse im HA Energy Dashboard sichtbar

## Fehlersuche

### Modbus-Proxy Probleme
- Logs prüfen: `docker logs lares-modbus-proxy`
- Sungrow IP in config/.env prüfen
- Netzwerkverbindung zum Sungrow prüfen: `ping $SUNGROW_IP`

### Sungrow2MQTT Probleme
- Logs prüfen: `docker logs lares-sungrow2mqtt`
- MQTT-Verbindung prüfen
- Modbus-Proxy erreichbar: `docker exec lares-sungrow2mqtt nc -zv lares-modbus-proxy 502`

### HA MQTT-Integration Probleme
- MQTT-Broker erreichbar: `docker logs lares-mosquitto`
- Username/Password prüfen
- HA-Logs prüfen

## Nächster Schritt

Wenn Phase 2 abgeschlossen ist, mit **Phase 3: Vallox Custom Bridge** fortfahren.
