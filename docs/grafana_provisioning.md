# Grafana Provisionierung & Dashboards

Dieses Dokument beschreibt die Einrichtung der versionskontrollierten Grafana-Konfiguration und Dashboards im Repository (`config/grafana/`).

## Erstellte Struktur

Folgende Verzeichnisstruktur und Dateien wurden unter `config/grafana/` angelegt:

```text
config/grafana/
├── dashboards/
│   ├── energy-sankey.json
│   ├── system.json
│   └── weather.json
└── provisioning/
    ├── dashboards/
    │   └── dashboards.yml
    └── datasources/
        └── influxdb.yml
```

### 1. Provisioning (`provisioning/`)

- **`datasources/influxdb.yml`**: Konfiguriert die `InfluxDB NAS`-Verbindung. Sie liest sicher die Umgebungsvariablen (`$INFLUX_ORG`, `$INFLUX_BUCKET`, `$INFLUX_TOKEN`), die im restlichen Setup verwendet werden, und konfiguriert die Nutzung der `Flux`-Abfragesprache. Ihr wird eine feste UID `influxdb-nas` zugewiesen, auf die sich Dashboards verlässlich beziehen können.
- **`dashboards/dashboards.yml`**: Weist Grafana an, den Ordner `/var/lib/grafana/dashboards` im Container rekursiv nach JSON-Dateien zu durchsuchen und sie automatisch in Grafana in einem Ordner namens "lares" zu laden.

### 2. Dashboards (`dashboards/`)

Es wurden Basis-Grafana-JSON-Schemata für die drei primären Anwendungsfälle generiert:

- **`energy-sankey.json`**: Implementiert das `fr-ser-sankey-panel` (gemäß ADR-012) und enthält Flux-Queries für `sungrow`, `meross` und `heating` (Novelan) Metriken.
- **`weather.json`**: Visualisiert Ecowitt-Daten mit Zeitreihen-Panels für Temperatur, Luftfeuchtigkeit und Windgeschwindigkeit.
- **`system.json`**: Bietet ein Zeitreihen-Monitoring für die NAS-Ressourcen (Telegrafs `cpu` und `mem` Metriken).

## Nächste Schritte für Coolify

Da Grafana über Coolify auf dem Pi läuft, sollten folgende Schritte zur Einbindung durchgeführt werden:

1. In Coolify den Grafana-Service so konfigurieren, dass diese Verzeichnisse gemountet werden.
2. Einen Bind-Mount des lokalen Pfads `./config/grafana/provisioning` nach `/etc/grafana/provisioning` im Container einrichten.
3. Einen Bind-Mount des lokalen Pfads `./config/grafana/dashboards` nach `/var/lib/grafana/dashboards` im Container einrichten.
4. Die notwendigen Umgebungsvariablen (`INFLUX_ORG`, `INFLUX_BUCKET`, `INFLUX_TOKEN`) im Coolify-Service setzen, damit Grafana diese in der Datenquellen-YAML auflösen kann.
5. Sicherstellen, dass das Sankey-Plugin installiert wird. Dies kann über die Umgebungsvariable `GF_INSTALL_PLUGINS=fr-ser-sankey-panel` in der Coolify-Service-Konfiguration erfolgen.

> [!TIP]
> Die Dashboard-JSONs sind funktionale Basis-Templates. Um sie zu erweitern, können sie in der Grafana-UI visuell angepasst (Layout, Farben, Schwellenwerte etc.) und anschließend als JSON exportiert werden, um die Dateien in diesem Repository zu überschreiben (Docs-as-Code).
