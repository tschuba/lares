## Why

Lares überwacht mehrere kritische Haustechnik-Systeme (PV-Anlage, Wärmepumpe, Lüftung, Stromzähler), meldet Fehler und Grenzwertverletzungen aber noch nicht vollständig per Push-Benachrichtigung. Grafana und ntfy/Pushover sind bereits als Notification-Infrastruktur vorhanden — es fehlen einzelne Alert-Regeln und Bridge-Felder für Wärmepumpe, PV-Batterie, Haushaltsgeräte und Bridge-Heartbeats.

## What Changes

**Bridge-Erweiterungen:**
- `vallox2mqtt`: `active_alarm_count` aus der Vallox-API (bereits geplant)
- `luxtronik2mqtt`: zwei neue Felder — `temperature_hot_water_setpoint` (Luxtronik-Sollwert aus Holdings) und `backup_heater_active` (ZWE1-Status, boolean)

**Neue Grafana-Alert-Regeln:**
- **Filterwechsel Lüftungsanlage** (`remaining_filter_days < 30`)
- **Lüftungsanlage Fehler** (`active_alarm_count > 0`)
- **Warmwasser-Ausfall** (Ist-Temperatur > 5°C unter Luxtronik-Sollwert)
- **Heizstab-Einsatz bei milder Außentemperatur** (`backup_heater_active` AND `temp_outside > 5°C`)
- **Legionellen / Warmwasser-Überheizung** (`temperature_hot_water > 60°C`)
- **PV-Batterie Übertemperatur** (`battery_temperature > 50°C`)
- **PV-Batterie Degradation** (`battery_state_of_healthy < 70%`)
- **Waschmaschine fertig** (Leistung war hoch, jetzt < 15 W)
- **Trockner fertig** (Leistung war hoch, jetzt < 15 W)
- **Bridge-Heartbeat** (4 Regeln: heating, ventilation, sungrow, ev)

Die bestehenden Regeln für CO₂, Sungrow-Fehler, Wärmepumpen-Fehler und Fritz-Batterie bleiben unverändert. Kein neuer Notification-Service.

## Capabilities

### New Capabilities

- `vallox-fault-reporting`: Bridge publiziert `active_alarm_count`; Grafana alertiert bei > 0
- `filter-change-alert`: Grafana alertiert wenn `remaining_filter_days < 30`
- `hot-water-failure`: Grafana alertiert wenn Warmwasser-Ist unter Luxtronik-Sollwert fällt
- `backup-heater-alert`: Grafana alertiert bei unnötigem Heizstab-Einsatz
- `legionella-overheat-alert`: Grafana alertiert bei Warmwasser > 60°C (Legionellenprogramm + Überheizung)
- `sungrow-battery-health`: Grafana alertiert bei Batterie-Übertemperatur und Degradation
- `appliance-done-alerts`: Grafana alertiert wenn Waschmaschine oder Trockner fertig sind
- `bridge-heartbeat-alerts`: Grafana alertiert wenn Bridge-Measurements ausbleiben

### Modified Capabilities

- `vallox-bridge`: Erweiterung um `active_alarm_count`
- `luxtronik-bridge`: Erweiterung um `temperature_hot_water_setpoint` und `backup_heater_active`

## Impact

- `bridges/vallox/vallox2mqtt.py`: neues Feld `active_alarm_count`
- `bridges/luxtronik/luxtronik2mqtt.py`: zwei neue Felder aus SHI-Interface
- `config/grafana/provisioning/alerting/rules.yaml`: 13 neue Alert-Regeln
- Kein neuer Service, keine neue Abhängigkeit, keine Compose-Änderung
