## ADDED Requirements

### Requirement: Grafana-Alert bei niedrigem Batteriestand

Grafana SHALL einen Alert auslösen wenn `battery_pct` des FRITZ!Smart Energy 250 unter 20% fällt, und eine Pushover-Notification versenden.

#### Scenario: Batteriestand unterschreitet Schwellwert

- **WHEN** `battery_pct` in InfluxDB für mindestens einen Evaluierungszeitraum (5 Minuten) unter 20% liegt
- **THEN** sendet Grafana eine Pushover-Notification mit Titel "Lares: Fritz Energy 250 – Batterie niedrig" und dem aktuellen Prozentwert

#### Scenario: Batteriestand erholt sich

- **WHEN** `battery_pct` nach einem Alert wieder auf ≥ 20% steigt
- **THEN** sendet Grafana eine Pushover-Resolve-Notification

### Requirement: Grafana-Dashboard zeigt Batteriestand als Gauge

Das Grafana-Dashboard SHALL einen Gauge-Panel für `battery_pct` anzeigen mit Farbstufen: grün (≥ 40%), gelb (20–39%), rot (< 20%).

#### Scenario: Normaler Betrieb

- **WHEN** `battery_pct` ≥ 40%
- **THEN** zeigt der Gauge grün

#### Scenario: Warnstufe

- **WHEN** `battery_pct` zwischen 20% und 39%
- **THEN** zeigt der Gauge gelb

#### Scenario: Kritisch

- **WHEN** `battery_pct` < 20%
- **THEN** zeigt der Gauge rot
