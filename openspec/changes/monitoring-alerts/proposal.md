## Why

Lares überwacht mehrere kritische Haustechnik-Systeme (PV-Anlage, Wärmepumpe, Lüftung, Stromzähler), meldet Fehler und Grenzwertverletzungen aber noch nicht vollständig per Push-Benachrichtigung. Grafana und ntfy/Pushover sind bereits als Notification-Infrastruktur vorhanden — es fehlen einzelne Alert-Regeln und ein Fault-Feld in der Vallox-Bridge.

## What Changes

- Neue Grafana-Alert-Regel: **Filterwechsel Lüftungsanlage** (`remaining_filter_days < 30`)
- Neue Grafana-Alert-Regel: **Lüftungsanlage Fehler** (fault_code > 0)
- Erweiterung `vallox2mqtt`: Vallox-Fehlercode (`A_CYC_FAULT_CODE` o.ä.) aus der API lesen und als `fault_code` publizieren, damit die Alert-Regel greifen kann

Die bestehenden Regeln für CO₂, Sungrow-Fehler, Wärmepumpen-Fehler und Fritz-Batterie bleiben unverändert. Es wird kein neuer Notification-Service eingeführt — die vorhandene Grafana-Alerting-Infrastruktur (Pushover + ntfy als Contact Points, YAML-Provisioning) wird genutzt.

## Capabilities

### New Capabilities

- `vallox-fault-reporting`: Bridge publiziert Vallox-Fehlercode auf MQTT; Grafana alertiert bei fault_code > 0
- `filter-change-alert`: Grafana alertiert wenn die verbleibenden Filtertage unter einen Schwellwert fallen

### Modified Capabilities

- `vallox-bridge`: Erweiterung um Fault-Code-Feld (kein Behavior-Break, nur additive Erweiterung des publizierten JSON)

## Impact

- `bridges/vallox/vallox2mqtt.py`: kleines Patch, neues Feld im publizierten Datensatz
- `config/grafana/provisioning/alerting/rules.yaml`: zwei neue Alert-Regeln
- Kein neuer Service, keine neue Abhängigkeit, kein Compose-Änderung
