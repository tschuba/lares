# Umsetzungsplan

Dieses Dokument beschreibt die schrittweise Implementierung von Lares basierend auf den dokumentierten Architekturentscheidungen.

## Prinzipien

- **Phasenbasiert**: Jede Phase baut auf der vorherigen auf
- **Testbar**: Nach jeder Phase ist ein lauffähiges Teilsystem vorhanden
- **Dokumentiert**: Alle Änderungen werden in den entsprechenden Docs nachgeführt
- **ADR-konform**: Entscheidungen folgen den festgelegten ADRs

## Phase 1: Infrastruktur-Grundlage

**Ziel**: Laufzeitumgebung und Netzwerkstruktur erstellen

### 1.1 Docker-Netzwerk `lares` erstellen
- Docker-Netzwerk `lares` auf Raspberry Pi anlegen
- Konfiguration in `compose/network.yml` dokumentieren

### 1.2 Mosquitto MQTT Broker部署
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
- [ ] Docker-Netzwerk `lares` existiert
- [ ] Mosquitto läuft und ist im `lares`-Netz erreichbar
- [ ] InfluxDB läuft und akzeptiert Verbindungen vom Pi
- [ ] Platzhalter-Werte sind definiert oder durch echte Werte ersetzt

## Phase 2: Modbus-Proxy und Sungrow-Integration

**Ziel**: Erste Datenquelle (Sungrow Inverter) anbinden

### 2.1 modbus-proxy部署
- Image: `ghcr.io/tiagoutinho/modbus-proxy`
- Konfiguration: Sungrow-IP als Ziel, Port 502
- Netzwerk: `lares`
- Test: Proxy erreichbar, leitet Anfragen weiter

### 2.2 sungrow2mqtt Bridge部署
- Image: `bohdan0/sungrow2mqtt` (gemäß ADR-013)
- Konfiguration: Modbus-Proxy als Quelle, Mosquitto als Ziel
- Topic-Struktur: `energy/sungrow/...`
- Test: MQTT-Topics mit Daten füllen

### 2.3 Home Assistant Konfiguration
- MQTT-Integration konfigurieren
- Sungrow-Entities in Energy Dashboard aufnehmen
- Test: Daten in HA sichtbar

**Abnahmekriterien Phase 2**:
- [ ] modbus-proxy läuft und ist erreichbar
- [ ] sungrow2mqtt publiziert Daten im MQTT
- [ ] Home Assistant zeigt Sungrow-Daten an
- [ ] Energieflüsse im HA Energy Dashboard sichtbar

## Phase 3: Vallox Custom Bridge

**Ziel**: Custom Python-Bridge für Vallox Lüftung erstellen (ADR-006)

### 3.1 Vallox API analysieren
- TCP API auf Port 18080 dokumentieren
- Relevante Endpunkte identifizieren
- Test-Setup mit echtem Gerät

### 3.2 vallox2mqtt Bridge implementieren
- Projektstruktur in `bridges/vallox/` erstellen
- Python-Module: API-Client, MQTT-Publisher, Main
- Dockerfile erstellen
- Unit-Tests schreiben
- Konfigurations-Schema definieren

### 3.3 Deployment und Test
- Container im `lares`-Netz部署
- MQTT-Topics: `ventilation/vallox/...`
- Integration in HA
- Test: Lüftungsdaten in HA sichtbar

**Abnahmekriterien Phase 3**:
- [ ] vallox2mqtt Bridge läuft als Container
- [ ] Vallox-Daten werden im MQTT publiziert
- [ ] Home Assistant zeigt Lüftungsdaten an
- [ ] Unit-Tests bestehen

## Phase 4: Weitere Bridges

**Ziel**: Verbleibende Geräte anbinden

### 4.1 luxtronik2mqtt (Novelan Wärmepumpe)
- Off-the-shelf Lösung evaluieren
- Deployment im `lares`-Netz
- Topic-Struktur: `heating/novelan/...`
- HA-Integration

### 4.2 ecowitt2mqtt (Wetterstation)
- Image: `bachya/ecowitt2mqtt`
- Port 4004 im `lares`-Netz exposed
- Ecowitt-Konfiguration anpassen
- Topic-Struktur: `weather/ecowitt/...`
- HA-Integration

### 4.3 WeeWX部署 (Wetterdaten-Upload)
- Image: `felddy/weewx`
- Konfiguration für externe Dienste (AWEKAS, Windy, WU, CWOP, OWM)
- Ecowitt-Daten parallel zu ecowitt2mqtt an WeeWX leiten
- Test: Upload an externe Dienste verifizieren

**Abnahmekriterien Phase 4**:
- [ ] Novelan-Daten im MQTT und HA sichtbar
- [ ] Wetterdaten im MQTT und HA sichtbar
- [ ] WeeWX lädt Daten an externe Dienste hoch
- [ ] Alle Geräte-Integrationen funktionieren

## Phase 5: Lokale Integrationen

**Ziel**: Geräte ohne Bridge direkt in HA integrieren

### 5.1 BambuLab P1S
- HA Bambu-Integration konfigurieren
- Test: Druckerstatus in HA sichtbar

### 5.2 Meross Steckdosen (meross_lan)
- HA `meross_lan` Integration konfigurieren
- 4 Steckdosen einbinden
- Energiemesswerte verifizieren
- Zuordnung zu Geräten (BambuLab, Arbeitstisch, Waschmaschine, Trockner)

### 5.3 Blink Kameras
- HA Blink-Integration konfigurieren
- Cloud-API-Verbindung testen
- Test: Kamera-Bilder in HA sichtbar

### 5.4 Alexa/Echo Geräte
- HA `alexa_media_player` Integration konfigurieren
- Test: Echo-Geräte in HA steuerbar

**Abnahmekriterien Phase 5**:
- [ ] BambuLab in HA integriert
- [ ] Alle Meross-Steckdosen mit Energiemessung in HA
- [ ] Blink-Kameras in HA sichtbar
- [ ] Echo-Geräte über HA steuerbar

## Phase 6: InfluxDB-Integration und Grafana

**Ziel**: Langzeitspeicherung und Visualisierung

### 6.1 InfluxDB-Integration in HA
- InfluxDB-Integration in HA konfigurieren
- Relevante Sensoren auswählen (Energie, Wetter, Lüftung, Heizung)
- Schreibintervall definieren (z.B. alle 5 Minuten)
- Test: Daten in InfluxDB sichtbar

### 6.2 Grafana部署
- Image: `grafana/grafana`
- Netzwerke: `lares` + Traefik-Netz
- InfluxDB als DataSource konfigurieren
- Dashboard erstellen:
  - Energie-Übersicht
  - Wetter-Trends
  - Lüftungs-Status
  - Heizungs-Verbrauch

### 6.3 Sankey-Diagramm (ADR-012)
- Sankey-Panel für Grafana einrichten
- Energieflüsse konfigurieren:
  - PV-Erzeugung
  - Batterie (Laden/Entladen)
  - Netzbezug/Einspeisung
  - Wärmepumpe
  - Meross-Lasten

### 6.4 Traefik + Authentik Konfiguration
- `cockpit.schubs.net` für Grafana
- Authentik vorschalten
- Test: Grafana über Internet mit Authentik erreichbar

**Abnahmekriterien Phase 6**:
- [ ] HA schreibt Daten in InfluxDB
- [ ] Grafana läuft und zeigt Daten an
- [ ] Sankey-Diagramm funktioniert
- [ ] Grafana über `cockpit.schubs.net` mit Authentik erreichbar

## Phase 7: Home Assistant Externe Erreichbarkeit

**Ziel**: HA über Internet mit Authentik erreichbar machen

### 7.1 Traefik-Konfiguration für HA
- `home.schubs.net` Route konfigurieren
- HA-Container in Traefik-Netz einbinden
- Test: HA über Traefik erreichbar

### 7.2 Authentik-Integration
- HA hinter Authentik schalten
- SSO-Konfiguration
- Test: HA über `home.schubs.net` mit Authentik erreichbar

**Abnahmekriterien Phase 7**:
- [ ] HA über `home.schubs.net` erreichbar
- [ ] Authentik-Schutz aktiv
- [ ] SSO funktioniert

## Phase 8: Finalisierung und Dokumentation

**Ziel**: System stabilisieren und dokumentieren

### 8.1 Compose-Dateien erstellen
- Alle Services in `compose/` strukturieren
- Environment-Variablen zentralisieren
- Start-Stop-Skripte erstellen

### 8.2 Dokumentation aktualisieren
- `docs/inventar.md`: Platzhalter durch echte Werte ersetzen
- `README.md`: Status auf "Produktiv" aktualisieren
- `docs/architektur.md`: Aktuelle Netzwerk-Topologie dokumentieren
- Betriebsanleitung erstellen

### 8.3 Backup-Strategie
- InfluxDB-Backups auf NAS
- HA-Konfiguration sichern
- Restore-Prozess dokumentieren

### 8.4 Monitoring
- Health-Checks für alle Services
- Alarmierung bei Ausfällen
- Log-Zentralisierung

**Abnahmekriterien Phase 8**:
- [ ] Alle Services über Compose startbar
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
- **Phase**: Planung
- **Nächster Schritt**: Phase 1 starten
