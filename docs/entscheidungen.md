# Architekturentscheidungen

Dieses Dokument hält die zentralen Entscheidungen für Lares mit kurzer Begründung fest.

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

## ADR-006: Vallox-Integration als custom MQTT-Bridge (Option A)

- Status: Angenommen
- Kontext: Kein etabliertes Standard-Image für Vallox->MQTT in dieser Zielarchitektur.
- Entscheidung: Eigene schlanke Python-Bridge (`vallox2mqtt`) mit Dockerfile.
- Begründung: Einheitliche Datenführung über MQTT, volle Kontrolle über Topics und Polling.

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

## ADR-011: Hybride Meross-Integration (HA-Kontrolle + MQTT-Metriken)

- Status: Angenommen
- Kontext: Vier Meross-Einzelsteckdosen (2x MSS310, 2x MSS315) sollen in die Energieauswertung einfließen. Ziel ist direkter Metrik-Flow zu InfluxDB ohne HA als Middleman, während HA die Steuerung behält.
- Entscheidung: Dual-Path-Integration:
  - Steuerung/Automatisierung: `meross_lan` in Home Assistant
  - Energiemetriken: `meross2mqtt` → Mosquitto → Telegraf → InfluxDB
- Begründung: HA behält bewährte Kontrolle, während Metriken direkt über MQTT-Bus in InfluxDB fließen (effizienter, reduziert Abhängigkeit von HA für reinen Datensammelpfad). Telegraf als offizielle InfluxData-Lösung gewährleistet Stabilität und Wartbarkeit.

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
