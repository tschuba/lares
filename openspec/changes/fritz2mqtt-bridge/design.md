## Context

Der FRITZ!Smart Energy 250 ist mit der FritzBox 7590 AX (192.168.178.1) gepairt und via DECT-ULE verbunden. Die FritzBox exponiert alle Smart-Home-Geräte über die lokale AHA-HTTP-API (`/webservices/homeautoswitch.lua`). Ein Spike hat gezeigt dass das Gerät als **drei separate Entities** in der API erscheint:

- Physisches Gerät (`FRITZ!Smart Energy 250 #1`): `battery_level=10`, kein Powermeter
- `Bezug` (virtuell): `has_powermeter=True`, `energy=21244000` Wh, `power=None`
- `Einspeisung` (virtuell): `has_powermeter=True`, `energy=21895000` Wh, `power=None`

Der 250 liefert **nur kumulative kWh** (Zählerstand), keinen Momentanwert (W). `power` ist immer `None`. Momentanleistung müsste über `derivative()` in Flux berechnet werden.

Das Lares-Bridge-Muster (ADR-014): Python-Skript auf dem NAS, pollt lokale API, publiziert JSON auf Mosquitto, Telegraf konsumiert und schreibt in InfluxDB.

## Goals / Non-Goals

**Goals:**

- Kumulative Bezugs- und Einspeisungswerte (kWh) aus der FritzBox AHA-API in InfluxDB persistieren
- Batteriestand des physischen Sensors auf MQTT publizieren für Grafana-Alerting
- Nahtlose Einreihung ins bestehende Lares-Muster (Profil `fritz`, gleiches CI-Pattern)
- Grafana-Alert bei Batteriestand < 20% via Pushover

**Non-Goals:**

- Momentanleistung (W) — der 250 liefert sie nicht
- Steuerkommandos — der Sensor ist rein read-only
- Home-Assistant-Integration — bewusst ausgeschlossen
- Weitere FritzBox Smart-Home-Geräte (Thermostate, Steckdosen) — Out of scope

## Decisions

### D1: pyfritzhome als AHA-API-Bibliothek

`pyfritzhome` (v0.6.20, aktiv gewartet, intern auch von der HA fritzbox-Integration genutzt) statt direkter HTTP-Calls. Die Library abstrahiert das PBKDF2-Loginverfahren der FritzBox vollständig.

*Alternative: direktes `requests` gegen die AHA-URL* — mehr Code für das gleiche Ergebnis, kein Vorteil.

### D2: Drei Entities identifizieren ohne Namens-Hardcoding

Die Namen "Bezug" und "Einspeisung" sind in der FritzBox UI frei konfigurierbar. Die Bridge identifiziert Entities deshalb ausschließlich über Capabilities:

- Physisches Gerät: `productname.startswith("FRITZ!Smart Energy 250")` AND `battery_level is not None`
- Powermeter-Entities: `productname.startswith("FRITZ!Smart Energy 250")` AND `has_powermeter=True`

Die zwei Powermeter-Entities werden nach `energy`-Wert sortiert und als `meters[0]` / `meters[1]` behandelt — ihre `.name`-Felder werden als Schlüssel im JSON-Blob verwendet, sodass die tatsächlichen Namen im MQTT-Payload und in InfluxDB erhalten bleiben.

*Alternative: feste Namen "Bezug"/"Einspeisung" — bricht bei anderer FritzBox-Konfiguration.*

### D3: MQTT-Topic `energy/fritz/state`

Konsistent mit bestehendem Topic-Schema (`heating/novelan/state`, `ev/skoda/state`). Retain=True damit Telegraf nach Neustart sofort einen Wert hat.

### D4: Polling-Intervall 60 Sekunden

Der digitale Stromzähler aktualisiert den Zählerstand im Minutentakt. Kürzere Intervalle bringen keinen Mehrwert, längere verschlechtern die Granularität für derivative()-Berechnungen in Grafana.

### D5: Energie-Einheit: kWh (float, gerundet auf 3 Dezimalstellen)

AHA-API liefert Wh als Integer. Division durch 1000 im Bridge-Code. Konsistent mit anderen Lares-Bridges (luxtronik2mqtt arbeitet ebenfalls mit kWh).

### D6: Batteriestand-Alert in Grafana, nicht in der Bridge

Grafana Alerting mit Pushover Contact Point — kein extra Notification-Code in der Bridge. Schwellwert 20% (AVM setzt `battery_low` erst bei ~5%, zu spät für praktische Warnung).

## Risks / Trade-offs

- **FritzBox-Login schlägt fehl** → Bridge loggt Fehler und retried beim nächsten Poll-Zyklus. Kein crash. [Mitigation: exponentielles Backoff optional, zunächst simpel]
- **Entity-Erkennung findet < 2 Powermeter** (z.B. Sensor abgekoppelt) → Bridge publiziert nur was vorhanden ist, loggt Warnung. Telegraf/InfluxDB behalten letzten Wert (retain=True).
- **`power` bleibt None** → Kein Momentanwert im Dashboard. Nutzbar über `derivative(non_negative: true)` in Flux auf `energy_kwh`. Ist ein bekanntes Device-Limitation, keine Überraschung.
- **pyfritzhome kennt Energy 250 nicht in Tested-Devices** → Spike hat bestätigt dass es funktioniert. Risiko: zukünftiges FritzOS-Update ändert AHA-Schema. Mitigation: produktname-basiertes Matching ist robust gegen ABI-Änderungen.

## Migration Plan

1. Bridge lokal bauen und gegen FritzBox testen (`docker build` + manueller Run mit Env-Vars)
2. MQTT-Output verifizieren (`mosquitto_sub -t energy/fritz/state`)
3. Telegraf-Config anpassen, InfluxDB-Ingestion prüfen
4. Grafana-Panel und Alert konfigurieren
5. CI-Job aktivieren, Image zu GHCR pushen
6. NAS-Deployment: `docker compose --profile fritz up -d`

Rollback: Profil `fritz` nicht starten — kein Impact auf andere Services.
