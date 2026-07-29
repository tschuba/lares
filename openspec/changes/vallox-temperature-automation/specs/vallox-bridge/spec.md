## MODIFIED Requirements

### Requirement: active_alarm_count im publizierten Datensatz

Der von `vallox2mqtt` auf `ventilation/vallox/*` publizierte Datensatz SHALL das Feld `active_alarm_count` (Integer, ≥ 0) enthalten.

#### Scenario: Feld ist im MQTT-Payload vorhanden

- **WHEN** ein regulärer Poll-Zyklus abgeschlossen wird
- **THEN** enthält der auf `ventilation/vallox/active_alarm_count` publizierte Wert die Anzahl aktiver Alarme

#### Scenario: Bestehende Felder bleiben unverändert

- **WHEN** das neue Feld hinzugefügt wird
- **THEN** bleiben alle bisherigen Felder (`fan_speed`, `co2_level`, `remaining_filter_days`, etc.) im Payload erhalten und unverändert

#### Scenario: Hitzeschutz ist Teil der einheitlichen Temperatur-Statemachine

- **WHEN** Zuluft-Temperatur > Raumluft-Temperatur
- **THEN** wechselt die einheitliche Statemachine auf AWAY (Hitzeschutz-Bedingung hat höchste Priorität) — die bisherige separate Hitzeschutz-Statemachine existiert nicht mehr als eigenständige Klasse
