## Why

`skoda2mqtt` (ADR-016) retries every fatal error identically: log, sleep with exponential
backoff (10s → 300s), retry forever. If `MYSKODA_USERNAME`/`MYSKODA_PASSWORD` become wrong, or
the session's refresh token goes stale mid-run, the bridge keeps retrying the same bad
credentials against Skoda's login endpoint indefinitely (as often as every 5 minutes). Skoda's
identity backend is known to lock accounts / rate-limit on repeated failed logins
(community-reported via `skodaconnect/myskoda`), so this bug can talk the linked mySkoda
account into a real lockout instead of just failing loudly once. This needs fixing before the
next time credentials drift out of sync (password rotation, expired consent, etc.).

## What Changes

- Distinguish auth-rejection failures (`AuthorizationFailedError`, `AuthorizationError`,
  `CSRFError`, `TermsAndConditionsError`, `MarketingConsentError`, `TokenExpiredError` — all
  verified against the `myskoda` library source) from transient/connectivity failures, which
  keep today's unchanged unlimited-retry behavior.
- Escalate auth-rejection failures that occur **during ongoing polling/commands** (e.g. a
  refresh token expiring mid-session), not just at initial login — `polling_loop` and
  `command_loop` currently swallow these silently and retry every `POLL_INTERVAL` (60s)
  forever, which is worse than the original bug.
- Add a two-tier, fully configurable backoff for auth-rejection failures: a fast tier (a few
  quick retries for one-off blips) followed by a cooldown tier (doubling backoff up to a
  configurable cap, e.g. once/day).
- The cooldown tier's total retry budget is itself configurable
  (`AUTH_COOLDOWN_MAX_RETRIES`). Default `0` = retry forever at the capped slow rate (chosen
  deliberately as the initial deployment default, to observe empirically whether Skoda
  tolerates a sufficiently slow capped rate, since its lockout policy is undocumented). Set to
  a positive number to make the bridge stop permanently (zero further automated login
  attempts) once that many cooldown attempts have failed — requiring a manual container
  restart to resume.
- Publish bridge auth status to a new retained MQTT topic (`ev/skoda/status`) so the state is
  observable via the existing MQTT → Telegraf → InfluxDB → Grafana pipeline.
- Document the five new environment variables in `docs/inventar.md` and add a short addendum
  to ADR-016 in `docs/entscheidungen.md`.

## Capabilities

### New Capabilities

- `skoda2mqtt-auth-resilience`: how `skoda2mqtt` detects, retries, backs off, and (optionally)
  permanently stops on mySkoda authentication failures, and how that state is surfaced via MQTT.

### Modified Capabilities

(none — this is the first OpenSpec capability defined for `skoda2mqtt`; no prior spec exists
to delta against)

## Impact

- `bridges/skoda/skoda2mqtt.py`: imports, config, `polling_loop`, `command_loop`, `run()`,
  `main()` (cosmetic constant reuse only).
- `docker-compose.yml`: five new env vars on the `skoda2mqtt` service (profile `ev`).
- `docs/inventar.md`: document the new env vars.
- `docs/entscheidungen.md`: short addendum to ADR-016.
- No new dependencies. No test suite exists for this bridge today; verification is manual
  (see `tasks.md`).
