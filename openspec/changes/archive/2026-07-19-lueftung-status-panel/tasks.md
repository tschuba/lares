## 1. Layout

- [x] 1.1 `orientation` im Panel „Aktueller Status" von `"horizontal"` auf `"auto"` setzen

## 2. Luftfeuchtigkeit → Bar Gauge

- [x] 2.1 Panel-Typ des `humidity`-Override auf `bargauge` umstellen (`type`-Feld im Panel, nicht nur Override)
- [x] 2.2 `options.displayMode: "lcd"` setzen
- [x] 2.3 `min: 0`, `max: 100` im `humidity`-Override setzen
- [x] 2.4 Thresholds für Luftfeuchtigkeit setzen: null→red, 30→yellow, 40→green, 60→yellow, 70→orange, 80→red
- [x] 2.5 Value Mappings für Luftfeuchtigkeit hinzufügen: 0–29→"Zu trocken", 30–39→"Trocken", 40–60→"Komfort", 61–70→"Feucht", 71–100→"Zu feucht"

## 3. Filter-Unit-Fix

- [x] 3.1 Unit im `remaining_filter_days`-Override von `"d"` auf `"none"` ändern (verhindert automatische Skalierung zu Wochen)

## 4. Verifikation

- [x] 4.1 Dashboard in Grafana laden und prüfen: Luftfeuchtigkeit zeigt Bar Gauge mit Zonennamen
- [x] 4.2 Prüfen: Filter zeigt ganzzahlige Tage, nicht Wochen
- [x] 4.3 Prüfen: Kachel-Layout (kein horizontaler Vollbreite-Modus)
