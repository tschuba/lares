## ADDED Requirements

### Requirement: Compose files reference only exact image versions
The system SHALL reference every container image in `docker-compose.yml` and
`docker-compose.pi.yml` by an exact version tag. The system SHALL NOT reference
`latest`, a bare major version, or a bare minor version for any service.

#### Scenario: Adding a new service to a compose file
- **WHEN** a new service is added to `docker-compose.yml` or `docker-compose.pi.yml`
- **THEN** its image tag SHALL be an exact version, not `latest` or a partial
  version

#### Scenario: Upgrading an existing pinned image
- **WHEN** an operator wants to move a service to a newer image version
- **THEN** the operator SHALL deliberately edit the image tag to the new exact
  version, rather than relying on a floating tag to advance on
  `docker compose pull`

### Requirement: Custom bridge images are only published on a GitHub Release
The system SHALL build and publish a new versioned image
(`ghcr.io/tschuba/lares/<image-name>:X.Y.Z`) for a given bridge only when a GitHub
Release with tag `<image-name>-vX.Y.Z` is published for that bridge. Pushing to
`main` SHALL continue to publish `latest`/`<branch>`/`<sha>` tags but SHALL NOT
advance any version tag referenced by production compose files.

#### Scenario: Merging a change to a bridge directory
- **WHEN** a commit touching `bridges/vallox/` is pushed to `main`
- **THEN** the workflow builds and publishes `vallox2mqtt:latest`,
  `vallox2mqtt:main`, and `vallox2mqtt:<sha>`, and does NOT publish or modify any
  `vallox2mqtt:X.Y.Z` tag

#### Scenario: Publishing a release for one bridge
- **WHEN** a GitHub Release with tag `vallox2mqtt-v1.3.0` is published
- **THEN** the workflow builds and publishes exactly
  `ghcr.io/tschuba/lares/vallox2mqtt:1.3.0`, and no other bridge's job runs

#### Scenario: Each bridge versions independently
- **WHEN** releases are published for two different bridges with different
  version numbers (e.g. `vallox2mqtt-v1.3.0` and `luxtronik2mqtt-v2.0.0`)
- **THEN** each bridge's published version reflects only its own release history,
  with no shared or repo-wide version number
