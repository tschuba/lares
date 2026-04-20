# Umsetzungsplan

Dieses Dokument beschreibt die schrittweise Implementierung von Lares basierend auf den dokumentierten Architekturentscheidungen.

## Inhaltsverzeichnis

- [Prinzipien](#prinzipien)
- [Phase 1: Infrastruktur-Grundlage (NAS-zentriert per ADR-014)](#phase-1-infrastruktur-grundlage-nas-zentriert-per-adr-014)
- [Phase 2: Modbus-Proxy und Sungrow-Integration (auf NAS)](#phase-2-modbus-proxy-und-sungrow-integration-auf-nas)
- [Phase 3: Vallox Custom Bridge (auf NAS)](#phase-3-vallox-custom-bridge-auf-nas)
- [Phase 4: Weitere Bridges (auf NAS)](#phase-4-weitere-bridges-auf-nas)
- [Phase 5: Lokale Integrationen (auf Pi via Coolify)](#phase-5-lokale-integrationen-auf-pi-via-coolify)
- [Phase 6: InfluxDB-Integration und Grafana](#phase-6-influxdb-integration-und-grafana)
- [Phase 7: Home Assistant Externe Erreichbarkeit (auf Pi via Coolify)](#phase-7-home-assistant-externe-erreichbarkeit-auf-pi-via-coolify)
- [Phase 8: Finalisierung und Dokumentation](#phase-8-finalisierung-und-dokumentation)
- [Abhängigkeiten und Reihenfolge](#abhängigkeiten-und-reihenfolge)
- [Risiken und Offene Punkte](#risiken-und-offene-punkte)
- [Zeitplan (Rough Estimate)](#zeitplan-rough-estimate)
- [Status](#status)

## Prinzipien

- **Phasenbasiert**: Jede Phase baut auf der vorherigen auf
- **Testbar**: Nach jeder Phase ist ein lauffähiges Teilsystem vorhanden
- **Dokumentiert**: Alle Änderungen werden in den entsprechenden Docs nachgeführt
- **ADR-konform**: Entscheidungen folgen den festgelegten ADRs

## Phase 1: Infrastruktur-Grundlage (NAS-zentriert per ADR-014)

**Ziel**: Laufzeitumgebung und Netzwerkstruktur auf NAS erstellen

### 1.1 Docker-Netzwerk `lares` auf NAS erstellen
- Docker-Netzwerk `lares` auf NAS anlegen (192.168.178.163)
- Netzwerk in `docker-compose.yml` definiert (Subnet 172.20.0.0/16)

### 1.2 Mosquitto MQTT Broker auf NAS部署
- Offizieller Container: `eclipse-mosquitto`
- Konfiguration: interne Kommunikation nur im `lares`-Netz
- Authentifizierung: Username/Password (siehe Inventar-Platzhalter)
- Persistenz: Konfiguration und retainierte Messages
- Test: MQTT-Verbindung aus einem anderen Container verifizieren

### 1.3 InfluxDB auf NAS部署
- Container auf NAS: `influxdb:2`
- Initialisierung: Organisation, Bucket, Token
- Netzwerk: nur LAN-intern erreichbar
- Test: Schreib/Lese-Zugriff vom Pi aus verifizieren

**Abnahmekriterien Phase 1**:
- [ ] Docker-Netzwerk `lares` auf NAS existiert
- [ ] Mosquitto auf NAS läuft und ist im `lares`-Netz erreichbar
- [ ] InfluxDB auf NAS läuft und akzeptiert Verbindungen vom Pi
- [ ] Platzhalter-Werte sind definiert oder durch echte Werte ersetzt

## Phase 2: Modbus-Proxy und Sungrow-Integration (auf NAS)

**Ziel**: Erste Datenquelle (Sungrow Inverter) anbinden

### 2.1 modbus-proxy auf NAS部署
- Image: `ghcr.io/tiagocoutinho/modbus-proxy`
- Konfiguration: Sungrow-IP als Ziel, Port 502
- Netzwerk: `lares` auf NAS
- Test: Proxy erreichbar, leitet Anfragen weiter

### 2.2 sungrow2mqtt Bridge auf NAS部署
- Image: `bohdan0/sungrow2mqtt` (gemäß ADR-013)
- Konfiguration: Modbus-Proxy als Quelle, Mosquitto als Ziel
- Topic-Struktur: `energy/sungrow/...`
- Test: MQTT-Topics mit Daten füllen

### 2.3 Home Assistant Konfiguration (auf Pi via Coolify)
- MQTT-Integration konfigurieren (Broker: NAS IP 192.168.178.163)
- Sungrow-Entities in Energy Dashboard aufnehmen
- Test: Daten in HA sichtbar

**Abnahmekriterien Phase 2**:
- [ ] modbus-proxy auf NAS läuft und ist erreichbar
- [ ] sungrow2mqtt auf NAS publiziert Daten im MQTT
- [ ] Home Assistant auf Pi zeigt Sungrow-Daten an
- [ ] Energieflüsse im HA Energy Dashboard sichtbar

## Phase 3: Vallox Custom Bridge (auf NAS)

**Ziel**: Custom Python-Bridge für Vallox Lüftung erstellen (ADR-006)

### 3.1 Vallox API analysieren
- HTTP API auf Port 80 dokumentieren
- Relevante Endpunkte identifizieren
- Test-Setup mit echtem Gerät

### 3.2 vallox2mqtt Bridge implementieren
- Projektstruktur in `bridges/vallox/` erstellen
- Python-Module: API-Client, MQTT-Publisher, Main
- Dockerfile erstellen
- Unit-Tests schreiben
- Konfigurations-Schema definieren

### 3.3 Deployment und Test auf NAS
- Container im `lares`-Netz auf NAS部署
- MQTT-Topics: `ventilation/vallox/...`
- Integration in HA (auf Pi)
- Test: Lüftungsdaten in HA sichtbar

**Abnahmekriterien Phase 3**:
- [ ] vallox2mqtt Bridge auf NAS läuft als Container
- [ ] Vallox-Daten werden im MQTT auf NAS publiziert
- [ ] Home Assistant auf Pi zeigt Lüftungsdaten an
- [ ] Unit-Tests bestehen

## Phase 4: Weitere Bridges (auf NAS)

**Ziel**: Verbleibende Geräte anbinden

### 4.1 luxtronik2mqtt (Novelan Wärmepumpe) auf NAS
- Off-the-shelf Lösung evaluieren
- Deployment im `lares`-Netz auf NAS
- Topic-Struktur: `heating/novelan/...`
- HA-Integration auf Pi

### 4.2 ecowitt2mqtt (Wetterstation) auf NAS
- Image: `bachya/ecowitt2mqtt`
- Port 4004 im `lares`-Netz auf NAS exposed
- Ecowitt-Konfiguration anpassen
- Topic-Struktur: `weather/ecowitt/...`
- HA-Integration auf Pi

### 4.3 WeeWX auf NAS部署 (Wetterdaten-Upload)
- Image: `felddy/weewx`
- Konfiguration für externe Dienste (AWEKAS, Windy, WU, CWOP, OWM)
- Ecowitt-Daten parallel zu ecowitt2mqtt an WeeWX leiten
- Test: Upload an externe Dienste verifizieren

**Abnahmekriterien Phase 4**:
- [ ] Novelan-Daten im MQTT auf NAS und HA auf Pi sichtbar
- [ ] Wetterdaten im MQTT auf NAS und HA auf Pi sichtbar
- [ ] WeeWX auf NAS lädt Daten an externe Dienste hoch
- [ ] Alle Geräte-Integrationen funktionieren

## Phase 5: Lokale Integrationen (auf Pi via Coolify)

**Ziel**: Geräte ohne Bridge direkt in HA integrieren

### 5.1 BambuLab P1S
- HA Bambu-Integration auf Pi konfigurieren
- Test: Druckerstatus in HA sichtbar

### 5.2 Meross Steckdosen (meross_lan)
- HA `meross_lan` Integration auf Pi konfigurieren
- 4 Steckdosen einbinden
- Energiemesswerte verifizieren
- Zuordnung zu Geräten (BambuLab, Arbeitstisch, Waschmaschine, Trockner)

### 5.3 Blink Kameras
- HA Blink-Integration auf Pi konfigurieren
- Cloud-API-Verbindung testen
- Test: Kamera-Bilder in HA sichtbar

### 5.4 Alexa/Echo Geräte
- HA `alexa_media_player` Integration auf Pi konfigurieren
- Test: Echo-Geräte in HA steuerbar

**Abnahmekriterien Phase 5**:
- [ ] BambuLab in HA auf Pi integriert
- [ ] Alle Meross-Steckdosen mit Energiemessung in HA auf Pi
- [ ] Blink-Kameras in HA auf Pi sichtbar
- [ ] Echo-Geräte über HA auf Pi steuerbar

## Phase 6: InfluxDB-Integration und Grafana

**Ziel**: Langzeitspeicherung und Visualisierung

### 6.1 InfluxDB-Integration in HA (auf Pi)
- InfluxDB-Integration in HA auf Pi konfigurieren (InfluxDB auf NAS: 192.168.178.163)
- Relevante Sensoren auswählen (Energie, Wetter, Lüftung, Heizung)
- Schreibintervall definieren (z.B. alle 5 Minuten)
- Test: Daten in InfluxDB auf NAS sichtbar

### 6.2 Grafana部署 (auf Pi via Coolify)
- Image: `grafana/grafana`
- Netzwerke: Traefik-Netz auf Pi
- InfluxDB auf NAS als DataSource konfigurieren
- Dashboard erstellen:
  - Energie-Übersicht
  - Wetter-Trends
  - Lüftungs-Status
  - Heizungs-Verbrauch

### 6.3 Sankey-Diagramm (ADR-012)
- Sankey-Panel für Grafana auf Pi einrichten
- Energieflüsse konfigurieren:
  - PV-Erzeugung
  - Batterie (Laden/Entladen)
  - Netzbezug/Einspeisung
  - Wärmepumpe
  - Meross-Lasten

### 6.4 Traefik + Authentik Konfiguration (auf Pi)
- `cockpit.schubs.net` für Grafana
- Authentik vorschalten
- Test: Grafana über Internet mit Authentik erreichbar

**Abnahmekriterien Phase 6**:
- [ ] HA auf Pi schreibt Daten in InfluxDB auf NAS
- [ ] Grafana auf Pi läuft und zeigt Daten an
- [ ] Sankey-Diagramm funktioniert
- [ ] Grafana auf Pi über `cockpit.schubs.net` mit Authentik erreichbar

## Phase 7: Home Assistant Externe Erreichbarkeit (auf Pi via Coolify)

**Ziel**: HA über Internet mit Authentik erreichbar machen

### 7.1 Traefik-Konfiguration für HA (auf Pi)
- `home.schubs.net` Route konfigurieren
- HA-Container in Traefik-Netz auf Pi einbinden
- Test: HA über Traefik erreichbar

### 7.2 Authentik-Integration (auf Pi)
- HA hinter Authentik schalten
- SSO-Konfiguration
- Test: HA über `home.schubs.net` mit Authentik erreichbar

**Abnahmekriterien Phase 7**:
- [ ] HA auf Pi über `home.schubs.net` erreichbar
- [ ] Authentik-Schutz aktiv
- [ ] SSO funktioniert

## Phase 8: Finalisierung und Dokumentation

**Ziel**: System stabilisieren und dokumentieren

### 8.1 Compose-Dateien finalisieren
- Alle Services in `docker-compose.yml` auf NAS konsolidiert
- Environment-Variablen in `config/.env` zentralisieren
- Deployment-Anleitung in `COOLIFY.md` finalisieren

### 8.2 Dokumentation aktualisieren
- `docs/inventar.md`: Platzhalter durch echte Werte ersetzen
- `README.md`: Status auf "Produktiv" aktualisieren
- `docs/architektur.md`: Aktuelle Netzwerk-Topologie (NAS-zentriert) dokumentieren
- Betriebsanleitung erstellen

### 8.3 Backup-Strategie
- InfluxDB-Backups auf NAS
- HA-Konfiguration auf Pi sichern
- Restore-Prozess dokumentieren

### 8.4 Monitoring
- Health-Checks für alle Services auf NAS
- Alarmierung bei Ausfällen
- Log-Zentralisierung

**Abnahmekriterien Phase 8**:
- [ ] Alle Services über `docker-compose.yml` auf NAS startbar
- [ ] Dokumentation vollständig und aktuell
- [ ] Backups laufen automatisch
- [ ] Monitoring aktiv

## Abhängigkeiten und Reihenfolge

```
Phase 1 (Infrastruktur)
  ↓
Phase 2 (Sungrow)
  ↓
Phase 3 (Vallox)
  ↓
Phase 4 (Weitere Bridges)
  ↓
Phase 5 (Lokale Integrationen)
  ↓
Phase 6 (InfluxDB + Grafana)
  ↓
Phase 7 (HA Extern)
  ↓
Phase 8 (Finalisierung)
```

**Kritische Pfade**:
- Phase 1 muss vollständig abgeschlossen sein, bevor Phase 2 starten kann
- Phase 6 benötigt Phase 2-5 für Datenquellen
- Phase 7 benötigt Phase 6 für Grafana, kann aber parallel zu Phase 5 erfolgen

## Risiken und Offene Punkte

1. **Sungrow Bridge**: Entscheidung zwischen off-the-shelf und custom Bridge noch offen
2. **Vallox API**: Doku verfügbar? Test-Setup nötig?
3. **Luxtronik2**: Off-the-shelf Lösung evaluiert?
4. **Netzwerk-Isolation**: `lares`-Netz vs. Traefik-Netz sauber getrennt?
5. **Backup/Restore**: InfluxDB-Backup-Strategie definiert?

## Zeitplan (Rough Estimate)

- Phase 1: 1-2 Tage
- Phase 2: 2-3 Tage
- Phase 3: 3-5 Tage (custom Entwicklung)
- Phase 4: 2-3 Tage
- Phase 5: 1-2 Tage
- Phase 6: 3-4 Tage
- Phase 7: 1-2 Tage
- Phase 8: 2-3 Tage

**Gesamt**: 15-24 Tage (abhängig von Erfahrungsgrad und Test-Setup)

## Status

- **Erstellt**: 2026-04-18
- **Aktualisiert**: 2026-04-19 (ADR-014: NAS-zentrierte Architektur)
- **Phase**: Implementierung
- **Phase 1-4**: Dokumentation und `docker-compose.yml` auf NAS fertiggestellt
- **Phase 5**: Dokumentation fertiggestellt, manuelle HA-Konfiguration auf Pi erforderlich
- **Phase 6**: Dokumentation fertiggestellt, manuelle Konfiguration erforderlich
- **Phase 7**: Dokumentation fertiggestellt, manuelle Konfiguration erforderlich
- **Phase 8**: Dokumentation fertiggestellt, manuelle Konfiguration erforderlich
- **Nächster Schritt**: Phase 8 manuell durchführen (Finalisierung, Backup, Monitoring)
