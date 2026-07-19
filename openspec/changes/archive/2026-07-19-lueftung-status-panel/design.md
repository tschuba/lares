## Context

Das Panel „Aktueller Status" (id=1) in `config/grafana/dashboards/ventilation.json` ist ein `stat`-Panel mit `colorMode: "background"` und `orientation: "horizontal"`. Es zeigt 5 Metriken als Vollbreite-Zeilen — alle Thresholds sind bereits definiert, aber ohne visuellen Kontext (nur Farbe, kein Bereich sichtbar). Luftfeuchtigkeit und CO₂ profitieren am meisten von einer besseren Darstellung.

## Goals / Non-Goals

**Goals:**
- Luftfeuchtigkeit als Bar Gauge mit sichtbaren Komfort-Zonen (keine Farbmemory nötig)
- CO₂ mit verfeinerten Warnstufen
- Layout als Kacheln statt horizontaler Zeilen
- Filter-Unit-Bug beheben

**Non-Goals:**
- Keine Änderungen an anderen Panels oder anderen Dashboards
- Kein Bridge-Code, keine neuen Queries

## Decisions

**Luftfeuchtigkeit: Bar Gauge `displayMode: "lcd"`**
`lcd` segmentiert den Balken sichtbar in Zonen — die Einteilung ist direkt ablesbar ohne dass man die Threshold-Werte kennen muss. `gradient` wäre weicher, aber weniger klar. `basic` zeigt nur die aktuelle Zone ohne Kontext. → `lcd` gewinnt.

Thresholds (absolute):
```
null (0%)  → red      (Zu trocken)
30%        → yellow
40%        → green    (Komfort-Zone)
60%        → yellow
70%        → orange
80%        → red      (Zu feucht)
```

Value Mappings (Ranges) für Zonentext:
```
0–29   → "Zu trocken"
30–39  → "Trocken"
40–60  → "Komfort"
61–70  → "Feucht"
71–100 → "Zu feucht"
```

min=0, max=100 explizit setzen (Pflicht für Bar Gauge).

**CO₂: Stat bleibt, Thresholds verfeinern**
Bestehende Thresholds (grün <800, gelb 800, orange 1000, rot 1400) sind sinnvoll. Einzige Anpassung: Startwert auf `green` bei `null` (bereits so), kein struktureller Change nötig.

**Layout: `orientation: "auto"`**
Grafana verteilt die Felder automatisch als Kacheln. Bei 5 Feldern und Panel-Breite 24 ergibt das ~5 gleichmäßige Kacheln. Keine weiteren Layout-Eingriffe nötig.

**Filter-Unit-Fix**
Grafana skaliert `"d"` (days) automatisch zu Wochen wenn der Wert >7. Lösung: Unit auf `"none"` und `displayName` auf `"Filter (Tage)"` belassen — der Zahlenwert ist dann unveränderter Rohdatenwert aus InfluxDB (Tage als Integer). Alternativ: Unit `"d"` behalten und Grafana-`noValue` oder custom unit testen. Einfachste Lösung: Unit auf `"none"` setzen.

## Risks / Trade-offs

- **Bar Gauge braucht min/max**: Ohne explizite Werte zeigt Grafana die Bar nicht korrekt an. Müssen in den Overrides gesetzt werden → kein Risiko, direkt lösbar.
- **Value Mappings überschreiben die Zahl**: Im Bar Gauge zeigt `textMode: "auto"` den gemappten Text statt der Prozentzahl. Wer den genauen Wert will, schaut ins Lüfterstufen-Panel oder Luftqualität-Timeseries. Akzeptabler Trade-off für das Status-Panel.
