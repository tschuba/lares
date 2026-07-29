## 1. Statemachine zusammenführen

- [ ] 1.1 Bestehende `HeatProtectionStateMachine` in `vallox2mqtt.py` zur einheitlichen `TemperatureStateMachine` umbenennen und Zustandstypen erweitern (IDLE, MONITORING, OVERRIDE, COOLING_DOWN)
- [ ] 1.2 Bedingungspriorität implementieren: Hitzeschutz → Sommer-Sperre → Sommer-Kühlung → Winter-Sparmodus → HOME
- [ ] 1.3 `MIN_TEMP_DELTA`-Prüfung vor Eintritt in MONITORING für BOOST-Bedingung einbauen
- [ ] 1.4 Separate Sustain- und Hold-Timer für Ventilationslogik einführen (`VENTILATION_SUSTAIN_MINUTES`, `VENTILATION_HOLD_MINUTES`)
- [ ] 1.5 Sensor-Ausfall-Handling: bei fehlendem Wert aktuelles Profil halten, kein Wechsel

## 2. Konfiguration

- [ ] 2.1 Neue Umgebungsvariablen auslesen: `VENTILATION_AUTOMATION_ENABLED`, `MIN_TEMP_DELTA`, `WINTER_THRESHOLD`, `VENTILATION_SUSTAIN_MINUTES`, `VENTILATION_HOLD_MINUTES`
- [ ] 2.2 `docker-compose.yml` um neue Env-Vars mit Defaults für den Vallox-Service erweitern
- [ ] 2.3 `COOLIFY.md` um neue Env-Vars dokumentieren

## 3. MQTT-Command-Subscription

- [ ] 3.1 MQTT-Subscription auf `ventilation/vallox/command/profile` im Bridge-Startup einrichten
- [ ] 3.2 JSON-Payload parsen: `profile`, optionale Felder `lock` und `duration`
- [ ] 3.3 `auto`-Befehl implementiert: Lock aufheben, interne Logik sofort reaktivieren
- [ ] 3.4 `lock: true`-Modus: interne Automatisierung suspendieren bis `auto` eintrifft
- [ ] 3.5 `duration`-Feld: explizite Dauer in Minuten an Vallox-API-Profil-Timer übergeben
- [ ] 3.6 Ungültige Payloads loggen und verwerfen ohne Bridge-Absturz

## 4. Pushover-Benachrichtigungen

- [ ] 4.1 `PUSHOVER_USER_KEY` und `PUSHOVER_API_TOKEN` aus Umgebung lesen; bei fehlendem Wert Warnung loggen und Benachrichtigungen überspringen
- [ ] 4.2 Nachrichtentexte in DE und EN als Dict implementieren (`NOTIFICATION_LANGUAGE`-Env-Var, Standard `de`)
- [ ] 4.3 Fire-and-forget HTTP POST zur Pushover-API bei automatischem Profilwechsel (nicht bei externem Command)
- [ ] 4.4 `VENTILATION_NOTIFICATION_ENABLED`-Flag prüfen vor jedem Sendeversuch
- [ ] 4.5 Netzwerkfehler nur loggen, kein Retry, Bridge-Loop nicht blockieren

## 5. Tests und Verifikation

- [ ] 5.1 Bestehende Unit-Tests in `bridges/vallox/tests/` auf umbenannte Statemachine anpassen
- [ ] 5.2 Tests für neue Bedingungsreihenfolge ergänzen (alle 5 Prioritätsstufen)
- [ ] 5.3 Test für Delta-Schwelle (kein BOOST bei Differenz < MIN_TEMP_DELTA)
- [ ] 5.4 Test für Sensor-Ausfall-Handling
- [ ] 5.5 Bridge lokal bauen und gegen echte Vallox-Instanz testen: Profilwechsel prüfen
