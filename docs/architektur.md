# Architektur

## Kontext

Lares ist eine lokal orientierte Smart-Home-Zentrale mit MQTT als Integrationsbus, Home Assistant als Steuerungs- und Automationskern, Grafana für Visualisierung und InfluxDB auf dem NAS für Langzeitspeicherung.

Der Raspberry Pi 4 dient als zentrale Laufzeitumgebung für die Integrationsdienste. Das Ugreen NAS übernimmt den Schwerpunkt Datenspeicherung.

## Leitprinzipien

- Lokal-first: Steuerung und Datenfluss im LAN priorisieren
- MQTT-first: einheitlicher Integrationsbus für heterogene Protokolle
- Funktionsorientierte Domains: Namen beschreiben Aufgabe, nicht Tool
- Security-by-default: internet-erreichbare Oberflächen nur mit Authentik-Schutz
- Niedrige Komplexität: nur eine produktive InfluxDB-Instanz (auf NAS)

## Subdomains und Begründung

| Subdomain | Service | Zweck | Begründung |
|---|---|---|---|
| `home.schubs.net` | Home Assistant | Bedienung, Automationen, Integrationslogik | Bereits etabliert; semantisch klar für Heimsteuerung |
| `cockpit.schubs.net` | Grafana | Monitoring, Trends, technische Übersicht | "Cockpit" transportiert Instrumenten- und Übersichtsgedanken |

Hinweis: Die Benennung bleibt bei internem Toolwechsel stabil und folgt dem Funktionsprinzip.

## Laufzeitarchitektur

- Reverse Proxy und Authentik laufen bereits auf dem Pi (Coolify-Umfeld).
- Home Assistant ist bereits via Coolify im Betrieb und wird zusätzlich ins interne `lares`-Netz eingebunden.
- Mosquitto ist der interne MQTT-Broker.
- Protokollspezifische Bridges binden Geräte an MQTT an.
- Meross-Integration ist dual-path: `meross_lan` in HA für Steuerung, `meross2mqtt` für direkte Energiemetriken zu MQTT/InfluxDB.
- Telegraf schreibt MQTT-Metriken (inkl. Meross) in InfluxDB auf dem NAS.
- WeeWX übernimmt die Weiterleitung von Wetterdaten an externe Wetterdienste.
- Grafana ist internet-erreichbar via Traefik, aber durch Authentik abgesichert.
- InfluxDB läuft zentral auf dem NAS und wird von Home Assistant und Telegraf beschrieben.

## Architekturdiagramm

```mermaid
flowchart TD
    Internet((Internet))

    subgraph Pi ["Raspberry Pi 4 - Coolify Host"]
        Traefik["Traefik Reverse Proxy"]
        Authentik["Authentik SSO"]

        subgraph LARES ["Docker-Netzwerk: lares"]
            Mosquitto["Mosquitto :1883"]
            ModbusProxy["modbus-proxy :502"]
            S2M["sungrow2mqtt"]
            L2M["luxtronik2mqtt"]
            V2M["vallox2mqtt (custom)"]
            M2M["meross2mqtt"]
            E2M["ecowitt2mqtt :4004"]
            Telegraf["Telegraf"]
            WeeWX["WeeWX"]
            HA["Home Assistant\nhome.schubs.net"]
            Grafana["Grafana\ncockpit.schubs.net"]
        end
    end

    subgraph NAS ["Ugreen DXP2800 NAS"]
        InfluxDB[("InfluxDB 2.x :8086")]
    end

    subgraph Geraete ["LAN Geräte"]
        Sungrow["Sungrow SH8.0RT\nModbus TCP :502"]
        Novelan["Novelan LADV 9.1\nLuxtronik2 :8889"]
        Vallox["Vallox ValloPlus 350 MV-E\nTCP :18080"]
        Ecowitt["Ecowitt GW1201\nHTTP Push"]
        Bambu["BambuLab P1S\nMQTT intern"]
        Meross["Meross MSS310/MSS315\nLeistungsmessung"]
        Blink["Blink Outdoor 4\nSync Module 2"]
        Echo["Echo Dot / Echo Show"]
    end

    subgraph Wetterdienste ["Externe Wetterdienste"]
        AWEKAS["AWEKAS"]
        Windy["Windy.com"]
        WU["Weather Underground"]
        CWOP["CWOP/APRS"]
        OWM["OpenWeatherMap"]
    end

    Internet --> Traefik
    Traefik --> Authentik
    Authentik --> HA
    Authentik --> Grafana

    Sungrow -->|Modbus TCP| ModbusProxy
    ModbusProxy --> S2M
    S2M -->|MQTT| Mosquitto

    Novelan -->|Luxtronik2| L2M
    L2M -->|MQTT| Mosquitto

    Vallox -->|TCP| V2M
    V2M -->|MQTT| Mosquitto

    Ecowitt -->|HTTP Push| E2M
    E2M -->|MQTT| Mosquitto
    Ecowitt -->|HTTP Push| WeeWX

    WeeWX -->|Upload| AWEKAS
    WeeWX -->|Upload| Windy
    WeeWX -->|Upload| WU
    WeeWX -->|Upload| CWOP
    WeeWX -->|Upload| OWM

    Mosquitto -->|MQTT| HA
    Bambu -->|Integration| HA
    Meross -->|meross_lan| HA
    Meross -->|HTTP| M2M
    M2M -->|MQTT| Mosquitto
    Mosquitto -->|MQTT| Telegraf
    Telegraf -->|Write| InfluxDB

    Blink -. Cloud API .-> Internet
    Internet -. Blink API .-> HA

    HA <-->|Alexa API| Echo

    HA -->|Write| InfluxDB
    Grafana -->|Read| InfluxDB
```

## Datenfluss

1. Feldgeräte liefern Rohdaten über native Protokolle.
2. Bridges transformieren in MQTT-Topics unter gemeinsamer Topic-Hierarchie.
3. Home Assistant konsumiert MQTT-Daten und führt Automationen aus.
4. Home Assistant schreibt Messwerte in InfluxDB auf dem NAS.
5. Grafana visualisiert aus InfluxDB.
6. Ecowitt-Daten werden parallel über WeeWX an externe Wetterdienste veröffentlicht.

## Energiefluss-Visualisierung

Energieflüsse werden in zwei Oberflächen dargestellt:

- Home Assistant Energy Dashboard (`home.schubs.net`) für täglichen Betrieb
- Grafana mit Sankey-Diagramm (`cockpit.schubs.net`) für detaillierte Flussanalysen

Energiebezogene Datenpunkte umfassen:

- Sungrow: PV-Erzeugung, Batterie (Laden/Entladen), Netzbezug, Einspeisung
- Novelan: Verbrauchswerte der Wärmepumpe (soweit verfügbar)
- Meross: Lasten von BambuLab P1S, Arbeitstisch, Waschmaschine, Trockner

## Wetterdaten-Freigabe

Für die externe Nutzung der Wetterdaten wird ein zweiter Pfad genutzt:

- Primär lokal: `Ecowitt -> ecowitt2mqtt -> MQTT -> Home Assistant`
- Parallel extern: `Ecowitt -> WeeWX -> Wetterdienste`

Dadurch bleiben lokale Automationen unabhängig und externe Veröffentlichungen klar gekapselt.

## Netzwerk- und Sicherheitsmodell

- Interne Dienste (MQTT, Bridges) sind nicht internet-erreichbar.
- Grafana und Home Assistant sind internet-erreichbar, aber durch Authentik abgesichert.
- Das NAS bleibt ohne direkte Internetexposition.
- MQTT-Zugriff von extern ist standardmäßig deaktiviert.

## Warum nur eine InfluxDB-Instanz auf dem NAS

Entscheidung: direkte Speicherung auf NAS-InfluxDB statt doppelter Influx-Topologie.

Begründung:

- Weniger Betriebs- und Replikationskomplexität
- Keine Split-Brain- oder Sync-Probleme
- Datenspeicher liegt dort, wo ohnehin Langzeitbetrieb vorgesehen ist
- Pi und NAS sind im selben LAN, daher ist direkte Kommunikation technisch einfach

Trade-off:

- Bei NAS-Ausfall werden kurzfristig keine neuen Zeitreihen geschrieben.
- Steuerung und Automationen in Home Assistant bleiben davon unabhängig funktionsfähig.
