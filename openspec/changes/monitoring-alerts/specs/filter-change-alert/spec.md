## ADDED Requirements

### Requirement: Grafana-Alert bei anstehendem Filterwechsel

Grafana SHALL bei `remaining_filter_days < 30` (sustained 12 Stunden) einen Alert auslösen. Das Feld `remaining_filter_days` wird bereits von `vallox2mqtt` publiziert und via Telegraf in InfluxDB geschrieben.

#### Scenario: Filterwechsel steht an

- **WHEN** `remaining_filter_days < 30` für mindestens 12 Stunden in InfluxDB vorliegt
- **THEN** feuert der Grafana-Alert "Filterwechsel Lüftungsanlage" mit severity=warning

#### Scenario: Filter wurde gewechselt

- **WHEN** `remaining_filter_days` wieder auf einen Wert ≥ 30 zurückgeht (nach Filterwechsel und Rücksetzen in der Anlage)
- **THEN** sendet Grafana eine Resolved-Benachrichtigung

#### Scenario: Keine Daten (Anlage offline)

- **WHEN** keine Daten für `remaining_filter_days` in InfluxDB vorliegen
- **THEN** bleibt der Alert im Zustand `NoData` (kein false-positive Alert)
