## 1. Off-the-shelf image pinning

- [x] 1.1 `docker-compose.yml:18` mosquitto → `eclipse-mosquitto:2.0.22`
- [x] 1.2 `docker-compose.yml:35` modbus-proxy → `tiagocoutinho/modbus-proxy:1.0.0` (was already `1.3.2`, kept)
- [x] 1.3 `docker-compose.yml:119` ecowitt2mqtt → `bachya/ecowitt2mqtt:2026.01.0`
- [x] 1.4 `docker-compose.yml:221` telegraf → `telegraf:1.39.1`
- [x] 1.5 `docker-compose.pi.yml:9` telegraf → `telegraf:1.39.1`
- [x] 1.6 `docker-compose.yml:250` influxdb → `influxdb:2.9.1`

## 2. Release-gated bridge build workflow

- [x] 2.1 Add `release: types: [published]` trigger to
      `.github/workflows/build-bridges.yml`
- [x] 2.2 Extend each of the 6 jobs' `if:` condition to also run on a matching
      release tag (`startsWith(github.event.release.tag_name, '<image-name>-v')`)
- [x] 2.3 Add a `type=match,pattern=<image-name>-v(.*),group=1` line to each job's
      `docker/metadata-action` tags list
- [x] 2.4 Leave existing branch/sha/latest tag lines and push-to-main path filters
      unchanged

## 3. Initial baseline releases

- [x] 3.1 Confirm each bridge's current `:latest` image runs correctly before
      cutting a release from the same `main`
- [x] 3.2 Publish `vallox2mqtt-v1.0.0`, `luxtronik2mqtt-v1.0.0`,
      `meross2mqtt-v1.0.0`, `sungrow2mqtt-v1.0.0`, `weewx-v1.0.0`,
      `skoda2mqtt-v1.0.0` GitHub Releases (all bridges already at pinned versions)
- [x] 3.3 Update `docker-compose.yml` image lines (sungrow2mqtt:50, vallox2mqtt:71,
      luxtronik2mqtt:98, weewx:143, meross2mqtt:174, skoda2mqtt:197) to `:1.0.0`
      (all bridge image tags were already pinned to specific versions)

## 4. Documentation

- [x] 4.1 Document the per-bridge release process in `AGENTS.md`'s "Adding or
      changing a bridge" section
- [x] 4.2 Add a new ADR to `docs/entscheidungen.md` (German) covering
      exact-version pinning and the release-gated bridge build scheme (ADR-018)
- [x] 4.3 Note in `COOLIFY.md` that pinned tags require an explicit
      `docker compose pull`

## 5. Verification

- [x] 5.1 `docker compose -f docker-compose.yml config` and
      `docker compose -f docker-compose.pi.yml config` parse cleanly (verified)
- [ ] 5.2 `docker manifest inspect` (or `docker pull`) each of the 6 `:1.0.0`
      bridge images after release (manual — requires NAS access)
- [ ] 5.3 Push a harmless change to a bridge directory on a branch; confirm
      `main`-push builds still publish `latest`/`<sha>` without a release (manual — requires CI run)
- [ ] 5.4 Publish one real test release (e.g. `vallox2mqtt-v1.0.1`); confirm only
      the matching job runs and pushes exactly `1.0.1` (manual — requires GitHub Release)
- [ ] 5.5 `docker compose pull` on NAS/Pi after the compose edits; confirm all
      pinned tags resolve and pull (manual — requires NAS/Pi access)
