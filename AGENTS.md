# AGENTS

## Repo reality

- Lares is a NAS-centric smart-home hub for `schubs.net`: MQTT integration bus, Home Assistant for control, Grafana for visualization, InfluxDB for long-term storage.
- Documentation-first: `docs/*.md` and the ADRs in `docs/entscheidungen.md` are the source of truth for "why"; implementation (Compose files, bridge code, configs) is added incrementally to match documented decisions.
- No root-level build/lint/test toolchain (no manifests, no task runner). The only test suite is per-bridge (see Commands).
- `config/` contains configuration templates and subdirectories for various services.
- `bridges/` contains custom bridge code: vallox, luxtronik, meross2mqtt, weewx, skoda (ADR-006, ADR-010, ADR-016).

## Language and docs

- Repository documentation is German-first (`README.md`, `docs/*.md`); keep new docs and ADR updates in German.
- Treat docs as source of truth unless executable config appears later and contradicts them.

## Architecture

- Two-host split (ADR-014):
  - Pi (`192.168.178.69`, Coolify host): public-facing services only — Home Assistant (`home.schubs.net`), Grafana (`cockpit.schubs.net`), Traefik, Authentik.
  - NAS (`192.168.178.163`): all integration services — Mosquitto, every MQTT bridge, modbus-proxy, WeeWX, Telegraf, InfluxDB 2.x.
- MQTT (Mosquitto) is the central integration bus (ADR-003): device → protocol bridge (NAS) → MQTT (NAS) → Telegraf → InfluxDB (NAS); Home Assistant and Grafana on the Pi consume MQTT/InfluxDB over LAN.
- Bridge pattern: each `bridges/<name>/` is a standalone script plus a Dockerfile (+ `requirements.txt` or `pyproject.toml`), built and published independently to `ghcr.io/tschuba/lares/<name>` by `.github/workflows/build-bridges.yml` (one path-filtered job per bridge).
- `docker-compose.yml` (deployed on the NAS) gates bridges behind profiles: `sungrow`, `ventilation`, `heating`, `weather`, `meross`, `ev`; `mosquitto`/`influxdb`/`telegraf` have no profile and always run. `docker-compose.pi.yml` is Pi-only (system-metrics Telegraf).
- `config/<service>/` holds provisioning and config templates (Mosquitto auth, `telegraf.conf`, Grafana dashboards/provisioning, `modbus-proxy.yml`, WeeWX template rendered via `envsubst`).

## High-impact architecture constraints

- MQTT is the central integration bus (ADR-003).
- Keep Sungrow access behind `modbus-proxy` (ADR-004); do not connect multiple clients directly.
- Keep a single productive InfluxDB on NAS only (ADR-005); do not introduce a second InfluxDB on Pi.
- `meross2mqtt` is read-only cloud telemetry; all Meross device control stays in Home Assistant via `meross_lan` (ADR-011) — don't add control logic to the bridge.
- Internet-facing UIs are function-named and Authentik-protected:
  - `home.schubs.net` (Home Assistant)
  - `cockpit.schubs.net` (Grafana)
- Internal services (MQTT, bridges, InfluxDB, modbus-proxy) are not meant to be public.

## Planned custom code boundary

- `bridges/vallox/` – custom Python bridge (`vallox2mqtt`) (ADR-006)
- `bridges/luxtronik/` – custom Python bridge (`luxtronik2mqtt`) (ADR-006)
- `bridges/meross2mqtt/` – custom image based on meross2homie; adds `discover.py` (one-time cloud auth for UUID/key discovery) and `entrypoint.sh` (auto-discovery on first start) (ADR-006, ADR-011)
- `bridges/weewx/` – custom image based on `felddy/weewx` with `weewx-mqtt-subscribe` and `envsubst` templating (ADR-006, ADR-010)
- `bridges/skoda/` – custom Python bridge (`skoda2mqtt`), mySkoda Cloud API (ADR-016)
- Prefer off-the-shelf container images for all other integrations unless docs/ADRs change (e.g. Sungrow uses `bohdan0/sungrow2mqtt`, ADR-013).

## Commands

- Run the one existing test suite (vallox2mqtt):

  ```bash
  cd bridges/vallox && python3 -m unittest discover -s tests -p "test_*.py"
  # equivalently: bridges/vallox/tests/run_tests.sh
  ```

- Build a bridge image locally: `docker build -t <name> bridges/<bridge-dir>`
- Deploy/update NAS services: `docker compose --profile <profile> [--profile <profile>...] up -d` (profiles above; see `COOLIFY.md` for env vars)
- Deploy Pi system-metrics Telegraf: `docker compose -f docker-compose.pi.yml up -d`
- CI (`.github/workflows/build-bridges.yml`) builds and pushes each changed bridge to GHCR on push to `main`, path-filtered per bridge directory; `workflow_dispatch` supports manual rebuilds.

## Adding or changing a bridge

1. Read, in order (see below), to confirm the change doesn't contradict a documented decision.
2. Bridge code lives at `bridges/<name>/<name>.py` plus a Dockerfile and `requirements.txt` (or `pyproject.toml`, see `meross2mqtt`). Config templates go in `config/<name>/`, never hardcoded secrets.
3. Wire the service into `docker-compose.yml` under the right profile, and into `.github/workflows/build-bridges.yml`'s path filters/job list if it's a new bridge directory.
4. Update `docs/inventar.md` and `docs/entscheidungen.md` for new devices/services or deviations from existing ADRs.

### Releasing a bridge version (ADR-018)

Bridge images in `docker-compose.yml` are pinned to explicit semver tags. A new tag is only pushed to GHCR when a GitHub Release is published. Steps:

1. Merge your changes to `main`. The CI build publishes `latest` and a `<sha>` tag — use these for manual pre-release testing.
2. Create a GitHub Release with tag `<image-name>-vX.Y.Z` (e.g. `vallox2mqtt-v1.2.6`). Use the published image name, not the bridge directory name (e.g. `sungrow2mqtt`, not `sungather`).
3. The release trigger fires only the matching build job and pushes the `X.Y.Z` semver tag to GHCR.
4. Update the image tag in `docker-compose.yml` and deploy: `docker compose pull && docker compose --profile <profile> up -d`.

## Before making infra/code changes

- Read, in order:
  1. `README.md`
  2. `docs/entscheidungen.md`
  3. `docs/architektur.md` (note: some phrasing predates ADR-014's NAS-centric split; `docker-compose.yml` reflects current topology)
  4. `docs/inventar.md`
- Preserve documented local-first decisions (e.g., `meross_lan`, cloud exceptions limited to Blink/Alexa/weather uploads).

## Documentation map

- `docs/architektur.md` — overall architecture + mermaid diagram
- `docs/entscheidungen.md` — ADRs, the source of truth for "why"
- `docs/inventar.md` — full hardware/service/network inventory
- `docs/konfiguration.md` — device-side setup (Ecowitt, WeeWX)
- `docs/umsetzungsplan.md` — phased implementation roadmap
- `COOLIFY.md` — deployment guide (profiles, env vars, troubleshooting)
