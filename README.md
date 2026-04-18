# Lares

Lares ist die Smart-Home-Zentrale für das Zuhause auf `schubs.net`.

Der Name ist absichtlich mit einem Augenzwinkern gewählt: In der römischen Hausreligion waren die *Lares* Schutzgottheiten des Heims. Sie galten als stille, stets anwesende Begleiter, die über Haus und Familie wachen. Genau diese Rolle übernimmt das Projekt: Daten sammeln, Technik koordinieren und den Betrieb sichern, ohne im Alltag störend in Erscheinung zu treten.

## Zielbild

- Geräte und Sensoren möglichst einheitlich per MQTT anbinden
- Daten zentral sammeln, validieren und in Dashboards visualisieren
- Automatisierungen lokal und robust in Home Assistant ausführen
- Internet-zugängliche Oberflächen über Traefik + Authentik schützen
- Langzeitdaten direkt auf dem NAS speichern

## Funktionale Subdomains

Die Subdomains sind absichtlich funktionsorientiert und nicht nach Tool-Namen benannt.

- `home.schubs.net`: Zentrale Bedien- und Automatisierungsebene (Home Assistant)
- `cockpit.schubs.net`: Messwerte, Trends und Betriebsübersicht (Grafana)

Begründung:

- `home` ist bereits etabliert und beschreibt die Hauptfunktion klar.
- `cockpit` signalisiert eine zentrale, instrumentenartige Übersicht aller wichtigen Kennzahlen.
- Die Benennung bleibt auch bei Toolwechsel stabil (z. B. falls Grafana später ersetzt wird).

## Dokumentation

- `docs/architektur.md`: Gesamtarchitektur inkl. Diagramm
- `docs/inventar.md`: Vollständiges Inventar (Geräte, Dienste, Ports, Netzwerke)
- `docs/entscheidungen.md`: Architekturentscheidungen mit Begründung

## Status

Aktueller Schwerpunkt ist Planungs- und Inventarphase. Implementierungsartefakte (Compose-Dateien, Bridge-Code, Konfigurationen) werden auf Basis der dokumentierten Entscheidungen schrittweise ergänzt.
