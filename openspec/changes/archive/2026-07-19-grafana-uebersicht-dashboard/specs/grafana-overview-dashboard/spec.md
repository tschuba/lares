## ADDED Requirements

### Requirement: Übersichts-Dashboard existiert
Es SHALL ein Dashboard `overview.json` in `config/grafana/dashboards/` geben, das automatisch via Grafana-Provisioning geladen wird.

#### Scenario: Dashboard wird provisioniert
- **WHEN** Grafana startet oder die Provisioning-Config neu lädt
- **THEN** ist das Dashboard "Lares – Überblick" in der Grafana-Oberfläche verfügbar

### Requirement: Energie-Kennzahlen im Überblick
Das Übersichts-Dashboard SHALL die folgenden aktuellen Energie-Werte anzeigen: PV Erzeugung (W), Hausverbrauch (W), Netz (W, positiv = Einspeisung), Heimspeicher-Ladestand (%), Sensor Batteriestand FRITZ!Smart Energy 250 (%).

#### Scenario: Energie-Panels zeigen aktuelle Werte
- **WHEN** das Dashboard geöffnet wird
- **THEN** zeigen alle 5 Energie-Stat-Panels den letzten Messwert aus den letzten 5 Minuten

### Requirement: Lüftungs-Kennzahlen im Überblick
Das Übersichts-Dashboard SHALL CO2-Gehalt (ppm), verbleibende Filter-Tage und Wärmeeintrag (ΔT Zuluft − Innenluft, °C) anzeigen.

#### Scenario: Lüftungs-Panel zeigt aktuellen Status
- **WHEN** das Dashboard geöffnet wird
- **THEN** zeigt das Lüftungs-Stat-Panel die Werte der letzten 10 Minuten

### Requirement: Wetter-Kennzahlen im Überblick
Das Übersichts-Dashboard SHALL Außentemperatur (°C), Windgeschwindigkeit (km/h) und Windrichtung (°) anzeigen.

#### Scenario: Wetter-Panels zeigen aktuelle Werte
- **WHEN** das Dashboard geöffnet wird
- **THEN** zeigen alle 3 Wetter-Stat-Panels den letzten Messwert aus den letzten 10 Minuten
