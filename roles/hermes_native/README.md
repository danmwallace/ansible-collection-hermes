# danmwallace.hermes.hermes_native

Installs [NousResearch hermes-agent](https://github.com/NousResearch/hermes-agent) natively on
Fedora Server as a pair of systemd services. The role creates a dedicated `hermes` OS user,
clones the source from GitHub, installs dependencies into a per-project `uv` venv, and runs the
gateway on port 8642 (`hermes-agent.service`) with an optional web UI on port 9119
(`hermes-dashboard.service`). Git identity, `gh` CLI auth, and an HTTPS credential helper are
also configured so the agent can clone, commit, and open pull requests as part of its coding
workflows.

When `hermes_native_dashboard_traefik_enabled: true`, the role drops a Traefik file-provider
route into `hermes_native_traefik_conf_dir` (default `/opt/podman/traefik/conf.d`) so the
dashboard is reachable over HTTPS without further configuration.

## Requirements

- Ansible >= 2.16
- Fedora Server (the role installs Fedora-specific packages via `dnf`)
- `become: true` on the play — most tasks require root to write system files
- A running Traefik instance with a `cloudflare` cert resolver and the `conf.d/` directory
  provider configured (e.g. from `danmwallace.podman.traefik`) when
  `hermes_native_dashboard_traefik_enabled: true`

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
| `hermes_native_repo_version` | str | no | `main` | Branch or tag to check out. |
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
| `hermes_native_traefik_conf_dir` | str | no | `/opt/podman/traefik/conf.d` | Directory where Traefik file-provider route files are written. |
| `hermes_native_dashboard_traefik_enabled` | bool | no | `false` | When true, write a Traefik route file for the dashboard. |
| `hermes_native_dashboard_traefik_hostname` | str | no | `""` | FQDN Traefik routes to the dashboard (e.g. `hermes-dash.example.com`). Required when `hermes_native_dashboard_traefik_enabled: true`. |

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
   `package-lock.json` modifications from the dashboard npm build), creates a Python 3.11 venv
   via `uv venv`, and runs `uv sync --extra all --locked` on version changes.
7. **Configure systemd services**: renders `/etc/hermes-agent/env` (EnvironmentFile with all
   API keys and server config), renders `~/config.yaml` (approvals policy and API server
   platform config), writes `hermes-agent.service` (`hermes gateway run`), and — when
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

- **Two services, one agent**: `hermes-agent.service` runs `hermes gateway run` (the
  OpenAI-compatible API server). `hermes-dashboard.service` runs `hermes dashboard --insecure`
  (the web UI). They are separate processes — unlike the Docker image which uses s6-rc to
  supervise both under a single container entrypoint.
- **config.yaml ownership**: the role writes `~/config.yaml` via template, so manual edits
  (e.g. enabling channels via the dashboard UI) will be overwritten on the next play run.
  Add any persistent config to `hermes_native_approvals_cron_mode` or the role defaults.
- **Platform-specific**: the role targets Fedora only. `dnf` tasks will fail on Debian/Ubuntu
  hosts.

## License

MIT
