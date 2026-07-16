## ADDED Requirements

### Requirement: Bridge pollt FritzBox AHA-API und publiziert Energiedaten

Die Bridge fritz2mqtt SHALL alle 60 Sekunden die FritzBox AHA-API abfragen und die Energiedaten des FRITZ!Smart Energy 250 als JSON-Blob auf dem MQTT-Topic `energy/fritz/state` mit `retain=True` publizieren.

Der Payload SHALL folgende Felder enthalten (soweit von der API geliefert):
- `battery_pct` (int): Batteriestand des physischen Sensors in Prozent
- `battery_low` (bool): AVM-Battery-Low-Flag
- `last_updated` (ISO-8601-String): Zeitstempel des letzten erfolgreichen Polls
- Pro Powermeter-Entity ein Schlüssel nach dem in der FritzBox konfigurierten Namen (z.B. `Bezug`, `Einspeisung`) mit dem kumulativen Zählerstand in kWh (float, 3 Dezimalstellen)

#### Scenario: Normaler Poll-Zyklus

- **WHEN** die Bridge einen Poll-Zyklus ausführt und alle drei Entities (physisches Gerät + 2 Powermeter) erreichbar sind
- **THEN** publiziert die Bridge einen JSON-Blob mit `battery_pct`, `battery_low`, beiden kWh-Werten und `last_updated` auf `energy/fritz/state`

#### Scenario: FritzBox nicht erreichbar

- **WHEN** die FritzBox während eines Poll-Zyklus nicht erreichbar ist oder der Login fehlschlägt
- **THEN** loggt die Bridge einen ERROR und überspringt den Publish; beim nächsten Zyklus wird erneut versucht; der zuletzt publizierte retained-Wert bleibt auf dem Broker erhalten

#### Scenario: Physisches Gerät nicht gefunden

- **WHEN** kein Device mit `productname` starting with "FRITZ!Smart Energy 250" und gesetztem `battery_level` gefunden wird
- **THEN** loggt die Bridge eine WARNING; Powermeter-Entities werden dennoch publiziert falls vorhanden

### Requirement: Entity-Erkennung ist unabhängig von konfigurierten Namen

Die Bridge SHALL Entities ausschließlich über Capabilities identifizieren, nicht über konfigurierte Namen ("Bezug", "Einspeisung").

#### Scenario: Umbenannte Entities

- **WHEN** die Powermeter-Entities in der FritzBox umbenannt werden (z.B. "Verbrauch" statt "Bezug")
- **THEN** erkennt die Bridge die Entities weiterhin korrekt und verwendet die neuen Namen als JSON-Schlüssel

### Requirement: Konfiguration ausschließlich über Umgebungsvariablen

Die Bridge SHALL folgende Umgebungsvariablen auswerten:
- `FRITZ_HOST` (default: `fritz.box`)
- `FRITZ_USER` (required)
- `FRITZ_PASSWORD` (required)
- `MQTT_HOST` (default: `mosquitto`)
- `MQTT_PORT` (default: `1883`)
- `MQTT_USERNAME` (optional)
- `MQTT_PASSWORD` (optional)
- `POLL_INTERVAL` (default: `60`, Sekunden)
- `LOG_LEVEL` (default: `INFO`)

#### Scenario: Fehlende Pflichtfelder

- **WHEN** `FRITZ_USER` oder `FRITZ_PASSWORD` nicht gesetzt sind
- **THEN** beendet sich die Bridge mit einem klaren Fehlermeldung im Log
