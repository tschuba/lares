## ADDED Requirements

### Requirement: MQTT-Command-Subscription für externe Profilsteuerung

Das System SHALL das Topic `ventilation/vallox/command/profile` abonnieren und eingehende JSON-Payloads als Profilbefehle verarbeiten.

#### Scenario: Einfacher Profilbefehl

- **WHEN** `{"profile": "boost"}` auf dem Command-Topic eintrifft
- **THEN** wechselt das System zu Profil BOOST und kehrt nach VENTILATION_HOLD_MINUTES automatisch zur internen Logik zurück

#### Scenario: Profilbefehl mit Lock

- **WHEN** `{"profile": "away", "lock": true}` eintrifft
- **THEN** wechselt das System zu AWAY und suspendiert die interne Automatisierung bis ein `{"profile": "auto"}` Befehl eintrifft

#### Scenario: Profilbefehl mit expliziter Dauer

- **WHEN** `{"profile": "boost", "duration": 120}` eintrifft
- **THEN** wechselt das System zu BOOST für 120 Minuten, danach Rückkehr zur internen Logik

#### Scenario: Auto-Befehl reaktiviert interne Logik

- **WHEN** `{"profile": "auto"}` eintrifft
- **THEN** wird eine aktive Lock-Sperre aufgehoben und die interne Temperaturautomatisierung sofort wieder aktiviert

#### Scenario: Ungültiger Befehl wird ignoriert

- **WHEN** ein nicht-JSON-Payload oder ein unbekannter Profilname eintrifft
- **THEN** wird der Befehl geloggt und verworfen, das aktuelle Profil bleibt unverändert

### Requirement: Gültige Profilwerte

Das System SHALL die Werte `home`, `away`, `boost`, `extra` und `auto` als gültige `profile`-Felder akzeptieren (Groß-/Kleinschreibung ignoriert).

#### Scenario: Bekannter Profilwert wird ausgeführt

- **WHEN** `{"profile": "home"}` eintrifft
- **THEN** wechselt das System zum HOME-Profil
