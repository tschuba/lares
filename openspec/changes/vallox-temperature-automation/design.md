## Context

Der `vallox2mqtt`-Bridge enthält bereits eine Hitzeschutz-Statemachine, die bei zu warmer Zuluft auf AWAY schaltet. Diese Logik ist isoliert implementiert und nicht erweiterbar für weitere Temperaturszenarien. Die Vallox ValloPlus 350 MV-E hat Bypass (stufenlos, Enthalpie-basiert) und unterstützt die Profile HOME, AWAY, BOOST, EXTRA und FIREPLACE via Websocket-API. Alle relevanten Temperaturdaten (Zuluft, Raumluft, Außenluft, Solltemperatur) sind bereits im Poll-Zyklus des Bridges verfügbar.

## Goals / Non-Goals

**Goals:**
- Hitzeschutz und neue Temperaturlogik in eine einheitliche Statemachine zusammenführen
- Sommer-Kühlung: BOOST wenn Außenluft kühler als Raumluft und Raumluft über Sollwert
- Sommer-Sperre: AWAY wenn Außenluft wärmer als Raumluft und Raumluft über Sollwert
- Winter-Sparmodus: AWAY wenn Außenluft unter konfiguriertem Schwellwert
- MQTT-Command-Subscription für externe Steuerung mit lock/duration/auto-Optionen
- Pushover-Benachrichtigung bei Profilwechseln, unabhängig von Automatisierung konfigurierbar

**Non-Goals:**
- Steuerung externer Sensoren am Vallox-Eingang (physische Hardware)
- Änderung der Vallox-internen Einstellungen (Bypass-Modus, Temperatursteuerungsmethode)
- Feuchtigkeits- oder CO₂-basierte Profilsteuerung (wird bereits vom Gerät intern gehandhabt)
- Raumspezifische Temperatursteuerung (nur Vallox Raumluft-Sensor verfügbar)

## Decisions

### Einheitliche Statemachine statt paralleler Logiken

**Entscheidung:** Bestehende Hitzeschutz-Statemachine wird zur einheitlichen `TemperatureStateMachine` erweitert. Keine separate Klasse für Ventilationslogik.

**Begründung:** Hitzeschutz und Ventilationsoptimierung sind dasselbe Problem aus verschiedenen Perspektiven — beide entscheiden anhand von Temperaturdifferenzen ob mehr oder weniger Lüften sinnvoll ist. Zwei parallele Statemachines würden Konflikte erzeugen (wer gewinnt?) und doppelte Zustandsverwaltung erfordern.

**Alternativ betrachtet:** Arbitrator-Pattern (zwei Maschinen, ein Schiedsrichter) — verworfen wegen unnötiger Komplexität bei diesem Problemraum.

### Bedingungsreihenfolge (Priorität)

```
1. Zuluft > Raumluft                                    → AWAY  (Hitzeschutz, sofortige Gefahr)
2. Außenluft > Raumluft AND Raumluft > Sollwert         → AWAY  (Sommer-Sperre)
3. Außenluft < Raumluft AND delta > MIN_TEMP_DELTA
   AND Raumluft > Sollwert                              → BOOST (Sommer-Kühlung)
4. Außenluft < WINTER_THRESHOLD                         → AWAY  (Winter-Sparmodus)
5. sonst                                                → HOME
```

**Begründung:** Hitzeschutz (1) hat höchste Priorität, da die Anlage aktiv schadet. Sommer-Sperre (2) verhindert unnötiges Einbringen von Wärme. Kühlung (3) nur wenn echter Delta vorhanden (MIN_TEMP_DELTA verhindert Schalten bei Messrauschen). Winter (4) ist passiv/energetisch, daher niedrigste Priorität.

### Hysterese: zwei Schichten

- **Delta-Schwelle** (`MIN_TEMP_DELTA`, Standard 2.0°C): Bedingung muss bedeutsam sein, bevor MONITORING beginnt
- **Sustain-Timer** (`VENTILATION_SUSTAIN_MINUTES`, Standard 15 min): Bedingung muss stabil anliegen vor Profilwechsel
- **Hold-Timer** (`VENTILATION_HOLD_MINUTES`, Standard 30 min): Profil bleibt mindestens so lange aktiv

Hitzeschutz behält eigene Timer-Defaults (`HEAT_SUSTAIN_MINUTES=30`, `HEAT_MIN_OVERRIDE_MINUTES=60`) für Rückwärtskompatibilität.

### MQTT-Command-Payload: JSON

```json
{"profile": "boost"}                      // auto-resume nach hold time
{"profile": "away", "lock": true}         // manuell bis auto
{"profile": "boost", "duration": 120}     // explizite Dauer in Minuten
{"profile": "auto"}                       // interne Logik reaktivieren
```

**Begründung:** JSON ist HA-freundlich, erweiterbar ohne Breaking Change, und erlaubt optionale Felder ohne Trennzeichen-Parsing.

### Pushover direkt aus Bridge-Prozess

**Entscheidung:** HTTP POST zur Pushover-API direkt aus `vallox2mqtt.py` via `aiohttp` (bereits in der Python-Umgebung verfügbar durch andere Deps).

**Begründung:** Grafana-Pushover-Integration ist für Metrikalerts gedacht, nicht für Bridge-Ereignisse. Eine direkte HTTP-Anfrage aus dem Bridge-Prozess ist einfacher als eine MQTT-Nachricht an Grafana-Alerting zu routen.

**Alternativ:** Notification via MQTT-Topic → Home Assistant → Pushover. Verworfen: unnötige Kopplung, Latenz, und HA-seitige Automation-Pflege.

### Sensor-Ausfall: Hold-Strategie

Bei fehlendem oder veralteten Sensor-Wert: aktuelles Profil halten (kein Wechsel). Keine Fallback-Profile, da der sichere Zustand "nichts ändern" ist.

## Risks / Trade-offs

- **Einzelner Innentemperatur-Sensor** → Messwert repräsentiert nur die Umgebung des Lüftungsgeräts, nicht den wärmsten Raum. Mitigation: akzeptiert; bessere Abdeckung erfordert zusätzliche Hardware.
- **BOOST mit Vallox-Timer** → nach Timer-Ablauf schaltet Gerät intern auf HOME; Bridge erkennt dies im nächsten Poll und evaluiert neu. Kein explizites Revert nötig, aber kurze Inkonsistenz (max. 1 Poll-Intervall). Mitigation: akzeptiert.
- **Pushover-Direktaufruf aus Bridge** → Netzwerkfehler blockiert Bridge-Loop nicht (fire-and-forget mit Timeout). Mitigation: Fehler nur geloggt, kein Retry.
- **AWAY im Winter bei tatsächlichem Lüftungsbedarf** (CO₂, Feuchtigkeit) → Vallox-interne CO₂/RH-Logik kann AWAY überschreiben. Mitigation: Geräteinterne Logik hat Vorrang vor Bridge-Profil in diesem Fall — vertretbar.

## Migration Plan

1. Neue Umgebungsvariablen mit Defaults — keine bestehende Konfiguration bricht
2. Bestehende `HEAT_SUSTAIN_MINUTES` / `HEAT_MIN_OVERRIDE_MINUTES` bleiben erhalten
3. Deploy via normalem Bridge-Update (Docker image rebuild + compose up)
4. Rollback: vorherige Image-Version, keine Datenbankänderungen
