## Why

`docker-compose.yml` and `docker-compose.pi.yml` reference most images with a
floating tag — `latest`, a bare major version (`influxdb:2`), or a bare minor
version (`mosquitto:2.0`) — and all six custom bridge images (`vallox2mqtt`,
`luxtronik2mqtt`, `meross2mqtt`, `sungrow2mqtt`, `weewx`, `skoda2mqtt`) are
referenced with no tag at all, which resolves to `latest`.
`.github/workflows/build-bridges.yml` republishes each bridge's `latest` tag on
every push to `main` that touches that bridge's directory. The combination means a
`docker compose pull` on the NAS/Pi can silently change what's running, and any
merged bridge change becomes "live" on the next pull with no deliberate release
step in between — deployments are not reproducible and a specific bridge version
can't be reviewed or rolled back independently of `main`.

## What Changes

- Every `image:` line in `docker-compose.yml` and `docker-compose.pi.yml` is pinned
  to an exact, non-floating version (current latest stable release per upstream
  registry, verified live — see `design.md` for the specific versions and how they
  were verified).
- `.github/workflows/build-bridges.yml` gains a `release: types: [published]`
  trigger. Each bridge's build job is extended so that publishing a GitHub Release
  with a tag named `<image-name>-vX.Y.Z` (e.g. `vallox2mqtt-v1.2.0`) builds and
  pushes exactly `ghcr.io/tschuba/lares/<image-name>:X.Y.Z` for that bridge only.
- The existing push-to-`main` build behavior (publishing `latest`/`<branch>`/`<sha>`
  tags) is unchanged, so unreleased code stays pullable for manual testing — it
  just stops being what `docker-compose.yml` references in production.
- Each of the 6 bridges gets an initial `v1.0.0` release cut from current `main`,
  and `docker-compose.yml` is updated to pin to those tags as the new baseline.
- `AGENTS.md` documents the per-bridge release process; `docs/entscheidungen.md`
  gets a new ADR recording the versioning/release decision; `COOLIFY.md` notes that
  pinned tags require an explicit `docker compose pull` to move forward.

## Capabilities

### New Capabilities

- `pinned-image-deployment`: deployed compose files only ever reference exact
  image versions, and custom bridge images change only when a maintainer
  publishes a GitHub Release for that specific bridge.

### Modified Capabilities

(none — first OpenSpec capability covering image versioning/release behavior)

## Impact

- `docker-compose.yml`: 11 `image:` lines updated to exact tags.
- `docker-compose.pi.yml`: 1 `image:` line updated.
- `.github/workflows/build-bridges.yml`: add `release` trigger, per-job `if:`
  condition, and a `type=match` tag rule to all 6 bridge jobs.
- `AGENTS.md`: document the release process under "Adding or changing a bridge".
- `docs/entscheidungen.md`: new ADR.
- `COOLIFY.md`: deployment note about explicit pulls.
- No code changes inside any bridge; no new dependencies.
