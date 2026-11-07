# Changelog

All notable changes to this collection will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.8.1] - 2026-11-07

### Added

- `hermes_native`: `hermes_native_python_version` (default `"3.14"`), the Python the
  venv is built with.

### Fixed

- `hermes_native`: the venv was pinned to Python 3.11 and never revisited, so
  upgrading to v0.23.0 (whose `uv.lock` only supports Python 3.14) failed in
  `uv sync --frozen` with "The current Python platform is not compatible with the
  lockfile's supported environments". The role now reads the venv's `pyvenv.cfg`,
  removes and recreates the venv when its Python differs from
  `hermes_native_python_version`, and runs `uv sync` whenever the venv was
  (re)created, not only when the source changed.

## [1.8.0] - 2026-11-07

### Added

- `hermes_native`: `hermes_native_config_extra`, a mapping merged on top of the
  role-managed `config.yaml` keys (for a `moa` preset, `max_concurrent_sessions`
  and the like), mirroring `hermes_config_extra` in `hermes_gateway`.

### Changed

- `hermes_native`: `~/config.yaml` and the `~/profiles/<name>/config.yaml` files
  are no longer rendered from templates. The role reads the live file, merges
  the Ansible-owned keys into it (`model`, `approvals`, `platforms.api_server`,
  `gateway.platforms.discord`, `hermes_native_config_extra`; the declared
  mapping for profiles) and writes it back only when the merged mapping
  differs. Keys Hermes writes itself (`_config_version`, the `/sethome`
  channel, `model.options`, onboarding flags) therefore survive a play run,
  and a run after Hermes reformatted the file reports no change. The model is
  written as `model.default` (the key Hermes writes) and the legacy
  `model.model` key is dropped on the first run, since Hermes prefers it and it
  would otherwise pin the old model. `approvals.mode` is now quoted, so `off`
  reaches Hermes as the string it expects rather than YAML `false`.
- `hermes_native`: `hermes-agent.service` sets `TimeoutStopSec=90` so Hermes
  can drain cron and chat turns on stop (it warned about the 45s default).

### Fixed

- `hermes_native`: check mode no longer fails in the SELinux tasks; the
  read-only `readlink` command now runs in check mode so the facts it feeds
  exist.

## [1.7.0] - 2026-11-06

### Added

- `hermes_native`: `hermes_native_api_server_traefik_enabled` and
  `hermes_native_api_server_traefik_hostname` write a Traefik file-provider
  route (`conf.d/hermes-api.yml`) for the native agent's OpenAI-compatible API
  server, the same way the dashboard route works. The role asserts that
  `hermes_native_api_server_host` is not loopback, since Traefik reaches the
  host process through `host.containers.internal`.
- `hermes_gateway`: `hermes_gateway_container_state` (`present`/`absent`,
  quadlet mode only). `absent` stops and removes the `hermes-gateway`
  container and its Quadlet unit while still rendering `config.yaml`,
  profiles and `SOUL.md` for the `hermes` role's container, so a host can
  retire the gateway container once another process owns Discord and the
  API.

### Changed

- `hermes_gateway`: in quadlet mode a change to `config.yaml` or any
  `SOUL.md` now also restarts `<hermes_container_name>.service`, so the
  `hermes` role's container picks up the new config. Hosts without that unit
  are tolerated.

## [1.6.0] - 2026-11-06

### Changed

- Default Hermes versions moved to upstream `v0.23.0`: `hermes_image_tag` and
  `hermes_gateway_image_tag` (were `v2026.7.1`) and
  `hermes_native_repo_version` (was `v2026.8.31`). Upstream switched from
  date-based to semver tags after `v2026.9.24`; the old tags still exist.
  **Upgrade note:** a host that does not set these variables will pull the new
  image, or check out and rebuild the native agent, on its next run. Set them
  in inventory first to stay on the current version.

### Fixed

- `argument_specs` and READMEs stated `latest` (and `main`) as the defaults
  for the three version variables while `defaults/main.yml` pinned a release;
  all three now agree.

## [1.5.0] - 2026-11-06

### Added

- `hermes`: optional Discord ownership for the main container via
  `hermes_discord_bot_token`, `hermes_discord_allowed_users` and
  `hermes_discord_allowed_channels` (rendered as `DISCORD_*` environment
  variables in both the Quadlet unit and the compose file). The role asserts
  an allowlist whenever a token is set. Use this instead of a `hermes_gateway`
  Discord gateway when the main container owns scheduled jobs: since
  v2026.9.x a cron job that delivers to Discord is blocked ("no gateway
  credentials configured") unless the process running it holds the token.

### Changed

- READMEs: document that a Discord bot token must be given to exactly one
  process. Two processes with the same token both receive and answer every
  message.

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
