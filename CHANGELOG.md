# Changelog

All notable changes to this collection will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.3] - 2026-10-04

### Fixed

- `hermes_native`: the SELinux labelling now follows `hermes_native_install_dir`
  instead of a hardcoded `~/hermes-agent`, so an overridden install directory
  no longer reintroduces the `203/EXEC` failure.

## [1.4.2] - 2026-10-04

### Fixed

- `hermes_native`: the `restorecon` task reported changed on every run because
  `restorecon -v` also lists files it leaves alone ("customized by admin");
  it now reports changed only when a file was actually relabeled.

## [1.4.1] - 2026-10-04

### Fixed

- `hermes_native`: the agent and dashboard units failed with `203/EXEC` under
  SELinux enforcing because systemd (`init_t`) may not execute `user_home_t`
  files. The role now sets `bin_t` file contexts for the venv entry points and
  uv's Python (resolving `/home` to its real path for bootc hosts) and runs
  `restorecon`. Previously only hosts labelled by hand worked.
- `hermes_native`: `uv sync --frozen` so the lockfile is never rewritten; the
  clone (`force: true`) and the sync no longer report changed on every run.

## [1.4.0] - 2026-10-04

### Added

- `hermes_native` and `claude_code` skip their dnf and yum-repo tasks on
  bootc/rpm-ostree hosts (`/run/ostree-booted`), where `/usr` is read-only and
  the image carries the packages. New molecule scenario `ostree` for
  `hermes_native` proves nothing is installed in that mode.

## [1.3.3] - 2026-09-12

### Fixed

- Removed two internal session-note files under `.superpowers/` that were committed by
  mistake with 1.3.2. They held no credentials. The directory is now in `.gitignore`.
- `build_ignore` excludes local-only paths (`.ansible`, `.claude`, `.superpowers`, `.venv`,
  `dist`, `*.tar.gz`), so a manual build from a working checkout cannot ship them.
- 1.3.2 was tagged but never published to Galaxy: its release run failed on a stale
  `GALAXY_API_KEY`. 1.3.3 carries the same bind-address fix without the stray files.

## [1.3.2] - 2026-09-12

### Fixed

- `hermes`, `hermes_gateway`: bind the dashboard and API server to `0.0.0.0` inside the
  container again. 1.3.0 changed these defaults (`hermes_dashboard_host`,
  `hermes_api_server_host`, `hermes_gateway_api_server_host`) to `127.0.0.1`, which is
  the container's own loopback: Traefik, a separate container on the Podman network,
  got connection refused and served 502. Running containers kept their old settings
  until their next restart, so the break surfaced later (ai-master gateway on
  2026-09-04, ai01 dashboard and API on 2026-09-12). No host ports are published, and
  upstream requires auth on any non-loopback bind. `hermes_native` keeps its
  `127.0.0.1` defaults, which are correct for a process on the host.

## [1.2.7] - 2026-07-29

### Added

- `hermes_gateway`: `hermes_gateway_discord_allowed_users`,
  `hermes_gateway_discord_allowed_channels`, and `hermes_gateway_discord_admin_users`
  variables — passed as `DISCORD_ALLOWED_USERS`, `DISCORD_ALLOWED_CHANNELS`, and
  `DISCORD_ADMIN_USERS` env vars to the gateway container (same env-var-first approach
  used by `hermes_native` since v1.2.3 to avoid config.yaml translation bugs).

### Fixed

- `hermes_gateway`: removed hardcoded `GATEWAY_ALLOW_ALL_USERS=true` from the Quadlet
  container unit — replaced with scoped Discord env vars derived from `hermes_profiles`
  gateway dict and the new `hermes_gateway_discord_*` variables.
- `hermes_gateway`: `argument_specs.yml` `hermes_gateway_port` default corrected from
  `3000` to `8642` to match `defaults/main.yml`.

## [1.2.6] - 2026-07-02

### Fixed

- `claude_code`: add missing `README.md` (Galaxy import requirement)

## [1.2.5] - 2026-07-02

### Changed

- `hermes`: pin `hermes_image_tag` from `latest` to `v2026.7.1` (date-based versioning)
- `hermes_gateway`: pin `hermes_gateway_image_tag` from `latest` to `v2026.7.1`

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
