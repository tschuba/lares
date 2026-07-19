### Requirement: Luftfeuchtigkeit als Bar Gauge mit Komfort-Zonen
Das Panel „Aktueller Status" SHALL Luftfeuchtigkeit als Bar Gauge (`displayMode: "lcd"`) mit min=0, max=100 darstellen. Thresholds und Value Mappings MÜSSEN die Komfort-Zone (40–60%) als grünen Bereich ausweisen. Der angezeigte Text SHALL den Zonennamen zeigen (Zu trocken / Trocken / Komfort / Feucht / Zu feucht).

#### Scenario: Wert im Komfortbereich
- **WHEN** Luftfeuchtigkeit liegt zwischen 40% und 60%
- **THEN** zeigt der Balken einen grünen Bereich und der Text lautet „Komfort"

#### Scenario: Wert unter Komfortbereich
- **WHEN** Luftfeuchtigkeit liegt unter 30%
- **THEN** zeigt der Balken einen roten Bereich und der Text lautet „Zu trocken"

#### Scenario: Wert über Komfortbereich
- **WHEN** Luftfeuchtigkeit liegt über 70%
- **THEN** zeigt der Balken einen orangen oder roten Bereich und der Text lautet „Zu feucht"

### Requirement: Kachel-Layout statt horizontaler Zeilen
Das Panel „Aktueller Status" SHALL `orientation: "auto"` verwenden, sodass die Metriken als Kacheln dargestellt werden statt als vollbreite horizontale Zeilen.

#### Scenario: Mehrere Metriken nebeneinander
- **WHEN** das Panel mindestens 2 Metriken enthält
- **THEN** werden diese nebeneinander als gleichmäßige Kacheln angezeigt

### Requirement: Filter-Anzeige in Tagen
Das Panel SHALL die verbleibende Filterlebensdauer in Tagen (ganzzahlig) anzeigen, nicht in Wochen oder anderen automatisch skalierten Einheiten.

#### Scenario: Filterwert unter 7 Tagen
- **WHEN** der Filterwert kleiner als 7 Tage ist
- **THEN** wird der Wert als Tage angezeigt (z.B. „5"), nicht als Bruchzahl von Wochen
