# Konfiguration

Dieses Dokument beschreibt geräteseitige Konfigurationsschritte, die nicht über `.env` oder `docker-compose.yml` abgedeckt sind.

## Inhaltsverzeichnis

- [Ecowitt GW1201 Wetter-Gateway](#ecowitt-gw1201-wetter-gateway)
- [WeeWX Wetterdienste](#weewx-wetterdienste)
- [Grafana](#grafana)

## Ecowitt GW1201 Wetter-Gateway

Das Ecowitt-Gateway unterstützt verschiedene Integrationswege. Es stehen zwei Optionen zur Verfügung:

### Option A: Direktes MQTT (empfohlen für vereinfachte Architektur)

Das Ecowitt-Gerät veröffentlicht Wetterdaten direkt an den MQTT-Broker.

#### Konfiguration in Ecowitt App

In der Ecowitt App unter "Custom Weather Service":

- **Protokoll**: MQTT
- **Broker-Adresse**: `192.168.178.163`
- **Port**: `1883`
- **Username**: `${MQTT_USERNAME}` (aus `.env`)
- **Password**: `${MQTT_PASSWORD}` (aus `.env`)
- **Topic-Präfix**: `weather/ecowitt` (optional, je nach Ecowitt-Implementierung)

#### Vorteile

- Kein zusätzlicher `ecowitt2mqtt` Container erforderlich
- Geringere Latenz (direkte Verbindung)
- Weniger Komplexität in der Docker-Compose-Konfiguration

#### Nachteile

- Kein Home Assistant Auto-Discovery (manuelle MQTT-Konfiguration in HA erforderlich)
- Topic-Struktur abhängig von Ecowitt-Implementierung

#### Architektur-Anpassung

Bei dieser Option kann der `ecowitt2mqtt` Service in `docker-compose.yml` entfernt werden.

---

### Option B: HTTP Push via ecowitt2mqtt (aktuelle Architektur)

Das Ecowitt-Gerät sendet Daten per HTTP POST an den `ecowitt2mqtt` Bridge-Container, welcher diese in MQTT konvertiert.

#### Konfiguration in Ecowitt App

In der Ecowitt App unter "Custom Weather Service":

- **Protokoll**: Ecowitt (HTTP POST)
- **URL**: `http://192.168.178.163:4004`
- **Port**: 4004 (ecowitt2mqtt Container auf NAS)

#### Vorteile

- Home Assistant Auto-Discovery aktiv (`ECOWITT2MQTT_HASS_DISCOVERY=true`)
- Konsistente Topic-Struktur über ecowitt2mqtt
- Etablierte Lösung mit Community-Support

#### Nachteile

- Zusätzlicher Container erforderlich
- Höhere Latenz (HTTP → Bridge → MQTT)
- Zusätzliche Komplexität

---

### WeeWX-Integration für externe Wetterdienste

Die Ecowitt App unterstützt nur einen einzigen Custom Weather Service gleichzeitig. Daher kann das Gerät nicht direkt an sowohl ecowitt2mqtt als auch WeeWX senden.

**Empfohlener Ansatz**: WeeWX konfiguriert sich als MQTT-Consumer und liest die Wetterdaten aus dem MQTT-Broker, anstatt einen direkten Push vom Ecowitt-Gerät zu empfangen.

#### WeeWX MQTT-Extension

Die MQTT-Subscribe-Erweiterung und `gettext` für envsubst sind im custom Docker-Image (`bridges/weewx/Dockerfile`) vorgeinstalliert. Das Image basiert auf `felddy/weewx:latest` und wird automatisch gebaut. Es ist keine manuelle Installation erforderlich.

#### WeeWX als MQTT-Consumer konfigurieren

WeeWX muss so konfiguriert werden, dass es als Treiber die MQTT-Subscribe-Erweiterung verwendet und die Ecowitt-Daten aus MQTT abonniert.

**Konfiguration via Template**

Die Konfiguration erfolgt über `config/weewx/weewx.conf.template`. Ein custom entrypoint-Skript substituiert automatisch Environment-Variablen aus der `.env`-Datei mittels `envsubst`.

Die Template-Datei enthält bereits:
- `station_type = MQTTSubscribe`
- MQTT-Subscribe Konfiguration mit Broker-Verbindung
- Beispiele für Wetterdienst-Konfigurationen (auskommentiert)

**Environment-Variablen in .env definieren**

Stelle sicher, dass folgende Variablen in `.env` definiert sind (für MQTT-Verbindung):
- `MQTT_USERNAME`
- `MQTT_PASSWORD`

Für Wetterdienste (optional, siehe [WeeWX Wetterdienste](#weewx-wetterdienste)):
- `WUNDERGROUND_STATION_ID`, `WUNDERGROUND_API_KEY`
- `AWEKAS_USERNAME`, `AWEKAS_PASSWORD`, `AWEKAS_STATION_ID`
- `WINDY_STATION_ID`, `WINDY_API_KEY`
- `CWOP_STATION_ID`, `CWOP_PASSWORD`
- `OPENWEATHER_STATION_ID`, `OPENWEATHER_API_KEY`

Das entrypoint-Skript generiert beim Container-Start automatisch `weewx.conf` aus dem Template mit substituierten Werten.

**Schritt 2: WeeWX neu starten**

```bash
docker-compose restart weewx
```

**Schritt 3: Logs prüfen**

```bash
docker-compose logs -f weewx
```

Suche nach Meldungen, die zeigen, dass WeeWX erfolgreich mit MQTT verbunden ist und Daten empfängt.

Damit erhält WeeWX die Wetterdaten über MQTT und kann diese an die externen Wetterdienste weiterleiten (siehe [WeeWX Wetterdienste](#weewx-wetterdienste)).

---

### Empfehlung

Für neue Installationen wird **Option A (direktes MQTT)** empfohlen, da sie die Architektur vereinfacht. Für bestehende Installationen mit funktionierendem `ecowitt2mqtt` kann **Option B** beibehalten werden.

**Hinweis**: Bei beiden Optionen ist keine IP-Adresse des Ecowitt-Geräts in der NAS-Konfiguration erforderlich. Das Gerät ist der aktive Sender.

## WeeWX Wetterdienste

WeeWX dient als zentraler Upload-Hub für die Veröffentlichung von Wetterdaten an externe Dienste (ADR-010).

### Vorbereitung

Konten bei den gewünschten Wetterdiensten einrichten und Zugangsdaten notieren:

- AWEKAS: Username, Password, Station ID
- Windy.com: Station ID, API Key
- Weather Underground: Station ID, API Key
- CWOP/APRS: Station ID, Password
- OpenWeatherMap: Station ID, API Key

### WeeWX-Konfiguration

Die Konfiguration erfolgt über `config/weewx/weewx.conf.template`. Environment-Variablen aus `.env` werden automatisch via `envsubst` substituiert (ähnlich wie bei SunGather).

Entferne die Kommentare für die gewünschten Wetterdienste im Template und stelle sicher, dass die entsprechenden Environment-Variablen in `.env` definiert sind.

#### Platzhalter ersetzen

Die Platzhalter in der WeeWX-Konfiguration müssen durch die echten Werte ersetzt werden. Diese sind auch in `docs/inventar.md` unter "Platzhalter für Betriebswerte" dokumentiert.

### Testen

Nach der Konfiguration WeeWX neu starten:

```bash
docker-compose restart weewx
```

Logs prüfen:

```bash
docker-compose logs -f weewx
```

Erfolgreiche Uploads zeigen sich in den Logs als erfolgreiche HTTP-POST an die jeweiligen Dienste.

## Grafana

Grafana läuft auf dem Raspberry Pi via Coolify und ist unter `cockpit.schubs.net` hinter Authentik erreichbar. Es visualisiert Daten aus der zentralen InfluxDB-Instanz auf dem NAS.

### InfluxDB-Datenquelle konfigurieren

Grafana muss als Datenquelle die InfluxDB auf dem NAS einrichten.

#### Schritte

1. Grafana unter `cockpit.schubs.net` öffnen (Authentik-Login erforderlich)
2. Navigation zu **Configuration** → **Data sources** → **Add data source**
3. **InfluxDB** auswählen
4. Folgende Konfiguration eingeben:

**InfluxDB 2.x Konfiguration:**

- **Name**: `InfluxDB NAS` (oder beliebig)
- **Query Language**: Flux
- **URL**: `http://192.168.178.163:8086`
- **Organization**: `${INFLUX_ORG}` (aus `.env`)
- **Token**: `${INFLUX_TOKEN}` (aus `.env`)
- **Default Bucket**: `${INFLUX_BUCKET}` (aus `.env`)

5. **Save & Test** klicken
6. Bei Erfolg erscheint "Data source is working"

### Dashboards importieren oder erstellen

#### Energiefluss-Sankey (ADR-012)

Für die Visualisierung der Energieflüsse wird ein Sankey-Diagramm verwendet:

1. **Sankey Panel Plugin** installieren:
   - Navigation zu **Configuration** → **Plugins**
   - Nach "Sankey" suchen
   - Plugin installieren (z.B. "Sankey Panel" von netsage-sankey-panel)

2. **Dashboard erstellen**:
   - **Create** → **Dashboard**
   - **Add new panel**
   - Panel-Typ auf "Sankey" ändern
   - Flux-Query für Energieflüsse konfigurieren

**Beispiel-Query für Sungrow-Daten:**

```flux
from(bucket: "${INFLUX_BUCKET}")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "sungrow")
  |> filter(fn: (r) => r["_field"] == "pv_power" or r["_field"] == "battery_power" or r["_field"] == "grid_power")
  |> aggregateWindow(every: 1h, fn: mean)
  |> yield(name: "mean")
```

3. Sankey-Knoten und -Verbindungen entsprechend der Energieflüsse konfigurieren:
   - PV → Batterie
   - PV → Netz (Einspeisung)
   - Batterie → Haus
   - Netz → Haus (Bezug)

#### Weitere Dashboard-Ideen

- **Wetterdaten-Trends**: Temperatur, Luftfeuchtigkeit, Wind, Niederschlag aus Ecowitt-Daten
- **Wärmepumpe-Metriken**: Leistungszahlen, Laufzeiten aus Novelan/Luxtronik-Daten
- **Meross-Energieverbrauch**: Verbrauch pro Steckdose (BambuLab, Arbeitstisch, Waschmaschine, Trockner)
- **System-Status**: CPU, RAM, Disk der Integrationsdienste (via Telegraf)

### Variablen für dynamische Dashboards

Für wiederverwendbare Dashboards können Variablen definiert werden:

1. Dashboard-Einstellungen → **Variables** → **Add variable**
2. Beispiele:
   - **Gerät-Auswahl**: Listet alle MQTT-Topics oder Geräte-IDs
   - **Zeitbereich**: Schnellwahl für 1h, 24h, 7d, 30d
   - **Aggregation**: mean, max, min, sum

### Warnungen und Alerts (optional)

Grafana kann Alerts basierend auf Schwellwerten senden:

1. Panel konfigurieren → **Alert** tab
2. Bedingung definieren (z.B. Batterie-Ladestand < 20%)
3. Notification Channel einrichten (z.B. E-Mail, Webhook zu Home Assistant)

### Tipps

- **Lange Zeitreihen**: InfluxDB auf NAS ist für Langzeitspeicherung optimiert – Dashboards können Monats/Jahres-Übersichten anzeigen
- **Performance**: Aggregation in Flux-Queries verwenden (z.B. `aggregateWindow(every: 1h, fn: mean)`) für große Zeitbereiche
- **Backup**: Dashboard-JSONs exportieren und versionieren (z.B. in `config/grafana/dashboards/`)
