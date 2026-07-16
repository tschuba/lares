## 1. Vallox-Bridge: Fault-Feld ergänzen

- [ ] 1.1 In `vallox2mqtt.py` nach dem Metrics-Abruf `data.get_alarms(skip_solved=True)` aufrufen und `active_alarm_count = len(active_alarms)` dem publizierten Datensatz hinzufügen
- [ ] 1.2 Test in `bridges/vallox/tests/` für den neuen Alarm-Pfad ergänzen (Szenarien: 0 Alarme, N Alarme)
- [ ] 1.3 Bridge lokal bauen und Smoke-Test: `docker build -t vallox2mqtt bridges/vallox`

## 2. Grafana-Alert: Lüftungsanlage Alarm

- [ ] 2.1 Alert-Regel `lares-vallox-alarm` in `config/grafana/provisioning/alerting/rules.yaml` ergänzen: Flux-Query auf `ventilation` Measurement, Feld `active_alarm_count`, Threshold > 0, `for: 2m`, `noDataState: NoData`, severity=critical
- [ ] 2.2 Annotation-Text formulieren (analog zu `lares-heatpump-fault`)

## 3. Grafana-Alert: Filterwechsel

- [ ] 3.1 Alert-Regel `lares-filter-change` in `config/grafana/provisioning/alerting/rules.yaml` ergänzen: Flux-Query auf `ventilation` Measurement, Feld `remaining_filter_days`, Threshold < 30, `for: 12h`, `noDataState: NoData`, severity=warning
- [ ] 3.2 Annotation-Text formulieren

## 4. Dokumentation

- [ ] 4.1 `docs/entscheidungen.md`: ADR-006 um die Bridge-Erweiterung (active_alarm_count) ergänzen
- [ ] 4.2 `config/telegraf/telegraf.conf`-Kommentar prüfen: ist `active_alarm_count` als bekanntes Feld dokumentiert?
