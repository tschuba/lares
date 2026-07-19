## Why

Das Panel „Aktueller Status" im Ventilations-Dashboard zeigt alle Werte als horizontale Vollbreite-Zeilen — Label links, Zahl rechts, kein visueller Kontext. Farb-Thresholds allein erfordern, dass man sich merkt welche Farbe welche Bedeutung hat; das Panel ist im Alltag kaum auf einen Blick ablesbar.

## What Changes

- **Layout**: `orientation: "horizontal"` → `"auto"` (Kachel-Grid statt Zeilen)
- **Luftfeuchtigkeit**: Stat → Bar Gauge (`displayMode: "lcd"`, min=0, max=100) mit farbigen Komfort-Zonen und Value Mappings für Zonentext (Zu trocken / Trocken / Komfort / Feucht / Zu feucht)
- **CO₂**: bleibt Stat, Thresholds verfeinern (grün / gelb / orange / rot)
- **Lüfterstufe**: bleibt Stat mit Zahlenwert
- **Filter (Tage)**: Unit-Fix — zeigt derzeit „23.1 weeks" statt Tage
- **Δ Außenluft−Innenluft**: bleibt Stat, keine Änderung

## Capabilities

### New Capabilities

- `lueftung-status-panel`: Selbsterklärendes Status-Panel für die Lüftungsanlage — Luftfeuchtigkeit mit sichtbaren Komfort-Zonen, CO₂ mit Warnstufen, einheitliches Kachel-Layout

### Modified Capabilities

*(keine bestehenden Specs betroffen)*

## Impact

- `config/grafana/dashboards/ventilation.json`: Panel „Aktueller Status" (id=1) — Panel-Typ-Änderung für Luftfeuchtigkeit, Layout-Option, Threshold- und Unit-Anpassungen
- Kein Bridge-Code, keine neuen MQTT-Topics, keine neuen Queries
