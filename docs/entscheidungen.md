# Architekturentscheidungen

Dieses Dokument hält die zentralen Entscheidungen für Lares mit kurzer Begründung fest.

## Inhaltsverzeichnis

- [ADR-001: Projektname "Lares"](#adr-001-projektname-lares)
- [ADR-002: Funktionsorientierte Subdomains](#adr-002-funktionsorientierte-subdomains)
- [ADR-003: MQTT als Integrationsbus](#adr-003-mqtt-als-integrationsbus)
- [ADR-004: modbus-proxy vor Sungrow](#adr-004-modbus-proxy-vor-sungrow)
- [ADR-005: InfluxDB nur auf NAS](#adr-005-influxdb-nur-auf-nas)
- [ADR-006: Custom Code für Vallox, WeeWX und Meross](#adr-006-custom-code-für-vallox-weewx-und-meross)
- [ADR-007: Externe Erreichbarkeit strikt minimieren](#adr-007-externe-erreichbarkeit-strikt-minimieren)
- [ADR-008: Authentik für alle internet-erreichbaren Oberflächen](#adr-008-authentik-für-alle-internet-erreichbaren-oberflächen)
- [ADR-009: Blink als akzeptierte Cloud-Ausnahme](#adr-009-blink-als-akzeptierte-cloud-ausnahme)
- [ADR-010: Wetterdaten mit WeeWX an mehrere Dienste veröffentlichen](#adr-010-wetterdaten-mit-weewx-an-mehrere-dienste-veröffentlichen)
- [ADR-011: Hybride Meross-Integration (HA-Kontrolle + Cloud-MQTT-Metriken)](#adr-011-hybride-meross-integration-ha-kontrolle--cloud-mqtt-metriken)
- [ADR-015: DNS-Interception für Meross via dnsmasq (abgelöst)](#adr-015-dns-interception-für-meross-via-dnsmasq)
- [ADR-012: Energieflüsse doppelt visualisieren (HA + Grafana Sankey)](#adr-012-energieflüsse-doppelt-visualisieren-ha--grafana-sankey)
- [ADR-013: Sungrow-Integration als off-the-shelf Image](#adr-013-sungrow-integration-als-off-the-shelf-image)
- [ADR-014: NAS-zentrierte Service-Verteilung](#adr-014-nas-zentrierte-service-verteilung)

## ADR-001: Projektname "Lares"

- Status: Angenommen
- Kontext: Gewünscht war ein prägnanter, nicht zu technischer Name mit Augenzwinkern.
- Entscheidung: Projektname ist `Lares`.
- Begründung: Historische Referenz auf die römischen Schutzgottheiten des Hauses; passt zur Funktion als stille, dauerhafte Heimzentrale.

## ADR-002: Funktionsorientierte Subdomains

- Status: Angenommen
- Kontext: Subdomains sollen auf Funktion statt Tool-Namen verweisen.
- Entscheidung:
  - `home.schubs.net` für Home Assistant
  - `cockpit.schubs.net` für Grafana
- Begründung: Höhere semantische Stabilität bei späterem Toolwechsel; bessere Verständlichkeit für Nutzer.

## ADR-003: MQTT als Integrationsbus

- Status: Angenommen
- Kontext: Heterogene Feldprotokolle (Modbus, Luxtronik, proprietär, HTTP-Push) sollen vereinheitlicht werden.
- Entscheidung: MQTT ist zentraler Transport- und Integrationskanal.
- Begründung: lose Kopplung, gute Beobachtbarkeit, standardisierte Weiterverarbeitung in Home Assistant.

## ADR-004: modbus-proxy vor Sungrow

- Status: Angenommen
- Kontext: Sungrow-Modbus-Verbindung zeigte in der Vergangenheit Empfindlichkeit.
- Entscheidung: `modbus-proxy` wird zwischen Inverter und Client(s) geschaltet.
- Begründung: Serialisierung und Stabilisierung von Modbus-Zugriffen; Schutz vor Konkurrenzzugriffen.

## ADR-005: InfluxDB nur auf NAS

- Status: Angenommen
- Kontext: Ursprünglich standen zwei InfluxDB-Instanzen (Pi + NAS) zur Diskussion.
- Entscheidung: Eine produktive InfluxDB auf dem NAS; direkte Writes/Reads über LAN.
- Begründung: geringere Komplexität, keine Replikationsverwaltung, klarer Datenspeicherort.
- Trade-off: Bei NAS-Ausfall pausiert Zeitreihenaufnahme temporär.

## ADR-006: Custom Code für Vallox, WeeWX und Meross

- Status: Angenommen
- Kontext: Für Vallox, WeeWX und Meross sind Anpassungen erforderlich, die nicht durch Standard-Images abgedeckt sind.
- Entscheidung:
  - Vallox: Eigene schlanke Python-Bridge (`vallox2mqtt`) mit Dockerfile
  - WeeWX: Custom Image basierend auf `felddy/weewx:latest` mit vorgeinstalliertem `gettext-base` und `weewx-mqtt-subscribe` sowie custom entrypoint für `envsubst`-Templating
  - Meross: Custom Image basierend auf meross2homie (https://github.com/Depau/meross2homie)
    mit eigenem entrypoint.sh (auto-Discovery beim Start) und discover.py
    (einmaliger Cloud-Login zur UUID/Key-Ermittlung)
- Begründung:
  - Vallox: Kein etabliertes Standard-Image für Vallox->MQTT in dieser Zielarchitektur; einheitliche Datenführung über MQTT, volle Kontrolle über Topics und Polling
  - WeeWX: MQTT-Subscribe-Erweiterung nicht über PyPI verfügbar, muss aus GitHub installiert werden; envsubst-Templating vereinfacht Konfiguration; Custom Image reduziert Container-Startzeit durch vorgeinstallierte Abhängigkeiten
  - Meross: meross2homie bietet Homie-konforme MQTT-Topics; custom entrypoint ermöglicht automatische UUID/Key-Discovery beim ersten Start ohne manuelle Konfiguration

## ADR-007: Externe Erreichbarkeit strikt minimieren

- Status: Angenommen
- Kontext: Sicherheit und Datenschutz haben hohe Priorität.
- Entscheidung: Nur funktional notwendige UIs werden über Traefik publiziert; interne Integrationsdienste bleiben intern.
- Begründung: kleinere Angriffsoberfläche, klare Trennung von Datenebene und Zugriffsebene.

## ADR-008: Authentik für alle internet-erreichbaren Oberflächen

- Status: Angenommen
- Kontext: Einheitliches SSO und Zugriffsmanagement bereits im Einsatz.
- Entscheidung: `home.schubs.net` und `cockpit.schubs.net` hinter Authentik.
- Begründung: konsistente Sicherheitspolitik, zentrale Identitätsverwaltung.

## ADR-009: Blink als akzeptierte Cloud-Ausnahme

- Status: Angenommen
- Kontext: Blink bietet keine vollwertige lokale API.
- Entscheidung: Einbindung über Home Assistant Blink-Integration trotz Cloud-Abhängigkeit.
- Begründung: vorhandene Hardware soll weitergenutzt werden; Cloud-Anteil ist auf diesen Teilbereich begrenzt und transparent dokumentiert.

## ADR-010: Wetterdaten mit WeeWX an mehrere Dienste veröffentlichen

- Status: Angenommen
- Kontext: Wetterdaten aus Ecowitt sollen kostenlos und vertrauenswürdig geteilt werden, mit besonderem Fokus auf den deutschsprachigen Raum.
- Entscheidung: WeeWX wird als Weiterleitungs-Hub eingesetzt; Zielplattformen sind AWEKAS, Windy.com, Weather Underground, CWOP/APRS und OpenWeatherMap.
- Begründung: Entkopplung zwischen lokalem Smart-Home-Pfad und externer Veröffentlichung, flexible Mehrfach-Uploads, etablierte Open-Source-Komponente.

## ADR-011: Hybride Meross-Integration (HA-Kontrolle + Cloud-MQTT-Metriken)

- Status: Angenommen (aktualisiert: Cloud-Anbindung statt lokaler DNS-Interception)
- Kontext: Vier Meross-Einzelsteckdosen (2x MSS310, 2x MSS315) sollen in die Energieauswertung einfließen. Ziel ist direkter Metrik-Flow zu InfluxDB ohne HA als Middleman, während HA die Steuerung behält. DNS-Interception (ADR-015) wurde verworfen, da sie die Meross App (Remote-Steuerung, Firmware-Updates) blockiert und dnsmasq als Single-Point-of-Failure fuer das gesamte Heimnetz fungiert.
- Entscheidung: Dual-Path-Integration:
  - Steuerung/Automatisierung: `meross_lan` in Home Assistant
  - Energiemetriken: `meross2mqtt` (Cloud-Anbindung via `meross_iot.MerossManager`) → Mosquitto → Telegraf → InfluxDB
- Anbindung: `meross2mqtt` verbindet sich dauerhaft zur Meross Cloud und liest Energiemetriken (Spannung, Strom, Leistung, Tages- und Gesamtverbrauch) per Polling. Die Bridge ist rein lesend; Steuerung erfolgt ausschliesslich ueber `meross_lan` in HA.
- Begründung: Kein Eingriff in die Netzwerkinfrastruktur (kein dnsmasq, kein TLS-Trick). Meross App bleibt vollstaendig nutzbar (Remote-Steuerung, Firmware-Updates). Metriken fliessen weiterhin direkt NAS → InfluxDB ohne HA als Middleman. Einziger Trade-off: Metrik-Pfad haengt von Meross Cloud-Verfuegbarkeit ab.

## ADR-012: Energieflüsse doppelt visualisieren (HA + Grafana Sankey)

- Status: Angenommen
- Kontext: Gewünscht ist eine grafische Darstellung der Energieflüsse aller relevanten Geräte und Sensordaten.
- Entscheidung: Home Assistant Energy Dashboard für operative Sicht und Grafana Sankey-Diagramm für detaillierte Flussvisualisierung.
- Begründung: Kombination aus einfacher Tagesansicht und tiefer Analyse, ohne auf ein einziges Frontend beschränkt zu sein.

## ADR-013: Sungrow-Integration als off-the-shelf Image

- Status: Angenommen
- Kontext: Für Sungrow SH8.0RT existiert ein etabliertes Community-Image `bohdan0/sungrow2mqtt`. Eine custom Bridge wurde prototypisch entwickelt und getestet.
- Entscheidung: Verwendet wird das off-the-shelf Image `bohdan0/sungrow2mqtt`. Die custom Bridge in `bridges/sungrow2mqtt/` wird archiviert für potenzielle spätere Verwendung.
- Begründung: ADR-006 beschränkt custom Code auf vallox2mqtt. Für Sungrow steht ein funktionierendes Standard-Image zur Verfügung, das Wartungsaufwand minimiert und Community-Support bietet. Die custom Bridge bleibt als Referenz verfügbar.

## ADR-014: NAS-zentrierte Service-Verteilung

- Status: Angenommen
- Kontext: Ugreen NAS (Intel N100, 8GB RAM) bietet deutlich mehr Rechenleistung als Raspberry Pi 4. Alle Geräte befinden sich im selben LAN mit statischen IPs.
- Entscheidung:
  - **NAS (192.168.178.163)**: Mosquitto, alle MQTT-Bridges, WeeWX, Telegraf, InfluxDB
  - **Pi (192.168.178.69, Coolify)**: Home Assistant, Grafana, Traefik, Authentik (nur öffentlich zugängliche Dienste)
- Begründung:
  - NAS-Hardware leistungsstärker für Integrationsdienste und Datensammlung
  - Zentralisierung von MQTT-Bus und Zeitreihen-Verarbeitung auf NAS reduziert Netzwerkverkehr
  - Pi wird zu leichtem Reverse-Proxy-Host für öffentliche Exposition
  - Home Assistant auf Pi kommuniziert über LAN mit MQTT-Broker auf NAS
  - Trennung von Datenebene (NAS) und Zugriffsebene (Pi) bleibt gewahrt
- Trade-off:
  - Bei NAS-Ausfall fallen alle Integrationsdienste aus (MQTT, Bridges, Telegraf)
  - Home Assistant bleibt lokal bedienbar, verliert aber MQTT-Daten-Feed
  - Erhöhte Netzwerklatenz zwischen HA (Pi) und MQTT (NAS) im Vergleich zu lokaler Deployment-Option

## ADR-015: DNS-Interception für Meross via dnsmasq

- Status: Abgelöst durch ADR-011 (Cloud-Anbindung)
- Kontext: Urspruenglich sollte dnsmasq iot.meross.com auf den NAS umleiten, damit Meross-Geraete den lokalen Mosquitto-Broker nutzen.
- Grund fuer Abloesung:
  - FritzBox 7590 AX unterstuetzt nur einen einzigen DNS-Server (kein Sekundaer-DNS-Fallback moeglich).
  - Globaler DNS-Override blockiert die Meross App vollstaendig (kein Remote-Zugriff, keine Firmware-Updates).
  - dnsmasq als Single-Point-of-Failure fuer das gesamte Heimnetz ist nicht akzeptabel.
- Nachfolger: ADR-011 (aktualisiert) — Cloud-Anbindung via `meross_iot.MerossManager`.
