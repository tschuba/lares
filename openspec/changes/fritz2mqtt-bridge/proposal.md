## Why

Der FRITZ!Smart Energy 250 ist bereits mit der FritzBox 7590 AX gepairt und misst bidirektional den Gesamthaushaltsstromverbrauch am digitalen Stromzähler. Die Daten sind bisher nur in der FritzBox-UI sichtbar — sie fehlen im Lares-Datenpfad (MQTT → Telegraf → InfluxDB → Grafana) und damit im Energiefluss-Dashboard (ADR-012).

## What Changes

- Neue Bridge `fritz2mqtt` unter `bridges/fritz/` (Python, pyfritzhome, Lares-Bridge-Muster)
- Pollt die FritzBox AHA-API alle 60 Sekunden und publiziert Bezug, Einspeisung und Gerätebatterie auf MQTT
- Neuer Docker-Compose-Service unter Profil `fritz` im NAS-Stack
- Neuer CI-Job in `.github/workflows/build-bridges.yml` für `bridges/fritz/`
- Neues Telegraf-Input in `config/telegraf/telegraf.conf` für Topic `energy/fritz/state`
- Grafana-Dashboard-Panel für Energiefluss-Erweiterung (Bezug + Einspeisung vom Zähler)
- Grafana-Alert: Batteriestand < 20% → Pushover-Notification
- Inventar und ADR aktualisiert

## Capabilities

### New Capabilities

- `fritz-energy-metering`: Polling der FritzBox AHA-API, Extraktion von Bezug (kWh), Einspeisung (kWh) und Batteriestand (%) des FRITZ!Smart Energy 250, Publikation als JSON-Blob auf MQTT
- `fritz-battery-alerting`: Grafana-Alert auf Batteriestand < 20% mit Pushover-Benachrichtigung

### Modified Capabilities

*(keine bestehenden Specs betroffen)*

## Impact

- **Neu**: `bridges/fritz/fritz2mqtt.py`, `bridges/fritz/Dockerfile`, `bridges/fritz/requirements.txt`
- **Geändert**: `docker-compose.yml` (neuer Service `fritz2mqtt`, Profil `fritz`)
- **Geändert**: `.github/workflows/build-bridges.yml` (neuer Job für `bridges/fritz/`)
- **Geändert**: `config/telegraf/telegraf.conf` (MQTT-Consumer für `energy/fritz/state`)
- **Geändert**: `docs/inventar.md`, `docs/entscheidungen.md` (neues Gerät + ADR)
- **Abhängigkeit**: `pyfritzhome >= 0.6.20`
- **Credentials**: FritzBox-Host, Username, Passwort als NAS-Env-Variablen
