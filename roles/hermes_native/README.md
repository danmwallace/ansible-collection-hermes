# danmwallace.hermes.hermes_native

Installs [NousResearch hermes-agent](https://github.com/NousResearch/hermes-agent) natively on
Fedora Server as a pair of systemd services. The role creates a dedicated `hermes` OS user,
clones the source from GitHub, installs dependencies into a per-project `uv` venv, and runs the
gateway on port 8642 (`hermes-agent.service`) with an optional web UI on port 9119
(`hermes-dashboard.service`). Git identity, `gh` CLI auth, and an HTTPS credential helper are
also configured so the agent can clone, commit, and open pull requests as part of its coding
workflows.

When `hermes_native_dashboard_traefik_enabled: true` or `hermes_native_api_server_traefik_enabled: true`,
the role drops a Traefik file-provider route into `hermes_native_traefik_conf_dir` (default
`/opt/podman/traefik/conf.d`) so the dashboard and/or the OpenAI-compatible API server are
reachable over HTTPS without further configuration. Traefik reaches the host process through
`host.containers.internal`, so the corresponding `hermes_native_dashboard_host` or
`hermes_native_api_server_host` must not be `127.0.0.1` (use `0.0.0.0`; Traefik is the TLS and
auth boundary, and the API server requires its key on any non-loopback bind).

## Requirements

- Ansible >= 2.16
- Fedora Server (the role installs Fedora-specific packages via `dnf`)
- On bootc/rpm-ostree hosts (`/run/ostree-booted` present) the role skips its dnf and
  yum-repo tasks; the image must already provide git, make, jq, yq, ripgrep, python3,
  python3-pip, curl, nodejs, npm and gh.
- `become: true` on the play — most tasks require root to write system files
- A running Traefik instance with a `cloudflare` cert resolver and the `conf.d/` directory
  provider configured (e.g. from `danmwallace.podman.traefik`) when
  `hermes_native_dashboard_traefik_enabled: true` or `hermes_native_api_server_traefik_enabled: true`

## Role Variables

| Variable | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `hermes_native_anthropic_api_key` | str | **yes** | `""` | Anthropic API key (`ANTHROPIC_API_KEY`). **Supply from vault.** |
| `hermes_native_api_server_key` | str | **yes** | `""` | API authentication key (min 8 chars) for the OpenAI-compatible endpoint. **Supply from vault.** |
| `hermes_native_dashboard_password` | str | **yes** | `""` | Basic auth password for the web dashboard. **Supply from vault.** |
| `hermes_native_gh_token` | str | **yes** | `""` | Fine-grained GitHub PAT for `gh` CLI auth. **Supply from vault.** |
| `hermes_native_user` | str | no | `hermes` | OS user the agent runs as. |
| `hermes_native_install_dir` | str | no | `/home/hermes/hermes-agent` | Directory where the source is cloned and the venv is created. |
| `hermes_native_repo_url` | str | no | `https://github.com/NousResearch/hermes-agent` | Git URL for the hermes-agent source repo. |
| `hermes_native_repo_version` | str | no | `v0.23.0` | Branch or tag to check out. The default is a pinned upstream release and moves when the collection is updated; set it in inventory to stay on a version. |
| `hermes_native_python_version` | str | no | `"3.14"` | Python (major.minor) the venv is built with. Upstream supports one Python per release and `uv.lock` only resolves for it (3.14 since v0.23.0); a venv built with another version is removed, rebuilt and re-synced. Change it together with `hermes_native_repo_version` when a release moves to a new Python. |
| `hermes_native_workspace_dir` | str | no | `/home/hermes/workspace` | Pre-created directory for repos the agent will work on. |
| `hermes_native_git_user_name` | str | no | `Hermes` | `git config user.name` for the hermes user. |
| `hermes_native_git_user_email` | str | no | `hermes@wallace.boston` | `git config user.email` for the hermes user. |
| `hermes_native_api_server_port` | int | no | `8642` | Port the OpenAI-compatible API server listens on. |
| `hermes_native_api_server_model_name` | str | no | `hermes-agent` | Model name advertised by the API server (`API_SERVER_MODEL_NAME`). |
| `hermes_native_env_file` | str | no | `/etc/hermes-agent/env` | Path of the `EnvironmentFile` read by the systemd service unit. |
| `hermes_native_dashboard_enabled` | bool | no | `true` | When true, render and start `hermes-dashboard.service`. |
| `hermes_native_dashboard_port` | int | no | `9119` | Port the web dashboard listens on. |
| `hermes_native_dashboard_username` | str | no | `hermes` | Basic auth username for the dashboard. |
| `hermes_native_approvals_cron_mode` | str | no | `deny` | Value written to `config.yaml` as `approvals.cron_mode` (`deny`, `allow`, or `auto`). |
| `hermes_native_config_extra` | dict | no | `{}` | Extra `config.yaml` keys merged on top of the role-managed ones (e.g. a `moa` preset, `max_concurrent_sessions`). Removing a key here does not remove it from the host. |
| `hermes_native_traefik_conf_dir` | str | no | `/opt/podman/traefik/conf.d` | Directory where Traefik file-provider route files are written. |
| `hermes_native_dashboard_traefik_enabled` | bool | no | `false` | When true, write a Traefik route file for the dashboard. |
| `hermes_native_dashboard_traefik_hostname` | str | no | `""` | FQDN Traefik routes to the dashboard (e.g. `hermes-dash.example.com`). Required when `hermes_native_dashboard_traefik_enabled: true`. |
| `hermes_native_api_server_traefik_enabled` | bool | no | `false` | When true, write a Traefik route file for the API server. Fails if `hermes_native_api_server_host` is `127.0.0.1`. |
| `hermes_native_api_server_traefik_hostname` | str | no | `""` | FQDN Traefik routes to the API server (e.g. `hermes-api.example.com`). Required when `hermes_native_api_server_traefik_enabled: true`. |
| `hermes_native_nopasswd_sudo` | bool | no | `false` | When true, writes `/etc/sudoers.d/hermes` granting the hermes user passwordless sudo. |
| `hermes_native_sudo_commands` | list | no | `[]` | Restrict passwordless sudo to specific command paths. When non-empty (and `hermes_native_nopasswd_sudo: true`), only these commands are allowed instead of `ALL`. E.g. `["/usr/bin/systemctl", "/usr/bin/podman"]`. |

## Dependencies

None declared in `meta/main.yml`. In practice the target host must have internet access to clone
the hermes-agent source from GitHub. When `hermes_native_dashboard_traefik_enabled: true`, a
running Traefik instance with a `conf.d/` file provider is expected (provided by
`danmwallace.podman.traefik`).

## Example Playbook

```yaml
- hosts: ai_agents
  become: true
  roles:
    - role: danmwallace.hermes.hermes_native
      vars:
        hermes_native_anthropic_api_key: "{{ vault_hermes_native_anthropic_api_key }}"
        hermes_native_api_server_key: "{{ vault_hermes_native_api_server_key }}"
        hermes_native_dashboard_password: "{{ vault_hermes_native_dashboard_password }}"
        hermes_native_gh_token: "{{ vault_hermes_native_gh_token }}"
        hermes_native_approvals_cron_mode: allow
        hermes_native_dashboard_traefik_enabled: true
        hermes_native_dashboard_traefik_hostname: hermes-dash.example.com
```

## What the Role Does

1. **Assert secrets**: fails fast if `hermes_native_anthropic_api_key` or
   `hermes_native_api_server_key` is empty.
2. **Create user and workspace**: creates the `hermes` system user with a home directory and
   the `hermes_native_workspace_dir` for agent repo work.
3. **Install system packages**: installs `git`, `nodejs`, `npm`, and build tools via `dnf`.
4. **Install uv**: downloads and installs `uv` into the hermes user's home.
5. **Install gh CLI**: installs the GitHub CLI via the GitHub RPM repository.
6. **Clone and build hermes-agent**: clones the source repo (`force: true` to handle
   `package-lock.json` modifications from the dashboard npm build), creates the venv with
   `uv venv --python hermes_native_python_version` (rebuilding it when the existing venv was
   made with another Python), and runs `uv sync --frozen --extra all` when the source or the
   venv changed.
7. **Configure systemd services**: renders `/etc/hermes-agent/env` (EnvironmentFile with all
   API keys and server config), merges the Ansible-owned keys into `~/config.yaml` (see
   Notes), writes `hermes-agent.service` (`hermes gateway run`), and — when
   `hermes_native_dashboard_enabled: true` — writes `hermes-dashboard.service` (`hermes
   dashboard --insecure`). Both units are enabled and started.
8. **Register with Traefik**: when `hermes_native_dashboard_traefik_enabled: true`, writes
   `hermes-dashboard.yml` into `hermes_native_traefik_conf_dir` so Traefik picks up the HTTPS
   route automatically.
9. **Configure git and gh**: sets `user.name`/`user.email` globally for the hermes user,
   configures an HTTPS credential helper backed by `gh auth token`, and authenticates `gh`
   with `hermes_native_gh_token`.

`Restart hermes-agent service` and `Restart hermes-dashboard service` handlers fire when the
env file, config.yaml, or the respective systemd unit changes.

## Notes

- **One process per Discord bot token**: when `hermes_native_discord_bot_token` is set, the
  native agent is the bot's gateway connection. Do not give the same token to `hermes_gateway`
  or the `hermes` role as well; every process holding it receives and answers every message.
- **Two services, one agent**: `hermes-agent.service` runs `hermes gateway run` (the
  OpenAI-compatible API server). `hermes-dashboard.service` runs `hermes dashboard --insecure`
  (the web UI). They are separate processes — unlike the Docker image which uses s6-rc to
  supervise both under a single container entrypoint.
- **config.yaml ownership**: since 1.8.0 the role merges into `~/config.yaml` (and each
  `~/profiles/<name>/config.yaml`) instead of replacing it. Ansible owns `model`, `approvals`,
  `platforms.api_server`, `gateway.platforms.discord` and whatever is in
  `hermes_native_config_extra`; keys Hermes writes itself (`_config_version` after a
  migration, the `/sethome` channel, `model.options`, onboarding flags) survive a play run,
  and the file is only rewritten when the merged mapping differs from the live one. Two
  consequences: a value changed from the dashboard that Ansible also declares is reverted on
  the next run, and a key removed from Ansible stays on the host until removed by hand. The
  legacy `model.model` key written by releases up to 1.7.0 is dropped on the first run
  because Hermes reads it in preference to `model.default`.
- **Platform-specific**: the role targets Fedora only. `dnf` tasks will fail on Debian/Ubuntu
  hosts.

## License

MIT
