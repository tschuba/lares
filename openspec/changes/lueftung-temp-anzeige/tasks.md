## 1. Bridge: cell_state publizieren

- [x] 1.1 In `bridges/vallox/vallox2mqtt.py` → `parse_vallox_data()`: Zeile `'cell_state': metrics.get('A_CYC_CELL_STATE', 0)` ergänzen

## 2. Ventilations-Dashboard: Δ-Panel fixen

- [x] 2.1 In `config/grafana/dashboards/ventilation.json` → Panel `Δ Zuluft − Innenluft (Wärmeeintrag)`: `thresholdsStyle.mode` von `"line"` auf `"area"` setzen
- [x] 2.2 Symmetrische Schwellen setzen: `null`→blau, `-3`→hellblau, `-1`→grün, `1`→orange, `3`→rot

## 3. Überblick-Dashboard: Neues Lüftungs-Effekt-Panel

- [x] 3.1 Neues Stat-Panel `Lüftungs-Effekt` in `config/grafana/dashboards/overview.json` anlegen (horizontal, `colorMode: background`)
- [x] 3.2 Query A: Flux-Join `temperature_supply_air − temperature_extract_air` (letzter Wert, range -10m), Feld `delta`, Einheit `celsius`, symmetrische Schwellen wie in 2.2
- [x] 3.3 Query B: `cell_state`-Metric letzter Wert; Value Mappings: 0→„Wärmerückgewinnung" (grün), 1→„Kälterückgewinnung" (hellblau), 2→„Bypass" (blau), 3→„Abtauung" (rot)
- [x] 3.4 Panel in Grid positionieren (unterhalb des bestehenden Lüftungs-Status-Panels)
