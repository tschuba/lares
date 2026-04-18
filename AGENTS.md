# AGENTS

## Repo reality (important)
- This repo is currently planning/documentation-first. There is no runnable app yet.
- No build/test/lint/typecheck/format toolchain is configured (no manifests, CI, or task runner).
- `compose/`, `config/`, and `bridges/vallox/` are intentionally present but currently empty.

## Language and docs
- Repository documentation is German-first (`README.md`, `docs/*.md`); keep new docs and ADR updates in German.
- Treat docs as source of truth unless executable config appears later and contradicts them.

## High-impact architecture constraints
- MQTT is the central integration bus (ADR-003).
- Keep Sungrow access behind `modbus-proxy` (ADR-004); do not connect multiple clients directly.
- Keep a single productive InfluxDB on NAS only (ADR-005); do not introduce a second InfluxDB on Pi.
- Internet-facing UIs are function-named and Authentik-protected:
  - `home.schubs.net` (Home Assistant)
  - `cockpit.schubs.net` (Grafana)
- Internal services (MQTT, bridges, InfluxDB, modbus-proxy) are not meant to be public.

## Planned custom code boundary
- Only `bridges/vallox/` is planned as custom code (`vallox2mqtt`, Python bridge) (ADR-006).
- Prefer off-the-shelf container images for other integrations unless docs/ADRs change.

## Before making infra/code changes
- Read, in order:
  1. `README.md`
  2. `docs/entscheidungen.md`
  3. `docs/architektur.md`
  4. `docs/inventar.md`
- Preserve documented local-first decisions (e.g., `meross_lan`, cloud exceptions limited to Blink/Alexa/weather uploads).
