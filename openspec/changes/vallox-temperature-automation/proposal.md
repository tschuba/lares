## Why

Die Vallox-Lüftungsanlage läuft derzeit mit einem festen Profil ohne Rücksicht auf die Temperaturdifferenz zwischen Innen- und Außenluft. Im Sommer wird dadurch warme Außenluft eingebracht, die das Haus unnötig aufheizt; im Winter wird bei eiskalter Außenluft zu viel Wärme abgeführt. Eine temperaturbasierte Automatisierung nutzt die vorhandenen Sensordaten der Anlage, um das Profil situationsgerecht anzupassen und Komfort sowie Energieeffizienz zu verbessern.

## What Changes

- Bestehende Hitzeschutz-Statemachine in `bridges/vallox/vallox2mqtt.py` wird zu einer einheitlichen Temperatur-Statemachine erweitert
- Neue Profilentscheidungslogik mit fünf priorisierten Bedingungen (Hitzeschutz, Sommer-Sperre, Sommer-Kühlung, Winter-Sparmodus, Normal)
- MQTT-Command-Topic `ventilation/vallox/command/profile` mit JSON-Payload für externe Steuerung (Home Assistant)
- Pushover-Benachrichtigungen bei Profilwechseln, optional und unabhängig von der Automatisierung konfigurierbar
- Neue Umgebungsvariablen für Schwellwerte, Sprache und Feature-Flags

## Capabilities

### New Capabilities

- `vallox-temperature-automation`: Einheitliche temperaturbasierte Profilsteuerung (HOME / AWAY / BOOST) basierend auf Zuluft-, Raumluft-, Außenluft- und Solltemperatur mit Hysterese
- `vallox-mqtt-command`: MQTT-Command-Subscription für externe Profilsteuerung mit JSON-Optionen (lock, duration, auto)
- `vallox-pushover-notification`: Pushover-Benachrichtigung bei automatischen Profilwechseln, mehrsprachig (DE/EN)

### Modified Capabilities

- `vallox-bridge`: Bestehende Hitzeschutzlogik wird in die neue einheitliche Statemachine integriert (Verhaltensänderung: zusätzliche Profile BOOST und AWAY aus neuen Bedingungen)

## Impact

- `bridges/vallox/vallox2mqtt.py`: Hauptänderung — Statemachine-Erweiterung, MQTT-Subscription, Notification-Logik
- `docker-compose.yml`: Neue Umgebungsvariablen für den Vallox-Service
- `COOLIFY.md`: Dokumentation der neuen Env-Vars
- Externe Abhängigkeit: Pushover API (bereits via Grafana genutzt, hier direkt aus dem Bridge-Prozess)
- Keine neuen Python-Pakete erforderlich (paho-mqtt bereits vorhanden; Pushover via HTTP mit `aiohttp` oder `requests`)
