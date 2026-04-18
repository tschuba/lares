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

---

# Phase 6: InfluxDB-Integration und Grafana

## Voraussetzungen

- Phasen 1-5 müssen vollständig abgeschlossen sein
- InfluxDB auf NAS läuft und ist erreichbar
- Home Assistant läuft und hat Datenquellen (Sungrow, Vallox, Novelan, Ecowitt, Meross)
- MQTT-Broker läuft und liefert Daten

## Setup-Anleitung

### 6.1 InfluxDB-Integration in Home Assistant

**Hinweis**: InfluxDB läuft auf dem NAS, nicht auf dem Pi.

**Einrichtung**:

1. In HA Settings → Devices & Services → Add Integration → "InfluxDB"
2. Verbindungstyp: "InfluxDB 2.0"
3. URL: `http://<NAS_LAN_IP>:8086`
4. Organisation: `<INFLUX_ORG>` (aus config/.env)
5. Bucket: `<INFLUX_BUCKET>` (aus config/.env)
6. Token: `<INFLUX_TOKEN>` (aus config/.env)
7. Test-Verbindung herstellen

**Sensoren konfigurieren**:

Relevante Sensoren für Zeitreihen-Aufnahme:
- Energie: Sungrow (PV, Batterie, Netzbezug, Einspeisung), Meross (4 Steckdosen)
- Wetter: Ecowitt (Temperatur, Luftfeuchtigkeit, Wind, Regen)
- Lüftung: Vallox (Temperatur, CO2, Luftfeuchtigkeit, Lüfterstufe)
- Heizung: Novelan (Verbrauchswerte, soweit verfügbar)

**Schreibintervall**:

In HA Configuration.yaml oder UI:
```yaml
influxdb:
  host: <NAS_LAN_IP>
  port: 8086
  database: <INFLUX_BUCKET>
  username: <INFLUX_USERNAME>
  password: <INFLUX_TOKEN>
  default_measurement: state
  exclude:
    domains:
      - automation
      - updater
      - sun
  include:
    entities:
      - sensor.sungrow_pv_power
      - sensor.sungrow_battery_power
      - sensor.sungrow_grid_power
      - sensor.meross_bambulab_power
      - sensor.meross_arbeitstisch_power
      - sensor.meross_waschmaschine_power
      - sensor.meross_trockner_power
      # ... weitere relevante Sensoren
```

**Verifizierung**:
- InfluxDB-Integration in HA zeigt "verbunden"
- Daten werden in InfluxDB geschrieben (InfluxDB UI prüfen)
- Query in InfluxDB UI zeigt Daten an

### 6.2 Grafana部署

**Einrichtung**:

```bash
# Verzeichnisse erstellen
mkdir -p data/grafana

# Grafana starten
docker compose -f compose/grafana.yml up -d

# Verifizieren
docker ps | grep grafana
docker logs lares-grafana
```

**Initialer Zugriff**:
- URL: `http://<PI_LAN_IP>:3000` (intern)
- Default-Login: admin / admin
- Passwort bei erstem Login ändern

**InfluxDB als DataSource konfigurieren**:

1. Configuration → Data Sources → Add data source → "InfluxDB"
2. Query Language: Flux
3. URL: `http://<NAS_LAN_IP>:8086`
4. Organisation: `<INFLUX_ORG>`
5. Token: `<INFLUX_TOKEN>`
6. Default Bucket: `<INFLUX_BUCKET>`
7. "Save & Test"

### 6.3 Dashboards erstellen

**Dashboard 1: Energie-Übersicht**

- PV-Erzeugung (Sungrow)
- Batterie-Status (Laden/Entladen)
- Netzbezug / Einspeisung
- Verbrauch: Meross-Lasten (BambuLab, Arbeitstisch, Waschmaschine, Trockner)
- Wärmepumpe (Novelan)

**Dashboard 2: Wetter-Trends**

- Temperatur (innen/außen)
- Luftfeuchtigkeit
- Windgeschwindigkeit
- Niederschlag
- Luftdruck

**Dashboard 3: Lüftungs-Status**

- Zuluft-Temperatur
- Abluft-Temperatur
- CO2-Gehalt
- Luftfeuchtigkeit
- Lüfterstufe

**Dashboard 4: Heizungs-Verbrauch**

- Wärmepumpen-Verbrauch (Novelan)
- Temperatur-Verläufe
- Betriebszeiten

### 6.4 Sankey-Diagramm (ADR-012)

**Einrichtung**:

1. In Grafana Plugins → "Sankey Panel" installieren
2. Neues Panel mit Sankey-Typ erstellen
3. Flux-Query für Energieflüsse konfigurieren

**Flux-Query Beispiel**:

```flux
from(bucket: "<INFLUX_BUCKET>")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "homeassistant")
  |> filter(fn: (r) => r["_field"] == "power")
  |> filter(fn: (r) => r["entity_id"] =~ /sungrow|meross|novelan/)
  |> aggregateWindow(every: 1h, fn: mean)
  |> yield(name: "mean")
```

**Energieflüsse konfigurieren**:
- Quellen: PV-Erzeugung
- Speicher: Batterie
- Verbraucher: Wärmepumpe, Meross-Lasten, Hausverbrauch
- Netz: Bezug/Einspeisung

**Verifizierung**:
- Sankey-Diagramm zeigt Energieflüsse
- Flussrichtungen korrekt
- Werte plausibel

### 6.5 Traefik + Authentik Konfiguration

**Hinweis**: Grafana soll über `cockpit.schubs.net` mit Authentik-Schutz erreichbar sein.

**Grafana in Traefik-Netz einbinden**:

```bash
# Grafana Compose-Datei anpassen
# Netzwerke: lares + traefik-net
docker compose -f compose/grafana.yml up -d
```

**Traefik Route konfigurieren**:

In Traefik-Konfiguration (Coolify-Umfeld):
```yaml
http:
  routers:
    grafana:
      rule: "Host(`cockpit.schubs.net`)"
      service: grafana
      entryPoints:
        - websecure
      middlewares:
        - authentik
  services:
    grafana:
      loadBalancer:
        servers:
          - url: "http://lares-grafana:3000"
```

**Authentik-Provider konfigurieren**:

1. In Authentik: Neue Application "Grafana Cockpit"
2. Provider: OAuth2 / OIDC
3. Callback URL: `https://cockpit.schubs.net/login/generic_oauth`
4. Authorization Flow: Default Authorization Flow
5. Scopes: openid, profile, email
6. Grafana als OAuth2-Client konfigurieren

**Grafana OAuth2 konfigurieren**:

In Grafana `grafana.ini` oder Environment-Variablen:
```ini
[server]
root_url = https://cockpit.schubs.net

[auth.generic_oauth]
enabled = true
name = Authentik
allow_sign_up = false
client_id = <GRAFANA_CLIENT_ID>
client_secret = <GRAFANA_CLIENT_SECRET>
scopes = openid profile email
auth_url = https://auth.schubs.net/application/o/authorize/
token_url = https://auth.schubs.net/application/o/token/
api_url = https://auth.schubs.net/application/o/userinfo/
```

**Verifizierung**:
- Grafana über `https://cockpit.schubs.net` erreichbar
- Authentik-Login erforderlich
- Nach Login: Grafana Dashboard sichtbar
- Daten aus InfluxDB geladen

## Abnahmekriterien

- [ ] HA schreibt Daten in InfluxDB
- [ ] Grafana läuft und zeigt Daten an
- [ ] Sankey-Diagramm funktioniert
- [ ] Grafana über `cockpit.schubs.net` mit Authentik erreichbar

## Fehlersuche

### InfluxDB-Verbindungsprobleme
- InfluxDB auf NAS läuft: `docker ps | grep influxdb`
- Netzwerkverbindung: `ping <NAS_LAN_IP>`
- Port erreichbar: `nc -zv <NAS_LAN_IP> 8086`
- Token/ORG/Bucket korrekt

### Grafana Probleme
- Grafana-Container läuft: `docker ps | grep grafana`
- Logs prüfen: `docker logs lares-grafana`
- DataSource-Test in Grafana UI durchführen
- InfluxDB-Query in Grafana Explorer testen

### Sankey-Probleme
- Sankey-Plugin installiert
- Flux-Query syntaktisch korrekt
- Daten in InfluxDB vorhanden
- Feld-Namen korrekt

### Traefik/Authentik Probleme
- Traefik-Logs prüfen
- Authentik-Provider konfiguriert
- Grafana OAuth2-Konfiguration korrekt
- CORS-Einstellungen prüfen

## Nächster Schritt

Wenn Phase 6 abgeschlossen ist, mit **Phase 7: Home Assistant Externe Erreichbarkeit** fortfahren.

---

# Phase 7: Home Assistant Externe Erreichbarkeit

## Voraussetzungen

- Phasen 1-6 müssen vollständig abgeschlossen sein
- Home Assistant läuft via Coolify
- Traefik und Authentik sind bereits im Coolify-Umfeld aktiv
- HA ist bereits intern funktionsfähig

## Setup-Anleitung

### 7.1 Traefik-Konfiguration für HA

**Hinweis**: Home Assistant läuft bereits via Coolify. Nur die Traefik-Route und Netzwerk-Einbindung müssen konfiguriert werden.

**HA-Container in Traefik-Netz einbinden**:

In Coolify oder Docker-Compose-Konfiguration:
```yaml
networks:
  lares:
  traefik-net:
    external: true
```

HA muss beiden Netzen zugeordnet sein:
- `lares`: für interne MQTT-Kommunikation
- `traefik-net`: für Reverse-Proxy-Zugriff

**Traefik Route konfigurieren**:

In Traefik-Konfiguration (Coolify-Umfeld oder docker-compose labels):
```yaml
http:
  routers:
    home-assistant:
      rule: "Host(`home.schubs.net`)"
      service: home-assistant
      entryPoints:
        - websecure
      middlewares:
        - authentik
      tls:
        certResolver: letsencrypt
  services:
    home-assistant:
      loadBalancer:
        servers:
          - url: "http://<HA_CONTAINER_NAME>:8123"
  middlewares:
    authentik:
      forwardAuth:
        address: "https://auth.schubs.net/outpost.goauthentik.io/auth/oauth2/verify"
        trustForwardHeader: true
```

**Alternativ über Docker Labels** (wenn HA als Docker-Container läuft):
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.home-assistant.rule=Host(`home.schubs.net`)"
  - "traefik.http.routers.home-assistant.entrypoints=websecure"
  - "traefik.http.routers.home-assistant.tls.certresolver=letsencrypt"
  - "traefik.http.routers.home-assistant.middlewares=authentik"
  - "traefik.http.services.home-assistant.loadbalancer.server.port=8123"
```

**Verifizierung**:
```bash
# HA über Traefik erreichen (ohne Authentik noch)
curl -I https://home.schubs.net
# Sollte Redirect zu Authentik oder 401/403 zeigen
```

### 7.2 Authentik-Integration

**Hinweis**: Home Assistant soll hinter Authentik laufen mit SSO.

**Authentik-Application erstellen**:

1. In Authentik: Neue Application "Home Assistant"
2. Provider: OAuth2 / OIDC
3. Authorization Flow: Default Authorization Flow (oder "OpenID Authorization Code Flow")
4. Redirect URIs:
   - `https://home.schubs.net/auth/external/callback`
5. Scopes: openid, profile, email
6. Client ID und Client Secret notieren

**Home Assistant OAuth2 konfigurieren**:

In HA `configuration.yaml`:
```yaml
homeassistant:
  auth_providers:
    - type: homeassistant
    - type: command_line
      command: /path/to/authentik_ha.py
      name: Authentik SSO
      meta: true
```

Oder über HA UI:
1. Settings → People → Add Provider → "Command Line"
2. Name: "Authentik SSO"
3. Command: `/config/authentik_ha.py`

**Authentik HA Command Provider erstellen**:

Script `/config/authentik_ha.py`:
```python
#!/usr/bin/env python3
import sys
import requests
import os

AUTHENTIK_URL = "https://auth.schubs.net"
CLIENT_ID = "<HA_CLIENT_ID>"
CLIENT_SECRET = "<HA_CLIENT_SECRET>"
TOKEN_URL = f"{AUTHENTIK_URL}/application/o/token/"
USERINFO_URL = f"{AUTHENTIK_URL}/application/o/userinfo/"

def get_user_info(code):
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'https://home.schubs.net/auth/external/callback',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    resp = requests.post(TOKEN_URL, data=data)
    token = resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    user_resp = requests.get(USERINFO_URL, headers=headers)
    return user_resp.json()

if __name__ == '__main__':
    code = sys.argv[1]
    user = get_user_info(code)
    print(f"name={user.get('name', user.get('username'))}")
    print(f"id={user.get('sub')}")
```

**HA für Authentik konfigurieren**:

In HA `configuration.yaml`:
```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - <TRAEFIK_IP_OR_CIDR>
  ip_ban_enabled: true
  login_attempts_threshold: 5
```

**Authentik Link in HA UI aktivieren**:

1. Settings → Integrations → Add Integration → "Authentik" (falls verfügbar)
2. Oder manuellen Link in HA Dashboard konfigurieren

**Verifizierung**:
1. Browser öffnen: `https://home.schubs.net`
2. Sollte zu Authentik Login weiterleiten
3. Nach Login: Weiterleitung zu HA Dashboard
4. User ist in HA eingeloggt

### 7.3 Test der externen Erreichbarkeit

**Funktions-Checkliste**:
- [ ] HA über `https://home.schubs.net` erreichbar
- [ ] Authentik-Login wird angezeigt
- [ ] Nach erfolgreichem Login: HA Dashboard sichtbar
- [ ] HA-Funktionen (Steuerung, Automationen) funktionieren
- [ ] WebSocket-Verbindungen funktionieren (für Live-Updates)
- [ ] Mobile Apps können sich verbinden

**WebSocket-Konfiguration** (falls nötig):

In Traefik:
```yaml
http:
  routers:
    home-assistant:
      rule: "Host(`home.schubs.net`)"
      # ... andere Konfiguration
      # WebSocket wird automatisch durch Traefik unterstützt
```

In HA `configuration.yaml`:
```yaml
http:
  cors_allowed_origins:
    - https://home.schubs.net
```

## Abnahmekriterien

- [ ] HA über `home.schubs.net` erreichbar
- [ ] Authentik-Schutz aktiv
- [ ] SSO funktioniert
- [ ] WebSocket-Verbindungen funktionieren
- [ ] Mobile Apps können sich verbinden

## Fehlersuche

### HA nicht über Traefik erreichbar
- HA-Container läuft: `docker ps | grep homeassistant`
- HA in Traefik-Netz eingebunden: `docker network inspect traefik-net`
- Traefik-Route konfiguriert: Traefik Dashboard prüfen
- DNS-Eintrag für `home.schubs.net` vorhanden
- Firewall-Regeln prüfen (Port 443)

### Authentik-Login funktioniert nicht
- Authentik-Application konfiguriert
- Redirect URIs korrekt (exakt übereinstimmend)
- Client ID/Secret korrekt
- Authorization Flow korrekt gewählt
- Authentik-Logs prüfen

### HA-Login nach Authentik fehlschlägt
- HA Command Provider Script korrekt
- Script ausführbar: `chmod +x /config/authentik_ha.py`
- Python-Abhängigkeiten installiert
- User-Mapping korrekt (username/email)
- HA Logs prüfen

### WebSocket-Probleme
- Traefik WebSocket-Support aktiv (standardmäßig)
- HA CORS-Konfiguration korrekt
- `use_x_forwarded_for: true` in HA aktiv
- Trusted Proxies korrekt konfiguriert

### Mobile Apps können sich nicht verbinden
- Externe URL in HA konfiguriert: `https://home.schubs.net`
- SSL-Zertifikat gültig (Let's Encrypt)
- WebSocket-Verbindung funktioniert
- Authentik SSO auch für Mobile Apps konfiguriert

## Nächster Schritt

Wenn Phase 7 abgeschlossen ist, mit **Phase 8: Finalisierung und Dokumentation** fortfahren.
