## Requirements

### Requirement: Vallox publiziert aktive Alarmanzahl

Die Bridge SHALL bei jedem Poll-Zyklus die Anzahl aktiver (ungeklärter) Alarme via `get_alarms(skip_solved=True)` ermitteln und als `active_alarm_count` (Integer) im publizierten JSON-Blob veröffentlichen.

#### Scenario: Keine aktiven Alarme

- **WHEN** die Vallox-Anlage keine aktiven Alarme meldet
- **THEN** wird `active_alarm_count: 0` im MQTT-Payload publiziert

#### Scenario: Mindestens ein aktiver Alarm

- **WHEN** die Vallox-Anlage einen oder mehrere aktive Alarme meldet
- **THEN** wird `active_alarm_count: N` (N ≥ 1) im MQTT-Payload publiziert

#### Scenario: API-Fehler beim Alarm-Abruf

- **WHEN** der Alarm-Abruf aus der Vallox-API fehlschlägt
- **THEN** wird der Fehler geloggt und `active_alarm_count` nicht publiziert (kein Payload mit 0 als Default-Override)

### Requirement: Grafana-Alert bei aktivem Vallox-Alarm

Grafana SHALL bei `active_alarm_count > 0` (sustained 2 Minuten) einen Alert auslösen und über alle konfigurierten Contact Points (Pushover, ntfy) benachrichtigen.

#### Scenario: Alarm wird erkannt

- **WHEN** `active_alarm_count > 0` für mindestens 2 Minuten in InfluxDB vorliegt
- **THEN** feuert der Grafana-Alert "Lüftungsanlage Alarm" mit severity=critical

#### Scenario: Alarm ist behoben

- **WHEN** `active_alarm_count` auf 0 zurückkehrt
- **THEN** sendet Grafana eine Resolved-Benachrichtigung
