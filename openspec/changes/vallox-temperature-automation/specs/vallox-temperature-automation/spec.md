## ADDED Requirements

### Requirement: Temperaturbasierte Profilentscheidung

Das System SHALL das aktive Vallox-Profil anhand einer priorisierten Bedingungsreihenfolge automatisch wählen, wenn `VENTILATION_AUTOMATION_ENABLED=true`.

#### Scenario: Hitzeschutz hat höchste Priorität

- **WHEN** Zuluft-Temperatur > Raumluft-Temperatur
- **THEN** wird Profil AWAY aktiviert, unabhängig von allen anderen Bedingungen

#### Scenario: Sommer-Sperre bei heißer Außenluft

- **WHEN** Außenluft-Temperatur > Raumluft-Temperatur AND Raumluft-Temperatur > Solltemperatur AND Hitzeschutz-Bedingung nicht erfüllt
- **THEN** wird Profil AWAY aktiviert

#### Scenario: Sommer-Kühlung bei kühler Außenluft

- **WHEN** Raumluft-Temperatur > Solltemperatur AND Raumluft-Temperatur − Außenluft-Temperatur > MIN_TEMP_DELTA
- **THEN** wird Profil BOOST aktiviert

#### Scenario: Winter-Sparmodus bei kalter Außenluft

- **WHEN** Außenluft-Temperatur < WINTER_THRESHOLD AND keine Sommer-Bedingung aktiv
- **THEN** wird Profil AWAY aktiviert

#### Scenario: Normalbetrieb

- **WHEN** keine der obigen Bedingungen zutrifft
- **THEN** wird Profil HOME aktiviert

### Requirement: Delta-Schwelle verhindert Schalten bei Messrauschen

Das System SHALL eine Temperaturänderung nur bewerten, wenn die Differenz zwischen Außen- und Raumluft mindestens `MIN_TEMP_DELTA` (Standard 2.0°C) beträgt.

#### Scenario: Zu geringe Differenz — kein Wechsel

- **WHEN** Außenluft-Temperatur < Raumluft-Temperatur AND die Differenz < MIN_TEMP_DELTA
- **THEN** wird kein BOOST ausgelöst und das aktuelle Profil bleibt erhalten

### Requirement: Zweistufige Hysterese

Das System SHALL einen Profilwechsel erst nach stabiler Bedingung über `VENTILATION_SUSTAIN_MINUTES` auslösen und das neue Profil mindestens `VENTILATION_HOLD_MINUTES` beibehalten.

#### Scenario: Kurze Temperaturschwankung löst keinen Wechsel aus

- **WHEN** eine Wechselbedingung kürzer als VENTILATION_SUSTAIN_MINUTES anliegt
- **THEN** wird kein Profilwechsel ausgelöst

#### Scenario: Profil bleibt mindestens HOLD-Zeit aktiv

- **WHEN** ein Profilwechsel ausgelöst wurde und die Bedingung vor Ablauf von VENTILATION_HOLD_MINUTES entfällt
- **THEN** bleibt das aktive Profil bis zum Ablauf von VENTILATION_HOLD_MINUTES bestehen

### Requirement: Sensor-Ausfall löst keinen Profilwechsel aus

Das System SHALL bei fehlendem oder veralteten Sensorwert das aktuelle Profil unverändert beibehalten.

#### Scenario: Fehlender Außenluft-Wert

- **WHEN** kein gültiger Außenluft-Temperaturwert verfügbar ist
- **THEN** verbleibt das System im aktuellen Profil ohne Änderung

### Requirement: Konfigurierbare Schwellwerte via Umgebungsvariablen

Das System SHALL folgende Umgebungsvariablen auswerten:

| Variable | Standard | Beschreibung |
|---|---|---|
| `VENTILATION_AUTOMATION_ENABLED` | `true` | Automatisierung ein/aus |
| `MIN_TEMP_DELTA` | `2.0` | Mindest-Temperaturdifferenz in °C |
| `WINTER_THRESHOLD` | `5.0` | Außenluft-Schwelle Winter-Sparmodus in °C |
| `VENTILATION_SUSTAIN_MINUTES` | `15` | Wartezeit vor Profilwechsel in Minuten |
| `VENTILATION_HOLD_MINUTES` | `30` | Mindesthaltedauer nach Profilwechsel in Minuten |

#### Scenario: Automatisierung deaktiviert

- **WHEN** `VENTILATION_AUTOMATION_ENABLED=false`
- **THEN** evaluiert das System keine Temperaturbedingungen und wechselt keine Profile automatisch
