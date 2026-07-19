## 1. Exception handling foundation

- [x] 1.1 Import `AuthorizationError`, `AuthorizationFailedError`, `CSRFError`, `MarketingConsentError`, `TermsAndConditionsError`, `TokenExpiredError` from `myskoda.auth.authorization` (not the top-level `myskoda` package — only two of the six are re-exported there) in `bridges/skoda/skoda2mqtt.py`
- [x] 1.2 Define a module-level `AUTH_EXCEPTIONS` tuple containing all six exceptions
- [x] 1.3 Add new config constants: `AUTH_MAX_RETRIES` (default 3), `AUTH_BACKOFF_BASE` (default 10), `BACKOFF_CAP` (300), `AUTH_COOLDOWN_BASE` (default 1800), `AUTH_COOLDOWN_MAX` (default 86400), `AUTH_COOLDOWN_MAX_RETRIES` (default 0), and `TOPIC_STATUS = "ev/skoda/status"`

## 2. Status publishing

- [x] 2.1 Add a `publish_status(mqtt, state, **fields)` helper that publishes a retained JSON message to `TOPIC_STATUS` with `state`, `last_updated`, and any extra fields

## 3. Escalate mid-session auth failures

- [x] 3.1 In `polling_loop`, re-raise `AUTH_EXCEPTIONS` instead of letting the bare `except Exception` swallow them
- [x] 3.2 In `command_loop`, re-raise `AUTH_EXCEPTIONS` instead of letting the bare `except Exception` swallow them around the `handle_command` call

## 4. Two-tier auth retry/backoff in `run()`

- [x] 4.1 Reorder `run()` so the `aiomqtt.Client` connection is established once, before the Skoda authentication retry loop (not after a successful login, as today)
- [x] 4.2 Wrap the `myskoda.connect()` call and the `asyncio.TaskGroup` (running `polling_loop`/`command_loop`) in a single `while True` retry loop using `except* AUTH_EXCEPTIONS`
- [x] 4.3 Track `auth_failures` (fast-tier counter) and `cooldown_failures` (cooldown-tier counter), both reset to 0 on successful authentication
- [x] 4.4 Implement the fast tier: while `auth_failures < AUTH_MAX_RETRIES`, increment, sleep `min(AUTH_BACKOFF_BASE * 2**(auth_failures-1), BACKOFF_CAP)`, publish `auth_retry` status, retry
- [x] 4.5 Implement the cooldown tier: once the fast tier is exhausted, increment `cooldown_failures`, sleep `min(AUTH_COOLDOWN_BASE * 2**(cooldown_failures-1), AUTH_COOLDOWN_MAX)`, publish `auth_error` status (with `next_retry_in_s`), retry
- [x] 4.6 Implement the permanent-stop condition: when `AUTH_COOLDOWN_MAX_RETRIES > 0` and `cooldown_failures >= AUTH_COOLDOWN_MAX_RETRIES`, log a final error, publish a terminal `auth_error` status (`final: true`), then block forever via `await asyncio.Event().wait()` — never exit the process
- [x] 4.7 Publish an `ok` status on every successful authentication

## 5. Cleanup

- [x] 5.1 In `main()`, replace the hardcoded `min(backoff * 2, 300)` with `min(backoff * 2, BACKOFF_CAP)`

## 6. Deployment configuration

- [x] 6.1 Add `AUTH_MAX_RETRIES=3`, `AUTH_BACKOFF_BASE=10`, `AUTH_COOLDOWN_BASE=1800`, `AUTH_COOLDOWN_MAX=86400`, `AUTH_COOLDOWN_MAX_RETRIES=0` to the `skoda2mqtt` service in `docker-compose.yml`

## 7. Documentation

- [x] 7.1 Document the five new environment variables in `docs/inventar.md`, next to the existing `MYSKODA_*` variables
- [x] 7.2 Add a short German-language addendum to ADR-016 in `docs/entscheidungen.md` documenting the resilience behavior and lockout-prevention rationale

## 8. Verification

- [x] 8.1 `python -m py_compile bridges/skoda/skoda2mqtt.py` to confirm no syntax errors
- [x] 8.2 With deliberately wrong `MYSKODA_PASSWORD` and default config (`AUTH_COOLDOWN_MAX_RETRIES=0`), run the bridge and confirm: fast tier retries `AUTH_MAX_RETRIES` times with growing backoff, then the cooldown tier retries indefinitely (use small test values for `AUTH_COOLDOWN_BASE`/`AUTH_COOLDOWN_MAX` to avoid waiting 30min+) and never stops
- [x] 8.3 With `AUTH_COOLDOWN_MAX_RETRIES` set to a small positive number (e.g. 2), confirm the bridge stops permanently after that many cooldown failures, publishes a final `auth_error` (`final: true`) status, makes no further connect attempts, and stays `Up` in `docker ps` rather than crash-looping
- [x] 8.4 Subscribe to `ev/skoda/status` (`mosquitto_sub -t ev/skoda/status`) during 8.2 and 8.3 and confirm the expected `auth_retry`/`auth_error`/`ok` transitions appear
- [x] 8.5 Restore correct credentials and `docker compose restart skoda2mqtt`; confirm it reconnects, publishes `{"state": "ok"}`, and resumes publishing to `ev/skoda/state`
- [x] 8.6 Temporarily stop the `mosquitto` broker while `skoda2mqtt` is running with valid credentials; confirm it keeps retrying indefinitely via the existing unchanged transient-failure backoff, without consuming any auth-tier retry budget
- [x] 8.7 If feasible, simulate a mid-session `TokenExpiredError` (e.g. by monkeypatching `myskoda.get_charging` to raise it after a successful initial connect) and confirm `polling_loop` escalates it into the fast/cooldown retry path, with exactly one retry cycle logged per failure (confirms `asyncio.TaskGroup`'s sibling-cancellation `CancelledError` does not leak past `except* AUTH_EXCEPTIONS` and cause `main()` to also catch it and reset the counters)
