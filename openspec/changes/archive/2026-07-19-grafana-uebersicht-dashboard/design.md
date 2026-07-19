## Context

Grafana 13.0.2, gehostet auf dem Pi via Coolify. Fünf bestehende Dashboards (`energy.json`, `heating.json`, `ventilation.json`, `weather.json`, `system.json`) — alle mit identischem Zeitfenster (`now/d → now`) und Refresh (`15s`). Alle Panels sind JSON-provisioniert aus `config/grafana/dashboards/`, das Verzeichnis ist bereits in `dashboards.yml` eingetragen.

## Goals / Non-Goals

**Goals:**
- Neues `overview.json` als zentraler Einstiegspunkt mit ~10 Stat-/Gauge-Panels
- Dashboard Links in allen 6 Dashboards mit `Keep time range`
- Queries direkt aus bestehenden Panels übernehmen — keine neuen Flux-Queries

**Non-Goals:**
- Zusammenführen aller Panels in ein einzelnes Dashboard
- Scrolling-Navigation / Anchor-Links innerhalb eines Dashboards (Grafana unterstützt das nicht nativ)
- Änderungen an Datenquellen, Bridges oder InfluxDB

## Decisions

**Welche Panels ins Übersichts-Dashboard?**

Energie-Zeile (5 Panels, alle stat/gauge, Queries direkt übernommen):
- PV Erzeugung (Panel 1, energy.json) — berechneter Flux-Wert
- Hausverbrauch (Panel 7, energy.json) — `sungrow.load_power_hybrid`
- Netz (Panel 3, energy.json) — `sungrow.export_power_hybrid`
- Heimspeicher-Ladestand (Panel 4, energy.json) — `sungrow.battery_level`
- Sensor Batteriestand (Panel 13, energy.json) — `fritz_energy.battery_pct`

Lüftung (1 Panel, stat multi-value, Query direkt übernommen):
- Aktueller Status (Panel 1, ventilation.json) — CO2, Filter-Tage, Feuchte, ΔT in einem Panel

Wetter (3 Panels, stat mit last-Wert):
- Außentemperatur — `weather.temp`
- Windgeschwindigkeit — `weather.windspeed`
- Windrichtung — `weather.winddir`

Layout:
```
[ PV ] [ Haus ] [ Netz ] [ Heimsp.-Lad. ] [ Sensor Batt. ]
[          Lüftung: Status (CO2, Filter, ΔT)              ]
[ Außentemp. ] [ Windgeschw. ] [ Windrichtung ]
```

**Warum keine Timeseries-Panels im Überblick?**
Stat-Panels laden schneller und zeigen den aktuellen Zustand auf einen Blick. Wer den Verlauf sehen will, springt ins Detaildashboard.

**Dashboard Links: wo platziert?**
Als Grafana `links`-Block je Dashboard (Settings → Links). Typ `dashboard`, mit `keepTime: true` und `targetBlank: false` (gleicher Tab, kein Fenster-Chaos).

**Home Dashboard:**
`overview.json` wird in Grafana als org-weites Home Dashboard gesetzt (Organization Settings → Home Dashboard). Alternativ reicht auch ein direkter Bookmark auf die URL.

## Risks / Trade-offs

- [Queries dupliziert] Queries aus bestehenden Panels werden in `overview.json` kopiert — Änderungen müssen an zwei Stellen gepflegt werden → Mitigation: Im Panel-Titel auf das Quelldashboard verweisen; langfristig ggf. Grafana Library Panels nutzen
- [PV-Query komplex] Die PV-Erzeugung ist ein berechneter Flux-Wert (kein direktes Feld) — Query wird 1:1 übernommen, kein Risiko
- [Grafana Home Dashboard] Setzt eine manuelle Einstellung in der Grafana UI voraus (nicht per Provisioning konfigurierbar ohne extra YAML) → Mitigation: Als optionaler Schritt dokumentieren
