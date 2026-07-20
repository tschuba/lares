## Context

Lares nutzt Grafana-Alerting (YAML-provisioned) mit Pushover und ntfy als Contact Points. Alle MQTT-Metriken fließen via Telegraf in InfluxDB und werden von Grafana per Flux-Query überwacht. Bestehende Regeln decken CO₂, Sungrow-Systemfehler, Wärmepumpen-Fehler, Lüftungs-Heizbetrieb und Fritz-Batterie ab.

## Goals / Non-Goals

**Goals:**
- Vallox-Bridge: `active_alarm_count` ergänzen
- Luxtronik-Bridge: `temperature_hot_water_setpoint` und `backup_heater_active` ergänzen
- 13 neue Grafana-Alert-Regeln (siehe tasks.md)

**Non-Goals:**
- Kein neuer Notification-Service
- Kein Alarm-Detail-Mapping (kein Text, kein Severity-Feld in MQTT)
- Keine Änderung an Routing oder Contact Points

## Decisions

### 1. `active_alarm_count` statt Alarm-Details (Vallox)

`get_alarms(skip_solved=True)` liefert aktive Alarme; `len(active_alarms)` als Integer ist das minimal nötige für Grafana-Threshold. String-Felder erfordern Flux-Map-Umwege wie bei Sungrow `system_state` — abgelehnt.

### 2. Filterwechsel-Schwellwert: 30 Tage

`remaining_filter_days < 30` gibt ausreichend Vorlauf ohne False Positives. Direkt in `rules.yaml`, kein Secret.

### 3. `temperature_hot_water_setpoint` aus Luxtronik Holdings

Luxtronik `hot_water_setpoint` ist ein Holding-Register (Index 6, `CelsiusUInt16`, `.value` liefert °C als float). `lux.read()` liest Holdings bereits — kein API-Mehraufwand, nur ein zusätzlicher `holding()`-Accessor im Bridge-Code.

Der Warmwasser-Alert nutzt dynamischen Sollwert statt Hardcode: `actual - setpoint < -5°C`. Damit zieht der Alert automatisch mit wenn der Sollwert am Luxtronik-Controller geändert wird. Flux-Math wie bei `lares-ventilation-heating`.

### 4. `backup_heater_active` aus SHI-Input `heatpump_zwe1_status`

Die Luxtronik-Bibliothek stellt `heatpump_zwe1_status` (ZWE1 = Zusatzwärmeerzeuger 1 = Heizstab) als Bool-Input aus dem SHI-Interface bereit (`since: "3.90.1"`). Direktes boolean Flag, kein operating_mode-Integer-Mapping nötig. Im Bridge als `0`/`1` publiziert.

**Alternativ betrachtet:** `operating_mode_int` (`.raw` des Calculation-Felds `ID_WEB_WP_BZ_akt`) — abgelehnt, weil die Bibliothek nur Codes 0–7 kennt und Novelan-spezifische Modi (Heizstab, Legionellen) als unbekannte Integers erscheinen würden, ohne Live-Spike verifizierbar.

### 5. Legionellen-Alert via Temperatur statt operating_mode

`temperature_hot_water > 60°C` statt `operating_mode_int == <unbekannter Wert>`. Vorteile:
- Kein Bridge-Patch für operating_mode nötig
- Fängt auch Fehlfunktionen ab (Überheizung unabhängig vom auslösenden Modus)
- Keine Verifizierung der Novelan-spezifischen Modusnummern notwendig

### 6. Sungrow-Batterie: Temperatur und Gesundheit statt Ladestand

`battery_level < 10%` wurde abgelehnt: im netzgekoppelten Betrieb schaltet der Wechselrichter automatisch auf Netzbezug — kein Handlungsbedarf, regelmäßiger Noise im Winter.

`battery_temperature > 50°C` und `battery_state_of_healthy < 70%` sind actionable (Sicherheit bzw. Garantie/Austausch). Beide Felder werden von SunGather bei `level: 2` publiziert und von Telegraf als JSON-Wildcard in InfluxDB gespeichert — keine Konfigurationsänderung nötig.

Hinweis: Das Register heißt tatsächlich `battery_state_of_healthy` (SunGather-Schreibweise, grammatikalisch inkorrekt).

### 7. Meross Appliance-Done: Zwei-Zeitfenster-Query

`power < 15 W für 10 min` allein würde beim Start sofort feuern (Gerät war aus). Lösung: zwei Zeitfenster kombinieren:
- Query A: `mean(power)` letzte 5 min < 15 W (aktuell idle)
- Query B: `max(power)` von -90 min bis -10 min > 200 W (war kürzlich aktiv)

Beide Bedingungen mit AND verknüpft. Meross Device-IDs aus bestehendem Energy-Dashboard:
- Trockner: `2307067395364351080248e1e9ceaeab`
- Waschmaschine: `2307068416409851080248e1e9ceb390`

### 8. Bridge-Heartbeat via noDataState: Alerting

Grafana `noDataState: Alerting` auf einer `last()`-Query pro Measurement erkennt Datenpausen ohne separate Heartbeat-Infrastruktur. Toleranzen je nach Poll-Intervall:
- heating/ventilation: 60 s Poll → 5 min Toleranz
- sungrow: 5 s Poll → 2 min Toleranz
- ev: 60 s Poll + Cloud-Latenz → 15 min Toleranz

### 9. Grafana-Provisioning bleibt die Alerting-Ebene

Kein neuer Service. `config/grafana/provisioning/alerting/rules.yaml` ist der etablierte GitOps-Mechanismus.

## Risks / Trade-offs

- **Vallox-API-Verfügbarkeit** → `active_alarm_count` fällt auf 0 zurück; Alert feuert nicht. Akzeptiert (`noDataState: NoData`).
- **Filterwechsel persistiert** → Alert feuert wiederholt bis neuer Filter gemeldet. `for: 12h` begrenzt Frequenz.
- **Heizstab ZWE1 vs ZWE2** → Nur ZWE1 wird überwacht. ZWE2 ist an der Novelan LADV 9.1 typischerweise nicht verbaut — bei Bedarf nachrüstbar.
- **Meross Startup False Positive** → Zwei-Zeitfenster-Query verhindert Startup-Alert wenn Gerät nie aktiv war.
- **battery_state_of_healthy Langzeitwert** → Alterungsdegradation < 70% ist selten und persistent; `for: 1h` verhindert transienten Ausreißer.
