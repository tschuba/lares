## ADDED Requirements

### Requirement: Pushover-Benachrichtigung bei automatischem Profilwechsel

Das System SHALL bei jedem automatischen Profilwechsel eine Pushover-Benachrichtigung senden, wenn `VENTILATION_NOTIFICATION_ENABLED=true`.

#### Scenario: Benachrichtigung bei BOOST-Aktivierung

- **WHEN** das System automatisch auf BOOST wechselt
- **THEN** wird eine Pushover-Nachricht gesendet mit Profilname, Grund und aktuellen Temperaturwerten

#### Scenario: Benachrichtigung bei AWAY-Aktivierung

- **WHEN** das System automatisch auf AWAY wechselt
- **THEN** wird eine Pushover-Nachricht gesendet mit Profilname, Grund (z.B. Hitzeschutz, Sommer-Sperre oder Winter-Sparmodus) und aktuellen Temperaturwerten

#### Scenario: Keine Benachrichtigung bei externem Command

- **WHEN** ein Profilwechsel durch einen externen MQTT-Befehl ausgelöst wird
- **THEN** wird keine Pushover-Benachrichtigung gesendet (externer Auslöser kennt den Wechsel bereits)

#### Scenario: Netzwerkfehler blockiert nicht den Bridge-Loop

- **WHEN** die Pushover-API nicht erreichbar ist
- **THEN** wird der Fehler geloggt, kein Retry, und der Bridge-Betrieb wird nicht unterbrochen

### Requirement: Mehrsprachige Benachrichtigungen

Das System SHALL Benachrichtigungstexte in der via `NOTIFICATION_LANGUAGE` konfigurierten Sprache ausgeben (Standard: `de`).

#### Scenario: Deutsche Nachricht (Standard)

- **WHEN** `NOTIFICATION_LANGUAGE=de` (oder nicht gesetzt)
- **THEN** lautet eine BOOST-Benachrichtigung z.B. „Vallox → BOOST: Außenluft 19°C < Raumluft 26°C"

#### Scenario: Englische Nachricht

- **WHEN** `NOTIFICATION_LANGUAGE=en`
- **THEN** lautet eine BOOST-Benachrichtigung z.B. „Vallox → BOOST: outdoor 19°C < indoor 26°C"

### Requirement: Konfigurierbare Pushover-Zugangsdaten

Das System SHALL `PUSHOVER_USER_KEY` und `PUSHOVER_API_TOKEN` als Umgebungsvariablen auslesen.

#### Scenario: Fehlende Zugangsdaten deaktivieren Benachrichtigungen

- **WHEN** `PUSHOVER_USER_KEY` oder `PUSHOVER_API_TOKEN` nicht gesetzt sind
- **THEN** werden Benachrichtigungen übersprungen und eine Warnung geloggt
