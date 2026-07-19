## Context

`skoda2mqtt` (`bridges/skoda/skoda2mqtt.py`, ADR-016) is a single-file async Python bridge:
`main()` wraps `run()` in an unlimited exponential-backoff retry loop (10s → 300s) that treats
every exception identically. `run()` authenticates once via `myskoda.connect(username,
password)`, then runs two concurrent loops in an `asyncio.TaskGroup`: `polling_loop` (reads
charging state every `POLL_INTERVAL`, publishes to MQTT) and `command_loop` (subscribes to an
MQTT command topic, issues charge commands). Both loops currently catch `Exception` broadly
and just log — nothing escalates out of them today.

`myskoda` is a community reverse-engineered client for Skoda's undocumented Cloud/OAuth API.
Its lockout/rate-limit policy is not published anywhere; community bug reports (
`skodaconnect/myskoda`) confirm the backend does lock accounts and return HTTP 429 on repeated
failed logins, but the exact thresholds are unknown.

The fix needs to ship as a single, mostly-contained change to this one bridge (plus
`docker-compose.yml`/docs), since this is a home-lab repo with no test infrastructure for
bridges and a small number of stakeholders (the repo owner, who is also the only operator).

## Goals / Non-Goals

**Goals:**
- Eliminate the unbounded, fast (≤5min-interval), indefinite retry of rejected mySkoda
  credentials that risks a real account lockout.
- Cover *both* the initial-login failure path and failures surfacing later, mid-session
  (e.g. an expiring refresh token), since the latter currently retries even faster (every
  `POLL_INTERVAL`, with zero backoff) and is arguably the higher-risk path.
- Make the "stop entirely" vs "keep retrying forever, very slowly" trade-off a runtime
  decision (env var), not a hardcoded one — Skoda's actual lockout policy can't be known in
  advance, so the safest approach is to let the operator dial this in empirically rather than
  guess once in code.
- Keep the bridge container alive and observable (via MQTT) in every failure mode, never
  silently exit (interacts badly with `restart: unless-stopped`).

**Non-Goals:**
- Distinguishing *why* a login was rejected (wrong password vs. Skoda-side outage vs.
  pending ToS) beyond what the `myskoda` library's exception types already convey — it
  doesn't expose finer detail (e.g. HTTP status) on most of these exceptions.
- Persisting failure-counter state across container restarts (e.g. to a file/volume) — out of
  scope; accepted that any container restart resets the bridge to the fast retry tier.
- Changing retry/backoff behavior for non-auth failures (MQTT broker down, network errors) —
  these keep today's existing unlimited-retry behavior unchanged.
- Applying this pattern to the repo's other bridges (`luxtronik2mqtt`, `vallox2mqtt`,
  `meross2mqtt`) — none of them talk to an API known to lock accounts on repeated failed auth;
  out of scope here, could be a future follow-up if warranted.

## Decisions

**Two-tier backoff (fast tier, then cooldown tier) instead of a single bounded retry.**
A single "retry N times, then stop" design was considered and initially planned, but rejected
because it can't tell a one-off blip (worth retrying quickly) from a real problem (worth
backing off hard from) — collapsing both into one budget means either over-reacting to noise
or under-reacting to a real failure. Two independent counters (`auth_failures` for the fast
tier, `cooldown_failures` for the cooldown tier) cleanly separate "is this just a blip"
(resolved in seconds) from "is this a sustained problem" (resolved over hours/days).

**The cooldown tier's total retry budget is a runtime config knob (`AUTH_COOLDOWN_MAX_RETRIES`),
not a hardcoded "stop" or "retry forever."** Considered and rejected: (a) hardcode "stop
forever after N attempts" — minimizes login attempts, but a one-off Skoda-side outage that
happens to surface as one of these exception types then permanently halts the bridge requiring
manual intervention, with no way to know in advance whether that's actually necessary; (b)
hardcode "retry forever, slowly" — self-heals automatically, but offers no way to fully
eliminate the bridge's contribution to lockout risk if that turns out to matter (e.g. if
Skoda's policy considers cumulative attempts over a long window, not just a rolling window).
Making it a config value (default `0` = unlimited) lets the operator deploy with maximum
self-healing first and observe real-world behavior, then dial in a hard stop without a code
change if that turns out to be necessary.

**Auth-class exceptions identified by reading `myskoda/auth/authorization.py` directly, not
relying on docs or summaries.** Six exceptions are raised there, all only after an HTTP
exchange with Skoda's servers has completed and come back rejected/malformed/requiring action:
`AuthorizationFailedError`, `AuthorizationError`, `CSRFError`, `TermsAndConditionsError`,
`MarketingConsentError` (all reachable from `connect()`), and `TokenExpiredError` (only
reachable from `authorize_refresh_token()` — i.e. mid-session token refresh, not initial
login). They share no common base class besides `Exception`, so must be enumerated explicitly.
Only two of the six (`AuthorizationError`, `AuthorizationFailedError`) are re-exported from the
top-level `myskoda` package; the rest must be imported from `myskoda.auth.authorization`
directly — confirmed by reading `myskoda/__init__.py`, since importing the others from the
top-level package raises `ImportError` at startup. Deliberately excluded: `NotAuthorizedError`
(internal programming-error guard, not a network condition), `BrandError` (static
config issue, fails identically on every attempt regardless of backoff — not a credentials
problem), `InvalidStatusError` (confirmed not raised anywhere in this file).

**`polling_loop`/`command_loop` re-raise auth-class exceptions instead of swallowing them.**
Both currently catch bare `Exception` and just log, with no escalation. `TokenExpiredError`
specifically can only ever surface here (it's not reachable from the initial `connect()` this
bridge uses), so without this change there is no path for the new retry/backoff logic to ever
see it — a mid-session token expiry would keep silently retrying every `POLL_INTERVAL` (60s,
zero backoff) forever, which is a faster and more dangerous pattern than the original bug.

**`run()` connects to MQTT before attempting Skoda auth, and retries Skoda auth in a loop
underneath that single MQTT connection.** Originally, MQTT was connected only after a
successful Skoda login. That meant: if MQTT was ever unreachable, the original code would
still have already re-authenticated to Skoda on every single outer retry — itself a smaller
instance of the same hammering risk. Reordering means status can also be published to MQTT
even while Skoda auth is actively failing, which the original ordering made impossible.

**On permanent stop, block forever in-process (`asyncio.Event().wait()`) rather than exit.**
The `skoda2mqtt` docker-compose service has `restart: unless-stopped`. If the process exited
after deciding to stop, Docker would immediately restart the container, silently resetting the
in-memory failure counters and re-triggering login attempts — defeating the entire safeguard.
Staying alive but idle (still connected to MQTT, just never reconnecting to Skoda) is the only
way to make "stop" actually mean stop without adding persistent state.

**Status published to a new retained MQTT topic (`ev/skoda/status`), reusing the existing
observability pipeline.** Every other piece of state in this repo flows MQTT → Telegraf →
InfluxDB → Grafana; this keeps the bridge consistent with that pattern rather than introducing
a separate alerting mechanism, and lets the operator visually distinguish `ok` /
`auth_retry` (fast tier) / `auth_error` (cooldown tier, or terminal if `final: true`).

## Risks / Trade-offs

- **[Risk]** `myskoda` doesn't distinguish "permanently rejected" from "Skoda server
  temporarily erroring" at the exception level — both raise identically.
  **Mitigation**: in the default (`AUTH_COOLDOWN_MAX_RETRIES=0`) mode this doesn't matter
  much — a transient outage just self-heals on a later cooldown attempt. In limited mode, a
  one-off outage that happens to land during the fast tier could exhaust the budget and
  require a manual restart even though credentials were fine; accepted as a known limitation
  given the library's constraints, documented in the spec.

- **[Risk]** Both failure counters reset to 0 immediately on any successful `connect()`, before
  the session has run for any length of time. A pathological rapid connect-succeed/fail
  flapping pattern could in theory never reach `AUTH_COOLDOWN_MAX_RETRIES`.
  **Mitigation**: judged unlikely (a fresh password-based login always yields a fresh,
  non-expired token) and not worth a "minimum stable runtime before reset" mechanism — and
  even in that case, each cycle still requires one full successful login first, so it can't
  exceed the fast-tier rate regardless.

- **[Risk]** `restart: unless-stopped` resets in-memory counters on *any* container restart,
  not just deliberate ones (e.g. a host reboot also clears a "permanently stopped" state).
  **Mitigation**: accepted — no persistent state store is in scope; worst case is a few extra
  fast-tier attempts after an involuntary restart, still far safer than the original bug.

- **[Risk]** No automated test suite exists for this or any bridge in this repo.
  **Mitigation**: verification is manual (see `tasks.md`), including running with deliberately
  wrong credentials against the real mosquitto broker and observing both `AUTH_COOLDOWN_MAX_RETRIES`
  modes plus the MQTT status topic.

- **[Risk]** `asyncio.TaskGroup` cancels sibling tasks when one fails; if that cancellation's
  `CancelledError` were ever included in the propagated `ExceptionGroup`, it could leak past
  `except* AUTH_EXCEPTIONS` and cause `main()`'s outer handler to also catch it, silently
  resetting the fast/cooldown counters on every auth failure and defeating the whole safeguard.
  **Mitigation**: `asyncio.TaskGroup` is documented to exclude cancellation-induced
  `CancelledError` from sibling tasks out of the propagated group; this is the same
  `except*`/`TaskGroup` idiom `main()` already relies on today. Still called out explicitly as
  a required verification step rather than assumed silently correct.

## Migration Plan

- Single deploy: update `bridges/skoda/skoda2mqtt.py`, rebuild/push the bridge image (existing
  CI in `.github/workflows/build-bridges.yml` already builds on changes under `bridges/skoda/`),
  add the five new env vars to `docker-compose.yml` (all have safe defaults — a currently
  healthy bridge's behavior is unaffected until an auth failure actually occurs), redeploy the
  `skoda2mqtt` service.
- No data migration — all new state (`auth_failures`, `cooldown_failures`) is in-memory only.
- Rollback: revert the bridge image/compose changes; no persisted state to clean up.

## Open Questions

- Once real-world data is gathered on whether the default unlimited-cooldown mode actually
  avoids lockouts, should `AUTH_COOLDOWN_MAX_RETRIES` default change, or stay opt-in forever?
- Should this retry/backoff/status-topic pattern be generalized and applied to the repo's other
  cloud-dependent bridges (e.g. `meross2mqtt`, also cloud-dependent per ADR-011) — left for a
  future change if this proves valuable in practice.
