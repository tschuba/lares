# Konfiguration

Dieses Dokument beschreibt geräteseitige Konfigurationsschritte, die nicht über `.env` oder `docker-compose.yml` abgedeckt sind.

## Inhaltsverzeichnis

- [Ecowitt GW1201 Wetter-Gateway](#ecowitt-gw1201-wetter-gateway)
- [WeeWX Wetterdienste](#weewx-wetterdienste)

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
