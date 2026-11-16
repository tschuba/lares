# Multi-Arch (amd64, arm64) ab 1.0.1; Image wird für den Pi (arm64) benötigt.
# Daten-Image: nur Dashboards + Provisioning, kein Grafana. Läuft als Init-Container (ADR-020).
FROM busybox:1.37
COPY dashboards /src/dashboards
COPY provisioning /src/provisioning
# Ziel-Volumes leeren (gelöschte Dashboards entfernen), dann Inhalt kopieren
CMD ["sh", "-c", "set -e; for d in dashboards provisioning; do echo \"sync $d\"; rm -rf /target/$d/*; cp -rv /src/$d/. /target/$d/; done; echo done"]
