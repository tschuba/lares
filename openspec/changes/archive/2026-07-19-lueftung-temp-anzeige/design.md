## Context

Die Vallox-Bridge (`bridges/vallox/vallox2mqtt.py`) liest per WebSocket-API alle Metriken und publisht sie einzeln auf MQTT. Telegraf leitet sie nach InfluxDB weiter. Grafana visualisiert über Flux-Queries.

Der aktuelle `Δ Zuluft − Innenluft`-Panel nutzt `thresholdsStyle.mode: line` (nur Linienfarbwechsel) und asymmetrische Schwellen (alle negativen Werte = blau, keine Abstufung). Der Bypass-Status (`A_CYC_CELL_STATE`) wird von der Bridge nicht publiziert.

Im Überblick-Dashboard zeigt das bestehende Feld `Außenluft − Innenluft` — nicht die Zuluft, was bei aktivem Bypass kein Problem ist, bei inaktivem Wärmetauscher aber das falsche Signal zeigt.

## Goals / Non-Goals

**Goals:**
- Symmetrische Farbzonen im Δ-Panel (beide Richtungen gleichwertig lesbar)
- Hintergrundfarben statt Linienfarbwechsel (`area`-Style)
- `cell_state` in MQTT verfügbar machen
- Kompakter Überblick-Block mit Δ Zuluft−Innenluft + Wärmetauscher-Status

**Non-Goals:**
- Automatische Steuerung der Lüfterstufe
- Alarm/Notification bei extremem Δ
- Änderung des bestehenden `Außenluft − Innenluft`-Felds im Status-Panel

## Decisions

**Delta-Basis: Zuluft (supply), nicht Außenluft (outdoor)**
Zuluft ist immer das was ins Haus kommt — bei Bypass ≈ Außenluft, bei Wärmerückgewinnung deutlich höher. Außenluft − Innenluft überzeichnet den Kälteeffekt im Winter. Konsequenz: der Flux-Query im Überblick-Panel entspricht dem Join aus `temperature_supply_air` und `temperature_extract_air` (identisch zum Ventilations-Dashboard).

**`cell_state` als Integer auf MQTT, Text-Mapping in Grafana**
Integer-Wert (0–3) hält die Bridge schlank; Grafana-Value-Mappings übersetzen in lesbare Texte. Alternative wäre String-Publishing in der Bridge — abgelehnt, da dann Farbschwellen in Grafana schwerer zu definieren sind.

**Stat-Panel (kein Gauge) für den Überblick**
Stat-Panels mit `colorMode: background` sind das etablierte Muster im Überblick-Dashboard (alle anderen Panels nutzen dasselbe). Ein Gauge würde visuell aus der Reihe fallen und ist für einen Übersichtswert nicht notwendig. Zwei Felder horizontal = ein Panel, konsistent mit dem bestehenden Lüftungs-Status-Panel.

**Schwellen: ±1 °C neutral, ±3 °C stark**
Abstimmung auf die Vallox-Sollwert-Toleranz (Temperatureinstellung Zuluft ±1 °C). Unter ±1 °C thermisch vernachlässigbar, über ±3 °C deutlich spürbar.

## Risks / Trade-offs

`cell_state` erst nach Bridge-Rebuild und -Restart verfügbar → Grafana-Panel zeigt bis dahin „No data" für das Wärmetauscher-Feld. Kein Datenverlust, nur verzögerte Sichtbarkeit.

Symmetrische Schwellen im Ventilations-Dashboard ändern die bisherige Farbgebung — wer sich an „blau = kalt" gewöhnt hat, sieht nun Abstufungen. Gewollte Verbesserung.

## Migration Plan

1. Bridge-Änderung committen → CI baut und pusht neues Image automatisch
2. Auf dem NAS: `docker compose --profile ventilation pull && docker compose --profile ventilation up -d`
3. Grafana-Dashboard-JSONs committen → Grafana lädt Provisioning beim nächsten Neustart oder per API-Reload

Rollback: Git-Revert der drei Dateien, Bridge-Redeployment.
