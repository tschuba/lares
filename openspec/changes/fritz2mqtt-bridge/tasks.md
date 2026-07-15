## 1. Bridge-Code

- [x] 1.1 `bridges/fritz/fritz2mqtt.py` erstellen: FritzBox-Login, Device-Discovery (capability-basiert), JSON-Payload-Aufbau, MQTT-Publish mit retain=True, Fehlerbehandlung und Retry-Loop
- [x] 1.2 `bridges/fritz/requirements.txt` erstellen: `pyfritzhome>=0.6.20`, `paho-mqtt>=2.0`
- [x] 1.3 `bridges/fritz/Dockerfile` erstellen (analog zu `bridges/luxtronik/Dockerfile`)

## 2. Infra-Integration

- [x] 2.1 Service `fritz2mqtt` in `docker-compose.yml` unter Profil `fritz` eintragen (Image `ghcr.io/tschuba/lares/fritz2mqtt`, Env-Vars: `FRITZ_HOST`, `FRITZ_USER`, `FRITZ_PASSWORD`, `MQTT_HOST`, `MQTT_USERNAME`, `MQTT_PASSWORD`)
- [x] 2.2 Env-Vars in `.env`-Template und `COOLIFY.md` dokumentieren
- [x] 2.3 CI-Job für `bridges/fritz/` in `.github/workflows/build-bridges.yml` ergänzen (path-filter `bridges/fritz/**`)

## 3. Telegraf

- [x] 3.1 MQTT-Consumer-Input in `config/telegraf/telegraf.conf` ergänzen: Topic `energy/fritz/state`, JSON-Parsing, Measurement-Name `fritz_energy`

## 4. Verifizierung

- [ ] 4.1 Bridge lokal bauen und gegen FritzBox testen: `docker build -t fritz2mqtt bridges/fritz && docker run --env-file .env fritz2mqtt`
- [ ] 4.2 MQTT-Output verifizieren: `mosquitto_sub -t energy/fritz/state` zeigt validen JSON-Blob
- [ ] 4.3 InfluxDB-Ingestion prüfen: Measurement `fritz_energy` mit Feldern `Bezug_kwh`, `Einspeisung_kwh`, `battery_pct` vorhanden

## 5. Grafana

- [x] 5.1 Pushover Contact Point in Grafana konfigurieren (API-Key + User-Key)
- [x] 5.2 Grafana-Alert-Rule anlegen: `battery_pct < 20` für 5 Minuten → Pushover
- [x] 5.3 Energie-Dashboard: Gauge-Panel für `battery_pct` (Farbstufen: rot < 20, gelb < 40, grün ≥ 40)
- [x] 5.4 Energie-Dashboard: Zeitreihen-Panel für `Bezug_kwh` und `Einspeisung_kwh` (kumulativ + optional derivative für Momentanleistung)

## 6. Dokumentation

- [x] 6.1 `docs/inventar.md`: FRITZ!Smart Energy 250 in Geräte-Inventar eintragen
- [x] 6.2 `docs/entscheidungen.md`: ADR für Fritz-Integration ergänzen (Begründung: lokale AHA-API, kein HA-Zwang, pyfritzhome)
