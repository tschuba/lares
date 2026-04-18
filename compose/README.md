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

---

# Phase 3: Vallox Custom Bridge

## Voraussetzungen

- Phase 1 muss vollständig abgeschlossen sein
- Phase 2 sollte abgeschlossen sein (für Mosquitto)
- Vallox IP-Adresse in config/.env definiert sein (VALLOX_IP)
- MQTT-Verbindungsdaten konfiguriert sein

## Setup-Anleitung

### 1. Vallox API analysieren

**Hinweis**: Diese Phase erfordert Zugriff auf das echte Vallox-Gerät.

```bash
# Vallox API-Endpunkte testen
curl http://<VALLOX_IP>:18080/api/v1/data
curl http://<VALLOX_IP>:18080/api/v1/info

# API-Response dokumentieren und an vallox2mqtt.py anpassen falls nötig
```

### 2. Vallox2MQTT部署

```bash
# Verzeichnisse erstellen
mkdir -p logs/vallox2mqtt

# Bridge bauen und starten
docker compose -f compose/vallox2mqtt.yml up -d --build

# Verifizieren
docker ps | grep vallox2mqtt
docker logs lares-vallox2mqtt

# MQTT-Topics prüfen
docker run --rm --network lares eclipse-mosquitto:2.0 mosquitto_sub -h lares-mosquitto -t "ventilation/vallox/#" -u $MQTT_USERNAME -P $MQTT_PASSWORD -v
```

### 3. Unit Tests ausführen

```bash
# In vallox Bridge-Verzeichnis wechseln
cd bridges/vallox

# Abhängigkeiten installieren (lokal für Tests)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Tests ausführen
chmod +x tests/run_tests.sh
./tests/run_tests.sh
```

### 4. Home Assistant Integration

1. MQTT-Sensoren für Vallox-Daten erstellen:
   - ventilation/vallox/fan_speed
   - ventilation/vallox/temperature_supply_air
   - ventilation/vallox/temperature_exhaust_air
   - ventilation/vallox/humidity
   - ventilation/vallox/co2_level

2. HA-Configuration.yaml oder UI-Konfiguration verwenden

## Abnahmekriterien

- [ ] vallox2mqtt Bridge läuft als Container
- [ ] Vallox-Daten werden im MQTT publiziert
- [ ] Home Assistant zeigt Lüftungsdaten an
- [ ] Unit-Tests bestehen

## Fehlersuche

### Vallox API Probleme
- Logs prüfen: `docker logs lares-vallox2mqtt`
- Vallox IP in config/.env prüfen
- API-Endpunkte manuell testen: `curl http://<VALLOX_IP>:18080/api/v1/data`
- API-Response-Struktur prüfen und ggf. parse_vallox_data() anpassen

### MQTT-Verbindungsprobleme
- Mosquitto läuft: `docker ps | grep mosquitto`
- Username/Password prüfen
- Netzwerk-Verbindung: `docker network inspect lares`

### Unit-Test-Probleme
- Python-Abhängigkeiten installieren
- Import-Pfade prüfen
- Mock-Setup in Tests prüfen

## Nächster Schritt

Wenn Phase 3 abgeschlossen ist, mit **Phase 4: Weitere Bridges** fortfahren.

---

# Phase 4: Weitere Bridges

## Voraussetzungen

- Phase 1 muss vollständig abgeschlossen sein
- IP-Adressen in config/.env definiert sein (NOVELAN_IP, ECOWITT_PUSH_TARGET, Wetterdienste)

## Setup-Anleitung

### 1. Luxtronik2MQTT部署

```bash
docker compose -f compose/luxtronik2mqtt.yml up -d --build
docker ps | grep luxtronik2mqtt
docker logs lares-luxtronik2mqtt
```

### 2. Ecowitt2MQTT部署

```bash
docker compose -f compose/ecowitt2mqtt.yml up -d
docker ps | grep ecowitt2mqtt
docker logs lares-ecowitt2mqtt
```

### 3. WeeWX部署

```bash
docker compose -f compose/weewx.yml up -d
docker ps | grep weewx
docker logs lares-weewx
```

## Abnahmekriterien

- [ ] Novelan-Daten im MQTT und HA sichtbar
- [ ] Wetterdaten im MQTT und HA sichtbar
- [ ] WeeWX lädt Daten an externe Dienste hoch

## Nächster Schritt

Wenn Phase 4 abgeschlossen ist, mit **Phase 5: Lokale Integrationen** fortfahren.

---

# Phase 5: Lokale Integrationen

## Voraussetzungen

- Phasen 1-4 müssen vollständig abgeschlossen sein
- Home Assistant läuft bereits via Coolify
- Geräte sind im LAN erreichbar und konfiguriert

## Setup-Anleitung

### 5.1 BambuLab P1S Integration

**Hinweis**: BambuLab P1S wird direkt über HA Bambu-Integration eingebunden.

1. In HA Settings → Devices & Services → Add Integration → "Bambu Lab"
2. IP-Adresse des Druckers eingeben (oder automatisch discovern)
3. Access Code aus Bambu Studio/Orca Slicer kopieren
4. Verbinden und Testen

**Verifizierung**:
- Druckerstatus in HA sichtbar (online/offline, printing, etc.)
- Temperaturwerte verfügbar
- Kamera-Bild verfügbar (falls aktiviert)

### 5.2 Meross Steckdosen (meross_lan)

**Hinweis**: 4 Meross-Steckdosen werden über die lokale `meross_lan` Integration eingebunden.

**Gerätezuordnung**:
- MSS310 (1): BambuLab P1S
- MSS310 (2): Arbeitstisch
- MSS315 (1): Waschmaschine
- MSS315 (2): Trockner

**Einrichtung**:

1. In HA Settings → Devices & Services → Add Integration → "Meross LAN"
2. Steckdosen automatisch discovern oder manuell IP-Adresse eingeben
3. Für jede Steckdose:
   - Einbindung bestätigen
   - Energiemessung aktivieren
   - Gerät benennen (z.B. "Steckdose BambuLab")
   - Bereich zuordnen (z.B. "Arbeitszimmer")

**Verifizierung**:
- Alle 4 Steckdosen in HA sichtbar
- Energiemesswerte verfügbar (Strom, Spannung, Leistung, Verbrauch)
- Schaltfunktion funktioniert

### 5.3 Blink Kameras Integration

**Hinweis**: Blink wird über Cloud-API eingebunden (ADR-009).

**Einrichtung**:

1. In HA Settings → Devices & Services → Add Integration → "Blink"
2. Blink-Benutzername und Passwort eingeben
3. 2FA-Code eingeben (falls erforderlich)
4. Sync Module und Kameras werden automatisch erkannt
5. Kameras benennen (z.B. "Blink Vorgarten", "Blink Garten")

**Verifizierung**:
- Kameras in HA sichtbar
- Live-Bilder abrufbar
- Motion-Detection-Events in HA
- Aufnahmen abrufbar

### 5.4 Alexa/Echo Geräte Integration

**Hinweis**: Alexa-Geräte werden über `alexa_media_player` Integration eingebunden.

**Einrichtung**:

1. HACS installieren (falls nicht vorhanden)
2. In HACS → Integrations → "Alexa Media Player" suchen und installieren
3. In HA Settings → Devices & Services → Add Integration → "Alexa Media Player"
4. Amazon-Benutzername und Passwort eingeben
5. 2FA-Code eingeben (falls erforderlich)
6. Echo-Geräte werden automatisch erkannt

**Verifizierung**:
- Echo Dot (2x) in HA sichtbar
- Echo Show (1x) in HA sichtbar
- Musik-Wiedergabe steuerbar
- Lautstärke steuerbar
- Alexa-Commands ausführbar

## Abnahmekriterien

- [ ] BambuLab in HA integriert
- [ ] Alle Meross-Steckdosen mit Energiemessung in HA
- [ ] Blink-Kameras in HA sichtbar
- [ ] Echo-Geräte über HA steuerbar

## Fehlersuche

### BambuLab Probleme
- Drucker im selben WLAN wie HA
- Firewall prüfen (Port 8883 für MQTT)
- Access Code korrekt aus Bambu Studio kopiert

### Meross Probleme
- Steckdosen im selben WLAN wie HA
- Cloud-Verbindung der Steckdosen deaktivieren (für reinen LAN-Modus)
- IP-Adressen statisch vergeben (DHCP-Reservation)

### Blink Probleme
- Internetverbindung prüfen
- Blink-Cloud-Status prüfen
- 2FA korrekt eingegeben

### Alexa Probleme
- Amazon-Konto korrekt
- 2FA korrekt eingegeben
- HACS korrekt installiert
- alexa_media_player Plugin aktuell

## Nächster Schritt

Wenn Phase 5 abgeschlossen ist, mit **Phase 6: InfluxDB-Integration und Grafana** fortfahren.
