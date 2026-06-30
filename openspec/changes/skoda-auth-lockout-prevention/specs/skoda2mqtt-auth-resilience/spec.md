## ADDED Requirements

### Requirement: Auth-class failures are identified by exception type, not by error message
The system SHALL treat `AuthorizationFailedError`, `AuthorizationError`, `CSRFError`,
`TermsAndConditionsError`, `MarketingConsentError`, and `TokenExpiredError` (all from
`myskoda.auth.authorization`) as auth-class failures. The system SHALL treat all other
exceptions (including connectivity errors such as timeouts or connection failures) as
transient failures, retried via the existing unlimited exponential backoff unchanged.

#### Scenario: Login rejected with wrong credentials
- **WHEN** `myskoda.connect()` raises `AuthorizationFailedError` because Skoda's login
  endpoint returned a non-OK status
- **THEN** the system classifies this as an auth-class failure and applies the fast/cooldown
  retry logic instead of the unlimited transient-failure backoff

#### Scenario: MQTT broker temporarily unreachable
- **WHEN** the bridge cannot connect to the configured MQTT broker
- **THEN** the system classifies this as a transient failure and retries with the existing
  unlimited exponential backoff (10s, doubling, capped at 300s), unaffected by any auth-class
  retry budget

### Requirement: Mid-session auth failures escalate instead of being silently retried
The system SHALL re-raise auth-class exceptions encountered during ongoing polling or command
handling (e.g. a refresh token expiring mid-session) so they are handled by the same
fast/cooldown retry logic as an initial login failure, instead of being caught and silently
retried every poll interval.

#### Scenario: Refresh token expires while the bridge is already running
- **WHEN** a request made during the regular polling loop raises `TokenExpiredError` after the
  bridge was previously authenticated successfully
- **THEN** the system stops the current polling/command session, classifies this as an
  auth-class failure, and applies the fast/cooldown retry logic — it does not continue polling
  at the normal poll interval as if nothing happened

### Requirement: Fast tier retries auth-class failures a bounded, configurable number of times
The system SHALL retry an auth-class failure up to `AUTH_MAX_RETRIES` (default 3) times, with
delay doubling from `AUTH_BACKOFF_BASE` seconds (default 10) and capped at 300 seconds between
attempts, before moving to the cooldown tier.

#### Scenario: First few consecutive auth-class failures
- **WHEN** an auth-class failure occurs and the number of consecutive fast-tier failures is
  still below `AUTH_MAX_RETRIES`
- **THEN** the system waits `min(AUTH_BACKOFF_BASE * 2^(attempt-1), 300)` seconds and retries
  authentication

#### Scenario: Successful authentication resets the fast-tier counter
- **WHEN** authentication succeeds after one or more fast-tier failures
- **THEN** the system resets the fast-tier failure counter to zero

### Requirement: Cooldown tier backs off auth-class failures at a slow, configurable, capped rate
Once the fast tier is exhausted, the system SHALL back off auth-class failures starting at
`AUTH_COOLDOWN_BASE` seconds (default 1800), doubling on each further consecutive cooldown
failure, capped at `AUTH_COOLDOWN_MAX` seconds (default 86400).

#### Scenario: Fast tier exhausted, entering cooldown
- **WHEN** an auth-class failure occurs and the fast-tier retry budget (`AUTH_MAX_RETRIES`)
  has already been exhausted
- **THEN** the system waits at least `AUTH_COOLDOWN_BASE` seconds before the next
  authentication attempt, and the wait time before each subsequent cooldown failure doubles up
  to `AUTH_COOLDOWN_MAX` seconds

#### Scenario: Successful authentication resets the cooldown-tier counter
- **WHEN** authentication succeeds after one or more cooldown-tier failures
- **THEN** the system resets the cooldown-tier failure counter to zero

### Requirement: The cooldown tier's total retry budget is configurable, including unlimited
The system SHALL support an `AUTH_COOLDOWN_MAX_RETRIES` setting (default 0) controlling how
many cooldown-tier failures are tolerated before the system stops attempting authentication
entirely. A value of 0 SHALL mean the cooldown tier retries indefinitely at the capped rate. A
positive value SHALL cause the system to stop permanently — making no further automated
authentication attempts — once that many cooldown-tier failures have occurred.

#### Scenario: Unlimited cooldown retries (default)
- **WHEN** `AUTH_COOLDOWN_MAX_RETRIES` is 0 and the cooldown tier keeps failing
- **THEN** the system continues retrying indefinitely at the capped cooldown rate, never
  stopping on its own

#### Scenario: Limited cooldown retries reach their budget
- **WHEN** `AUTH_COOLDOWN_MAX_RETRIES` is set to a positive number N and the cooldown tier has
  failed N times consecutively
- **THEN** the system makes no further automated authentication attempts until the process is
  restarted

### Requirement: The system never exits the process to stop retrying
When the system decides to permanently stop attempting authentication, it SHALL remain running
(not exit the process), so that a container restart policy that auto-restarts on process exit
cannot silently reset the failure counters and resume rapid authentication attempts.

#### Scenario: Permanent stop keeps the process alive
- **WHEN** the system has reached its configured permanent-stop condition
  (`AUTH_COOLDOWN_MAX_RETRIES` reached)
- **THEN** the process continues running and remains connected to MQTT, making no further
  authentication attempts, until it is manually restarted

### Requirement: Auth status is published to a retained MQTT topic
The system SHALL publish its authentication status to a retained MQTT topic (`ev/skoda/status`)
on every state transition: successful authentication, each fast-tier retry, each cooldown-tier
retry, and the terminal permanent-stop state.

#### Scenario: Successful authentication
- **WHEN** authentication succeeds
- **THEN** the system publishes a retained message to `ev/skoda/status` indicating a healthy
  state

#### Scenario: Permanent stop reached
- **WHEN** the system reaches the permanent-stop condition
- **THEN** the system publishes a retained message to `ev/skoda/status` indicating the
  terminal error state, including how many total authentication attempts were made
