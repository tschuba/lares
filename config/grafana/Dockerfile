# Daten-Image: nur Dashboards + Provisioning, kein Grafana. Läuft als Init-Container (ADR-020).
FROM busybox:1.37
COPY dashboards /src/dashboards
COPY provisioning /src/provisioning
# Ziel-Volumes leeren (gelöschte Dashboards entfernen), dann Inhalt kopieren
CMD ["sh", "-c", "for d in dashboards provisioning; do rm -rf /target/$d/* && cp -r /src/$d/. /target/$d/; done"]
