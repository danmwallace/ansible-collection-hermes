# Changelog

All notable changes to this collection will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-06-21

### Added

- `hermes_native`: `hermes-dashboard.service` — separate systemd unit that runs
  `hermes dashboard` so the web UI is available on the native install (Docker's
  s6-rc supervision is not available outside the container).
- `hermes_native`: `config.yaml.j2` template — manages `/home/hermes/config.yaml`
  for `approvals.cron_mode` and `platforms.api_server.enabled`, making both
  settings idempotent under Ansible.
- `hermes_native`: Traefik file-provider route template
  (`hermes-dashboard.traefik.yml.j2`) — exposes the native dashboard over HTTPS
  via Traefik's `conf.d/` directory when
  `hermes_native_dashboard_traefik_enabled: true`.
- `hermes_native`: `hermes_native_api_server_model_name` variable (default:
  `hermes-agent`) written to the systemd env file as `API_SERVER_MODEL_NAME`.
- `hermes`: `hermes_api_server_model_name` variable (default: `hermes-agent`)
  rendered as `API_SERVER_MODEL_NAME` in the Quadlet container unit.
- `hermes`: `API_SERVER_PORT` rendered in the Quadlet container unit from
  `hermes_api_server_port` (was present in defaults but missing from the unit).

### Fixed

- `hermes_native`: `force: true` added to the `ansible.builtin.git` task to
  prevent idempotency failures caused by npm modifying `package-lock.json`
  during the dashboard build step.
- `hermes_native`: replaced SSH deploy key with HTTPS gh credential helper for
  simpler repository access.
- `hermes_native`: corrected `ExecStart` to use `hermes gateway run` instead of
  bare `hermes`.

## [1.1.0] - 2026-06-14

### Added

- `hermes_native` role — install NousResearch hermes-agent natively on Fedora Server
  as a systemd service with dedicated `hermes` OS user, SSH deploy key, gh CLI auth,
  and git tooling for coding-agent workflows (code review, PR submission).

## [1.0.2] - 2026-06-14

### Fixed

- `galaxy.yml`: add required Galaxy taxonomy tags (`linux`, `infrastructure`)
- `meta/runtime.yml`: add patch segment to `requires_ansible` (`>=2.16.0`)

## [1.0.1] - 2026-06-14

### Fixed

- Corrected `galaxy.yml` description and tags to reflect Podman Quadlet deployment (not Docker Compose)
- Updated collection dependencies from `community.docker` to `containers.podman`, `ansible.posix`, `community.general`

## [1.0.0] - 2026-06-14

### Added

- `danmwallace.hermes.hermes` role — deploy Hermes AI agent as a Podman Quadlet on Fedora
- `danmwallace.hermes.hermes_gateway` role — deploy Hermes Gateway (TUI gateway with Traefik routing) as a Podman Quadlet on Fedora
