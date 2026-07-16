## Context

Lares nutzt Grafana-Alerting (YAML-provisioned) mit Pushover und ntfy als Contact Points. Alle MQTT-Metriken fließen via Telegraf in InfluxDB und werden von Grafana per Flux-Query überwacht. Bestehende Regeln decken CO₂, Sungrow, Wärmepumpe und Fritz-Batterie ab.

Zwei Lücken existieren:
1. Die Vallox-Bridge publiziert keinen Fault-Status — die API hat ihn (`get_alarms`, `A_CYC_TOTAL_FAULT_COUNT`), er wird nur nicht weitergegeben.
2. Es fehlt eine Alert-Regel für `remaining_filter_days` (Wert ist bereits in MQTT vorhanden).

## Goals / Non-Goals

**Goals:**
- Vallox-Bridge um `active_alarm_count` erweitern (Anzahl aktiver, ungeklärter Alarme)
- Grafana-Alert-Regel für `active_alarm_count > 0` (Lüftungsfehler)
- Grafana-Alert-Regel für `remaining_filter_days < 30` (Filterwechsel)

**Non-Goals:**
- Kein neuer Notification-Service (kein mqttwarn, kein Node-RED)
- Kein Alarm-Detail-Mapping in MQTT (kein Text, kein Severity-Feld — Grafana-Alert reicht)
- Keine Änderung an Routing oder Contact Points

## Decisions

### 1. `active_alarm_count` statt Alarm-Details

Die API liefert `get_alarms(skip_solved=True)` — ein Python-Aufruf, der aktive Alarme zurückgibt. Die einfachste nutzbare Repräsentation für Grafana ist `len(active_alarms)` als Integer.

**Alternativ betrachtet:** Alarm-Code und Severity-Text publizieren. Abgelehnt: Grafana-Alerting arbeitet auf numerischen Feldern, String-Felder erfordern Umwege (wie bei `system_state` in Sungrow). Ein Integer ist das minimal nötige.

### 2. Filterwechsel-Schwellwert: 30 Tage

`remaining_filter_days < 30` gibt ausreichend Vorlauf ohne False Positives bei normaler Nutzung. Der Wert ist kein Secret und gehört direkt in `rules.yaml`.

### 3. Grafana-Provisioning bleibt die Alerting-Ebene

Kein neuer Service. Die YAML-Dateien in `config/grafana/provisioning/alerting/` sind bereits der GitOps-Mechanismus für Alerts — das Pattern wird fortgeschrieben.

## Risks / Trade-offs

- **Vallox-API-Verfügbarkeit** → `active_alarm_count` fällt auf 0 zurück wenn die API nicht antwortet; Alert feuert dann nicht. Gleiche Schwäche wie alle anderen Bridges — akzeptiert, da `noDataState: NoData` in Grafana gesetzt werden kann.
- **Filterwechsel-Alert persistiert** → `remaining_filter_days` bleibt niedrig bis die Anlage einen neuen Filter meldet; Alert feuert wiederholt. Grafana-`for`-Bedingung (z.B. `for: 12h`) begrenzt Notification-Frequenz via Grafana-Throttling.
