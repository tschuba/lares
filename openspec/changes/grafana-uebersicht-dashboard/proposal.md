## Why

Der Wechsel zwischen fünf separaten Grafana-Dashboards (Energie, Lüftung, Wetter, Heizung, System) ist umständlich und unterbricht den Arbeitsfluss. Ein zentrales Übersichts-Dashboard mit direkten Navigationsmöglichkeiten zu den Detailansichten schafft einen schnellen Einstieg ohne Kontextwechsel.

## What Changes

- Neues Grafana-Dashboard `overview.json` mit den wichtigsten Kennzahlen aller Bereiche (~10 Stat-/Gauge-Panels)
- Dashboard Links in alle 6 Dashboards (inkl. neuem Überblick) für direkten Wechsel mit erhaltenem Zeitbereich (`Keep time range`)
- `overview.json` wird als Standard-Startseite (`Home Dashboard`) in Grafana konfiguriert

## Capabilities

### New Capabilities

- `grafana-overview-dashboard`: Übersichts-Dashboard mit Kennzahlen aus allen Bereichen und Dashboard-Navigation

### Modified Capabilities

- `grafana-dashboard-links`: Alle bestehenden Dashboards erhalten Dashboard Links zur gegenseitigen Navigation

## Impact

- Neue Datei `config/grafana/dashboards/overview.json`
- Bestehende Dateien `config/grafana/dashboards/energy.json`, `heating.json`, `ventilation.json`, `weather.json`, `system.json` erhalten jeweils einen `links`-Block
- Kein Einfluss auf Datenquellen, Telegraf, InfluxDB oder MQTT-Bridges
- Grafana-Provisioning (`config/grafana/provisioning/dashboards/dashboards.yml`) lädt `overview.json` automatisch, da das Verzeichnis bereits überwacht wird
