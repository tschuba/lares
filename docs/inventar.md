# Inventar

Dieses Dokument führt alle relevanten Komponenten, Dienste, Ports und Integrationen für Lares.

## 1) Hardware-Inventar

| Komponente | Details | Funktion |
|---|---|---|
| Raspberry Pi 4 Model B Rev 1.5 | 8 GB RAM, 1 TB Storage | Laufzeit für Integrationen, HA, Broker, Grafana |
| Ugreen DXP2800 NAS | LAN-intern, nicht internet-erreichbar | InfluxDB-Langzeitspeicher |

## 2) Geräte-Inventar

| Gerät | Typ | Prim. Protokoll | Netzpfad | Bridge/Integration |
|---|---|---|---|---|
| Sungrow SH8.0RT | PV/Hybrid-Inverter | Modbus TCP :502 | LAN via WiNet-S | `modbus-proxy` + `sungrow2mqtt` |
| Novelan LADV 9.1-1/3 | Wärmepumpe | Luxtronik2 :8889 | LAN/Ethernet | `luxtronik2mqtt` |
| Vallox ValloPlus 350 MV-E | Lüftungsanlage | TCP API :18080 | LAN/Ethernet | `vallox2mqtt` (custom, Option A) |
| Ecowitt GW1201 | Wetter-Gateway | HTTP Push -> :4004 | LAN | `ecowitt2mqtt` |
| BambuLab P1S | 3D-Drucker | lokaler MQTT-Mechanismus | WLAN | Home Assistant Bambu-Integration |
| Meross MSS310 (1) | Einzelsteckdose mit Energiemessung | lokal via `meross_lan` | WLAN | Home Assistant `meross_lan` |
| Meross MSS310 (2) | Einzelsteckdose mit Energiemessung | lokal via `meross_lan` | WLAN | Home Assistant `meross_lan` |
| Meross MSS315 (1) | Einzelsteckdose mit Energiemessung | lokal via `meross_lan` | WLAN | Home Assistant `meross_lan` |
| Meross MSS315 (2) | Einzelsteckdose mit Energiemessung | lokal via `meross_lan` | WLAN | Home Assistant `meross_lan` |
| Blink Outdoor 4 (2x) + Sync Module 2 | Kamera-System | Blink Cloud API | WLAN + Internet | Home Assistant Blink-Integration |
| Amazon Echo Dot (2x), Echo Show (1x) | Sprach-/Audio-Geräte | Alexa API | WLAN + Internet | `alexa_media_player` in HA |

Zuordnung der Meross-Steckdosen:

- MSS310 (1): BambuLab P1S
- MSS310 (2): Arbeitstisch
- MSS315 (1): Waschmaschine
- MSS315 (2): Trockner

## 3) Service-Inventar (Pi / Coolify)

| Service | Image/Artefakt | Intern/Extern | Ports | Persistenz |
|---|---|---|---|---|
| Home Assistant | beständiger Coolify-Service | Extern via `home.schubs.net` | App-intern | bestehend |
| Mosquitto | `eclipse-mosquitto` | Intern | 1883/tcp | ja |
| modbus-proxy | `ghcr.io/tiagocoutinho/modbus-proxy` | Intern | 502/tcp | nein |
| sungrow2mqtt | `bohdan0/sungrow2mqtt` | Intern | - | nein |
| luxtronik2mqtt | Python Service | Intern | - | optional |
| vallox2mqtt | custom Python Bridge | Intern | - | optional |
| ecowitt2mqtt | `bachya/ecowitt2mqtt` | Intern | 4004/tcp (listener) | optional |
| WeeWX | `felddy/weewx` | Intern + ausgehend ins Internet | pluginabhängig | ja |
| Grafana | `grafana/grafana` | Extern via `cockpit.schubs.net` | 3000 intern | ja |

## 4) Service-Inventar (NAS)

| Service | Image | Rolle | Port |
|---|---|---|---|
| InfluxDB 2.x | `influxdb:2` | zentrale Zeitreihen-Datenbank | 8086/tcp |

## 5) Netzwerke

| Netzwerkname | Zweck | Teilnehmer |
|---|---|---|
| `lares` | internes Smart-Home Integrationsnetz | HA, Mosquitto, Bridges, Grafana |
| Traefik-Netz (bestehend) | Reverse Proxy Routing | Traefik, Authentik, externe Dienste |
| Standard/Coolify-Projektnetze | segmentierte Laufzeit je Projekt | bestehende Services |

Hinweis: Relevante Dienste werden in mehreren Netzen eingebunden, wenn erforderlich (z. B. Grafana: `lares` + Traefik-Netz).

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

- `PI_LAN_IP=<...>`
- `NAS_LAN_IP=<...>`
- `SUNGROW_IP=<...>`
- `NOVELAN_IP=<...>`
- `VALLOX_IP=<...>`
- `ECOWITT_PUSH_TARGET=http://<PI_LAN_IP>:4004`
- `MQTT_USERNAME=<...>`
- `MQTT_PASSWORD=<...>`
- `INFLUX_URL=http://<NAS_LAN_IP>:8086`
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
