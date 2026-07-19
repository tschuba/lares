## ADDED Requirements

### Requirement: Dashboard Links in allen Dashboards
Alle 6 Grafana-Dashboards (overview, energy, heating, ventilation, weather, system) SHALL einen `links`-Block enthalten, der zu den jeweils anderen 5 Dashboards verlinkt.

#### Scenario: Navigation von einem Dashboard zum anderen
- **WHEN** ein Nutzer auf einen Dashboard Link klickt
- **THEN** wird das Ziel-Dashboard im gleichen Tab geöffnet und der aktuelle Zeitbereich übernommen (`keepTime: true`)

### Requirement: Zeitbereich bleibt beim Wechsel erhalten
Dashboard Links SHALL mit `keepTime: true` konfiguriert sein, sodass der gewählte Zeitbereich beim Dashboard-Wechsel nicht zurückgesetzt wird.

#### Scenario: Zeitbereich-Erhalt
- **WHEN** der Nutzer im Dashboard "Energie" den Zeitbereich auf "letzte 7 Tage" gesetzt hat und zu "Lüftung" navigiert
- **THEN** zeigt "Lüftung" ebenfalls den Zeitbereich "letzte 7 Tage"
