## 1. Übersichts-Dashboard erstellen

- [x] 1.1 `config/grafana/dashboards/overview.json` anlegen mit Titel "Lares – Überblick", gleichem Zeitfenster (`now/d → now`) und Refresh (`15s`) wie die bestehenden Dashboards
- [x] 1.2 Energie-Zeile: 5 Stat-Panels aus `energy.json` übernehmen (PV Erzeugung, Hausverbrauch, Netz, Heimspeicher-Ladestand, Sensor Batteriestand) — Queries 1:1 kopieren
- [x] 1.3 Lüftungs-Zeile: Stat-Panel "Aktueller Status" aus `ventilation.json` übernehmen (CO2, Filter-Tage, Feuchte, ΔT)
- [x] 1.4 Wetter-Zeile: 3 Stat-Panels für Außentemperatur (`weather.temp`), Windgeschwindigkeit (`weather.windspeed`), Windrichtung (`weather.winddir`) — als `last()`-Wert aus letzten 10 Minuten

## 2. Dashboard Links ergänzen

- [x] 2.1 `links`-Block in `overview.json` einfügen: Links zu energy, heating, ventilation, weather, system — je `type: "dashboards"`, `keepTime: true`, `targetBlank: false`
- [x] 2.2 `links`-Block in `energy.json` einfügen: Links zu overview, heating, ventilation, weather, system
- [x] 2.3 `links`-Block in `heating.json` einfügen: Links zu overview, energy, ventilation, weather, system
- [x] 2.4 `links`-Block in `ventilation.json` einfügen: Links zu overview, energy, heating, weather, system
- [x] 2.5 `links`-Block in `weather.json` einfügen: Links zu overview, energy, heating, ventilation, system
- [x] 2.6 `links`-Block in `system.json` einfügen: Links zu overview, energy, heating, ventilation, weather

## 3. Abschluss

- [x] 3.1 Grafana neu laden (oder Provisioning triggern) und prüfen, ob "Lares – Überblick" erscheint
- [x] 3.2 Dashboard Links in einem Dashboard testen: Klick → Zeitbereich bleibt erhalten
- [x] 3.3 Optional: "Lares – Überblick" als Home Dashboard in Grafana Organization Settings setzen
