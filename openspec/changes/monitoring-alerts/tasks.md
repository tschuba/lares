## 1. Vallox-Bridge: `active_alarm_count` ergänzen

- [ ] 1.1 In `vallox2mqtt.py` nach dem Metrics-Abruf `data.get_alarms(skip_solved=True)` aufrufen und `active_alarm_count = len(active_alarms)` dem publizierten Datensatz hinzufügen
- [ ] 1.2 Test in `bridges/vallox/tests/` für den neuen Alarm-Pfad ergänzen (Szenarien: 0 Alarme, N Alarme)
- [ ] 1.3 Bridge lokal bauen: `docker build -t vallox2mqtt bridges/vallox`

## 2. Luxtronik-Bridge: zwei neue Felder

- [ ] 2.1 `holding()`-Accessor ergänzen: `entry = lux.holdings.get(name); return entry.value if entry else None`
- [ ] 2.2 `temperature_hot_water_setpoint`: `holding("hot_water_setpoint")` in den publizierten Datensatz aufnehmen (°C float, kein `/10` nötig — `CelsiusUInt16` konvertiert bereits)
- [ ] 2.3 `backup_heater_active`: `1 if inp("heatpump_zwe1_status") else 0` in den publizierten Datensatz aufnehmen
- [ ] 2.4 Bridge lokal bauen: `docker build -t luxtronik2mqtt bridges/luxtronik`

## 3. Grafana-Alerts: Lüftung

- [ ] 3.1 `lares-vallox-alarm`: `active_alarm_count > 0`, `for: 2m`, `noDataState: NoData`, severity=critical
- [ ] 3.2 `lares-filter-change`: `remaining_filter_days < 30`, `for: 12h`, `noDataState: NoData`, severity=warning

## 4. Grafana-Alerts: Wärmepumpe

- [ ] 4.1 `lares-hot-water-failure`: Flux-Math `temperature_hot_water - temperature_hot_water_setpoint < -5`, `for: 30m`, `noDataState: NoData`, severity=critical
- [ ] 4.2 `lares-backup-heater`: `backup_heater_active > 0` AND `temperature_outside > 5`, `for: 15m`, `noDataState: NoData`, severity=warning
- [ ] 4.3 `lares-legionella-run`: `temperature_hot_water > 60`, `for: 10m`, `noDataState: NoData`, severity=warning

## 5. Grafana-Alerts: PV-Batterie

- [ ] 5.1 `lares-sungrow-battery-temp`: `battery_temperature > 50`, `for: 5m`, `noDataState: NoData`, severity=critical
- [ ] 5.2 `lares-sungrow-battery-health`: `battery_state_of_healthy < 70`, `for: 1h`, `noDataState: NoData`, severity=warning

## 6. Grafana-Alerts: Haushaltsgeräte (Meross)

- [ ] 6.1 `lares-waschmaschine-fertig`: Query A = mean(power, -5m) < 15 W; Query B = max(power, -90m..-10m) > 200 W; beide Conditions AND, `for: 10m`, `noDataState: OK`, severity=info; device=`2307068416409851080248e1e9ceb390`
- [ ] 6.2 `lares-trockner-fertig`: analog, device=`2307067395364351080248e1e9ceaeab`

## 7. Grafana-Alerts: Bridge-Heartbeat

- [ ] 7.1 `lares-heartbeat-heating`: `last()` auf `heating` Measurement, `noDataState: Alerting`, `for: 5m`, severity=critical
- [ ] 7.2 `lares-heartbeat-ventilation`: `last()` auf `ventilation` Measurement, `noDataState: Alerting`, `for: 5m`, severity=critical
- [ ] 7.3 `lares-heartbeat-sungrow`: `last()` auf `sungrow` Measurement, `noDataState: Alerting`, `for: 2m`, severity=critical
- [ ] 7.4 `lares-heartbeat-ev`: `last()` auf `ev` Measurement, `noDataState: Alerting`, `for: 15m`, severity=warning

## 8. Dokumentation

- [ ] 8.1 `docs/entscheidungen.md`: ADR-006 um beide Bridge-Erweiterungen ergänzen (vallox `active_alarm_count`, luxtronik `temperature_hot_water_setpoint` + `backup_heater_active`)
- [ ] 8.2 `config/telegraf/telegraf.conf`-Kommentare: `active_alarm_count` unter ventilation, `backup_heater_active` + `temperature_hot_water_setpoint` unter heating dokumentieren
