# Inventar

Dieses Dokument führt alle relevanten Komponenten, Dienste, Ports und Integrationen für Lares.

## 1) Hardware-Inventar

| Komponente | Details | Funktion |
|---|---|---|
| Raspberry Pi 4 Model B Rev 1.5 | 8 GB RAM, 1 TB Storage, 192.168.178.69 | Coolify-Host, öffentliche Dienste (HA, Grafana, Traefik, Authentik) |
| Ugreen DXP2800 NAS | Intel N100 4-Core, 8 GB RAM, 192.168.178.163 | Integrationsdienste (Mosquitto, Bridges, WeeWX, Telegraf, InfluxDB) |

## 2) Geräte-Inventar

| Gerät | Typ | Prim. Protokoll | Netzpfad | Bridge/Integration |
|---|---|---|---|---|
| Sungrow SH8.0RT | PV/Hybrid-Inverter | Modbus TCP :502 | LAN via WiNet-S | `modbus-proxy` + `sungrow2mqtt` |
| Novelan LADV 9.1-1/3 | Wärmepumpe | Luxtronik2 :8889 | LAN/Ethernet | `luxtronik2mqtt` |
| Vallox ValloPlus 350 MV-E | Lüftungsanlage | HTTP API :80 | LAN/Ethernet | `vallox2mqtt` (custom, Option A) |
| Ecowitt GW1201 | Wetter-Gateway | HTTP Push -> :4004 | LAN | `ecowitt2mqtt` |
| BambuLab P1S | 3D-Drucker | lokaler MQTT-Mechanismus | WLAN | Home Assistant Bambu-Integration |
| Meross MSS310 (1) | Einzelsteckdose mit Energiemessung | lokal via `meross_lan` + `meross2mqtt` | WLAN | Home Assistant `meross_lan` (Steuerung) + `meross2mqtt` (Metriken) |
| Meross MSS310 (2) | Einzelsteckdose mit Energiemessung | lokal via `meross_lan` + `meross2mqtt` | WLAN | Home Assistant `meross_lan` (Steuerung) + `meross2mqtt` (Metriken) |
| Meross MSS315 (1) | Einzelsteckdose mit Energiemessung | lokal via `meross_lan` + `meross2mqtt` | WLAN | Home Assistant `meross_lan` (Steuerung) + `meross2mqtt` (Metriken) |
| Meross MSS315 (2) | Einzelsteckdose mit Energiemessung | lokal via `meross_lan` + `meross2mqtt` | WLAN | Home Assistant `meross_lan` (Steuerung) + `meross2mqtt` (Metriken) |
| Blink Outdoor 4 (2x) + Sync Module 2 | Kamera-System | Blink Cloud API | WLAN + Internet | Home Assistant Blink-Integration |
| Amazon Echo Dot (2x), Echo Show (1x) | Sprach-/Audio-Geräte | Alexa API | WLAN + Internet | `alexa_media_player` in HA |

Zuordnung der Meross-Steckdosen:

- MSS310 (1): BambuLab P1S
- MSS310 (2): Arbeitstisch
- MSS315 (1): Waschmaschine
- MSS315 (2): Trockner

## 3) Service-Inventar (Pi / Coolify - 192.168.178.69)

| Service | Image/Artefakt | Intern/Extern | Ports | Persistenz |
|---|---|---|---|---|
| Home Assistant | beständiger Coolify-Service | Extern via `home.schubs.net` | App-intern | bestehend |
| Grafana | `grafana/grafana` | Extern via `cockpit.schubs.net` | 3000 intern | bestehend |
| Traefik | Coolify-integriert | Reverse Proxy | 80/443 | - |
| Authentik | Coolify-integriert | SSO | App-intern | - |

## 4) Service-Inventar (NAS - 192.168.178.163)

| Service | Image/Artefakt | Intern/Extern | Ports | Persistenz |
|---|---|---|---|---|
| Mosquitto | `eclipse-mosquitto` | Intern | 1883/tcp | ja |
| modbus-proxy | `ghcr.io/tiagocoutinho/modbus-proxy` | Intern | 502/tcp | nein |
| sungrow2mqtt | `bohdan0/sungrow2mqtt` | Intern | - | nein |
| luxtronik2mqtt | Python Service | Intern | - | optional |
| vallox2mqtt | custom Python Bridge | Intern | - | optional |
| meross2mqtt | `depau/meross2mqtt` | Intern | - | optional |
| ecowitt2mqtt | `bachya/ecowitt2mqtt` | Intern | 4004/tcp (listener) | optional |
| Telegraf | `telegraf` | Intern | - | optional |
| WeeWX | `felddy/weewx` | Intern + ausgehend ins Internet | pluginabhängig | ja |
| InfluxDB 2.x | `influxdb:2` | Intern | 8086/tcp | ja |

## 5) Netzwerke

| Netzwerkname | Zweck | Teilnehmer |
|---|---|---|
| `lares` (NAS) | internes Smart-Home Integrationsnetz auf NAS | Mosquitto, Bridges, Telegraf, WeeWX, InfluxDB |
| LAN (192.168.178.0/24) | physisches Netzwerk zwischen Pi und NAS | HA, Grafana auf Pi verbinden zu Mosquitto, InfluxDB auf NAS |
| Traefik-Netz (Pi) | Reverse Proxy Routing | Traefik, Authentik, HA, Grafana |
| Standard/Coolify-Projektnetze (Pi) | segmentierte Laufzeit je Projekt | bestehende Services |

Hinweis: Home Assistant und Grafana auf Pi kommunizieren über LAN mit MQTT-Broker und InfluxDB auf NAS (ADR-014).

## 6) Subdomains und Erreichbarkeit

| Subdomain | Service | Schutz |
|---|---|---|
| `home.schubs.net` | Home Assistant | Authentik vorgeschaltet |
| `cockpit.schubs.net` | Grafana | Authentik vorgeschaltet |

Nicht öffentlich exponiert:

- Mosquitto
- modbus-proxy
- alle Bridges
- InfluxDB auf NAS

## 7) Platzhalter für Betriebswerte

Diese Werte werden vor Umsetzung mit Realwerten ersetzt:

- `PI_LAN_IP=192.168.178.69`
- `NAS_LAN_IP=192.168.178.163`
- `SUNGROW_IP=<...>`
- `NOVELAN_IP=<...>`
- `VALLOX_IP=<...>`
- `ECOWITT_PUSH_TARGET=http://192.168.178.163:4004`
- `MQTT_USERNAME=<...>`
- `MQTT_PASSWORD=<...>`
- `INFLUX_URL=http://192.168.178.163:8086`
- `INFLUX_ORG=<...>`
- `INFLUX_BUCKET=<...>`
- `INFLUX_TOKEN=<...>`
- `AWEKAS_USERNAME=<...>`
- `AWEKAS_PASSWORD=<...>`
- `WINDY_STATION_ID=<...>`
- `WINDY_API_KEY=<...>`
- `WUNDERGROUND_STATION_ID=<...>`
- `WUNDERGROUND_API_KEY=<...>`
- `CWOP_STATION_ID=<...>`
- `CWOP_PASSWORD=<...>`
- `OPENWEATHER_STATION_ID=<...>`
- `OPENWEATHER_API_KEY=<...>`

## 8) Wetterdatenfreigabe (Ecowitt)

Der GW1201 soll Wetterdaten parallel lokal und an externe Dienste liefern:

- Lokal: `ecowitt2mqtt` für MQTT/HA/Grafana
- Extern: über WeeWX an mehrere Wetterdienste

Geplante externe Dienste:

- AWEKAS (DACH-Fokus)
- Windy.com
- Weather Underground
- CWOP/APRS
- OpenWeatherMap

Hinweis: WeeWX dient als zentraler Upload-Hub, damit lokale Datennutzung und externe Veröffentlichung sauber getrennt bleiben.

## 9) Energiefluss-Visualisierung

Energieflüsse werden zweigleisig visualisiert:

- Home Assistant Energy Dashboard für operativen Überblick in `home.schubs.net`
- Grafana Sankey-Diagramm für detaillierte Flussdarstellung in `cockpit.schubs.net`

Primäre Energiequellen und -senken:

- Sungrow (PV, Batterie, Netzbezug, Einspeisung)
- Wärmepumpe (Novelan)
- Meross-Steckdosen (BambuLab P1S, Arbeitstisch, Waschmaschine, Trockner)

## 10) Cloud-Abhängigkeiten (bewusst)

| Komponente | Grund |
|---|---|
| Blink | keine vollwertige lokale API verfügbar |
| Alexa/Echo | API-basiert, internetgebunden |
| Wetterfreigabe-Dienste | externe Veröffentlichung erfordert ausgehende Internetverbindung |

Alle anderen Kernpfade sind lokal-first ausgelegt.
