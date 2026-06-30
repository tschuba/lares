## Context

`docker-compose.yml` (NAS) and `docker-compose.pi.yml` (Pi) gate services behind
profiles; `mosquitto`/`influxdb`/`telegraf` always run, the rest are
profile-gated. Off-the-shelf images (`eclipse-mosquitto`, `tiagocoutinho/modbus-proxy`,
`bachya/ecowitt2mqtt`, `telegraf`, `influxdb`) are referenced with floating tags.
The six custom bridge images are built independently by path-filtered jobs in
`.github/workflows/build-bridges.yml` and published to
`ghcr.io/tschuba/lares/<bridge>`; every job currently tags `latest` (plus
branch/sha) on every push to `main`, and compose references no explicit tag
(= `latest`) for all of them. There is no existing release automation
(no release-please/semantic-release) and AGENTS.md documents a deliberately
minimal, no-root-toolchain repo — any solution should stay consistent with that.

## Goals / Non-Goals

**Goals:**
- No image reference in either compose file resolves to a floating tag.
- Custom bridge images change in production only via a deliberate, reviewable
  action (a GitHub Release), never as a side effect of merging to `main`.
- Keep the existing `main`-push build (latest/branch/sha tags) working for manual
  pre-release testing — don't slow down day-to-day bridge development.
- Stay consistent with the repo's minimal-tooling philosophy: no new root-level
  toolchain, no release-please/semantic-release.

**Non-Goals:**
- Pinning base images inside bridge Dockerfiles (`FROM python:3.x-slim`,
  `felddy/weewx:latest`) — out of scope for this change; flagged as a possible
  future follow-up.
- Digest pinning (`@sha256:...`) in addition to tag pinning — not requested.
- Automating version bumps/changelogs — manual tagging is sufficient for a
  6-bridge homelab repo.
- Tying all 6 bridges to one repo-wide version number — each bridge releases
  independently, on its own schedule.

## Decisions

**Off-the-shelf images pinned to the latest available stable version, not to
whatever happens to be currently running.** A deliberate upgrade, bundled with the
pinning change. Versions verified live against each registry/release feed during
planning (re-verified via direct Docker Hub tag probing and the upstream GitHub
releases API, not just the first page of results — large repos like `telegraf`
(460 tags) and `influxdb` (631 tags) can bury the true latest tag behind
non-version tags like `-alpine`/`pr-*`/`dependabot-*` on page one):
- `eclipse-mosquitto:2.0.22` (a `2.1.x` source release exists upstream, but no
  `2.1.x` Docker image has been published yet — `2.0.22` is the latest *published
  image*, confirmed via 404s on `2.1.0`/`2.1.1`/`2.1.2`)
- `tiagocoutinho/modbus-proxy:1.0.0` (image has had no release since 2022; only 3
  tags exist total; `latest` and `1.0.0` are the same build)
- `bachya/ecowitt2mqtt:2026.01.0` (calendar-versioned; confirmed no `2026.02.0`/
  `2026.03.0`/`2026.06.0` exist)
- `telegraf:1.39.1` (confirmed via `influxdata/telegraf`'s GitHub releases API,
  published the day before this proposal was drafted)
- `influxdb:2.9.1` — staying on the 2.x line deliberately. InfluxDB also has a
  newer 3.x line (latest `v3.10.0`), but it's a different storage engine (IOx),
  not a drop-in tag bump; the repo's current deployment, config, and ADR-005
  ("single productive InfluxDB on NAS only") are all built around 2.x. Jumping to
  3.x would need its own migration and is explicitly out of scope here.

**Release trigger is a GitHub Release (`release: types: [published]`), not a bare
tag push.** Gives changelog notes in the GitHub UI per bridge release and matches
"only updated on release" literally. Publishing a Release auto-creates the
underlying tag, so this subsumes tag-push triggering — no separate `push: tags`
wiring needed.

**Tag naming `<image-name>-vX.Y.Z`, prefixed by the published image name (not the
source directory name).** This is a monorepo building 6 independently-versioned
images from one workflow file, and one bridge (`sungrow2mqtt`) is built from a
differently-named directory (`bridges/sungather/`). Using the published image name
keeps the release tag self-describing regardless of source layout.

**`docker/metadata-action`'s `type=match` pattern derives the semver tag directly
from `github.event.release.tag_name`.** No custom scripting needed — `release` is
a documented, supported event type for that action's tag matching.

**Existing `main`-push build behavior is left untouched.** Considered making the
pipeline "release-only" end-to-end by removing it, but rejected: it's useful for
testing a bridge change before committing to a release, and removing it wouldn't
reduce any risk — compose no longer references `latest` either way — it would only
remove a convenience.

## Risks / Trade-offs

- **[Risk]** Pinned tags mean compose no longer "just" picks up upstream patches;
  someone has to notice and bump versions deliberately.
  **Mitigation**: accepted as the explicit goal of this change — reproducibility
  over auto-patching. A future Dependabot/Renovate config for Docker Compose could
  surface available bumps if drift becomes a maintenance burden (see Open
  Questions).
- **[Risk]** `docker/metadata-action`'s `type=match` against
  `github.event.release.tag_name`, combined with 6 parallel per-bridge jobs in one
  workflow reacting to one shared `release` event, needs to be verified to
  actually scope correctly to just the matching bridge.
  **Mitigation**: required manual verification step — publish one real test
  release and confirm only the matching job runs and only the matching tag is
  pushed (see `tasks.md` §5).
- **[Risk]** `tiagocoutinho/modbus-proxy` has had no release since 2022; pinning to
  `1.0.0` doesn't reduce real upgrade risk (it's the same build `latest` already
  pointed to) but does freeze the repo against a future silent break if the
  maintainer ever force-pushes a new `latest` without a new tag.
  **Mitigation**: none needed — pure improvement, no behavior change today.
- **[Risk]** Initial `v1.0.0` baseline releases for all 6 bridges happen in one
  batch; if any bridge's `main` is currently broken, that breakage gets enshrined
  as `v1.0.0`.
  **Mitigation**: verification step requires confirming each bridge's current
  `:latest` image already runs correctly before cutting `v1.0.0` from the same
  code (see `tasks.md` §3.1).

## Migration Plan

1. Land the workflow change (`release` trigger + per-job tag matching) and confirm
   it doesn't break existing `main`-push builds.
2. Cut `vallox2mqtt-v1.0.0` … `skoda2mqtt-v1.0.0` GitHub Releases from current
   `main`.
3. Edit `docker-compose.yml`/`docker-compose.pi.yml` to the exact pinned tags.
4. Deploy: `docker compose pull && docker compose --profile ... up -d` on the NAS,
   `docker compose -f docker-compose.pi.yml pull && up -d` on the Pi.
5. Document the release process in `AGENTS.md`, add the ADR to
   `docs/entscheidungen.md`, note the pull requirement in `COOLIFY.md`.

Rollback: revert the compose tag edits to the previous floating tags; no data
migration is involved (image pinning is stateless).

## Open Questions

- Should a Dependabot/Renovate config be added later to surface available version
  bumps for both the pinned off-the-shelf images and the bridge base images, now
  that floating auto-updates are gone?
- Should the Dockerfile base images (`python:3.x-slim`, `felddy/weewx:latest`) get
  the same exact-pinning treatment in a follow-up change?
