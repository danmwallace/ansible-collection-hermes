# Changelog

All notable changes to this collection will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.4] - 2026-06-30

### Added

- `claude_code`: new role — installs Claude Code CLI for the `hermes` user and
  writes a `settings.json` scoping it to Hermes orchestration context.
- `hermes_native`: profile provisioning support (`tasks/profiles.yml`,
  `templates/profile_config.yaml.j2`) — idempotently renders per-profile
  `config.yaml` files under `HERMES_HOME`.

## [1.2.3] - 2026-06-30

### Added

- `hermes_native`: Discord gateway support — `DISCORD_BOT_TOKEN` and
  `DISCORD_ALLOWED_USERS` written to the systemd env file when
  `hermes_native_discord_bot_token` is set (direct env-var approach bypasses
  a YAML-to-env translation bug in the gateway's `_apply_yaml_config` hook).
- `hermes_native`: `gateway.platforms.discord` block written to `config.yaml`
  with `token`, `require_mention`, and YAML-list `allow_from` / `allow_admin_from`.
- `hermes_native`: `hermes_native_discord_bot_token`, `hermes_native_discord_allowed_users`,
  `hermes_native_discord_admin_users`, and `hermes_native_discord_require_mention`
  variables (default: `require_mention: true`).
- `hermes_native`: `hermes_native_nopasswd_sudo` — writes `/etc/sudoers.d/hermes`
  with `NOPASSWD: ALL` when `true`, removes the file when `false`. Validated via
  `visudo -cf` before applying.
- `hermes_native`: `hermes_native_model` (default: `claude-sonnet-4-6`) and
  `hermes_native_model_provider` (default: `anthropic`) — written to `config.yaml`
  as `model.model` / `model.provider`, preventing the gateway from falling back to
  `claude-fable-5` which is unavailable on standard Anthropic API keys.

## [1.2.2] - 2026-06-21

### Added

- `hermes_native`: `hermes_native_approvals_mode` variable (default: `"manual"`) written
  to `config.yaml` as `approvals.mode`; set to `"off"` to disable all approval prompts.

## [1.2.1] - 2026-06-21

### Fixed

- `hermes`: restore `hermes_google_client_id`, `hermes_google_client_secret`,
  `hermes_gmail_refresh_token`, and `hermes_gcal_refresh_token` defaults (empty
  strings) that were accidentally removed in v1.2.0; `env.j2` references them in a
  conditional block so their absence caused an undefined-variable error on every run.

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
