## Why

Die Darstellung des Temperatur-Eintrags beim Lüften (Zuluft − Innenluft) ist schwer lesbar: nur eine Farbe für alle negativen Werte (kalte Zuluft), kein visueller Kontext ob die Lüftung kühlt oder heizt, und kein Bypass-Status sichtbar. Auf dem Überblick-Dashboard fehlt eine kompakte Gesamtansicht die auf einen Blick zeigt was die Lüftung gerade thermisch tut.

## What Changes

- **Ventilations-Dashboard**: Δ-Panel (`Δ Zuluft − Innenluft`) erhält symmetrische Schwellwerte (beide Richtungen gleichmäßig abgestuft) und Hintergrundfarben statt Linienfarbwechsel (`thresholdsStyle.mode: area`)
- **Bridge**: Vallox-Bridge publisht `cell_state` (Wärmerückgewinnung / Bypass / Abtauung) via MQTT
- **Überblick-Dashboard**: Neues kompaktes Stat-Panel `Lüftungs-Effekt` mit zwei Feldern: Δ Zuluft−Innenluft (mit symmetrischen Schwellen) + Wärmetauscher-Status (cell_state mit Textmapping)

## Capabilities

### New Capabilities

- `lueftungs-effekt-anzeige`: Kompakte Darstellung des thermischen Effekts der Lüftung (Δ Temperatur + Bypass-Status) im Überblick-Dashboard

### Modified Capabilities

*(keine bestehenden Specs betroffen)*

## Impact

- `bridges/vallox/vallox2mqtt.py`: +1 Zeile in `parse_vallox_data`
- `config/grafana/dashboards/ventilation.json`: Threshold-Konfiguration des Δ-Panels
- `config/grafana/dashboards/overview.json`: Neues Panel + ggf. Query für Zuluft-Delta
- CI baut Bridge-Image neu nach Push auf `main`
- Kein Breaking Change; neues MQTT-Topic `ventilation/vallox/cell_state` (additiv)
