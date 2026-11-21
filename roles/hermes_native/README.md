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
| `hermes_native_profiles` | list of dict | no | `[]` | Additional profiles, served at `/p/<name>/`. Each entry has `name` (required), `config` (merged into `~/profiles/<name>/config.yaml`), and an optional `api_server_key`: the profile's own key, at least 16 characters, written to `~/profiles/<name>/.env`. **Supply `api_server_key` from vault.** |
| `hermes_native_dashboard_password` | str | **yes** | `""` | Basic auth password for the web dashboard. **Supply from vault.** |
| `hermes_native_gh_token` | str | **yes** | `""` | GitHub token for `gh` CLI auth: a classic PAT for a machine account (fine-grained tokens can't reach another personal account's repos), or a fine-grained PAT. Any other github.com account `gh` holds is logged out. **Supply from vault.** |
| `hermes_native_user` | str | no | `hermes` | OS user the agent runs as. |
| `hermes_native_install_dir` | str | no | `/home/hermes/hermes-agent` | Directory where the source is cloned and the venv is created. |
| `hermes_native_repo_url` | str | no | `https://github.com/NousResearch/hermes-agent` | Git URL for the hermes-agent source repo. |
| `hermes_native_repo_version` | str | no | `v0.23.3` | Branch or tag to check out. The default is a pinned upstream release and moves when the collection is updated; set it in inventory to stay on a version. |
| `hermes_native_python_version` | str | no | `"3.14"` | Python (major.minor) the venv is built with. Upstream supports one Python per release and `uv.lock` only resolves for it (3.14 since v0.23.0); a venv built with another version is removed, rebuilt and re-synced. Change it together with `hermes_native_repo_version` when a release moves to a new Python. |
| `hermes_native_uv_extras` | list | no | `[all, discord]` | Extras for `uv sync --extra`. Since v0.23.0 upstream's `all` covers tooling only; messaging platforms (`discord`, `telegram`, ...) are separate extras. The list is recorded in `venv/.ansible-uv-extras`; changing it re-runs the sync. |
| `hermes_native_workspace_dir` | str | no | `/home/hermes/workspace` | Pre-created directory for repos the agent will work on. |
| `hermes_native_git_user_name` | str | no | `Hermes` | `git config user.name` for the hermes user. |
| `hermes_native_git_user_email` | str | no | `hermes@wallace.boston` | `git config user.email` for the hermes user. |
| `hermes_native_git_signing_key` | str | no | `""` | Path to a public key the hermes user signs commits and tags with (`gpg.format ssh`, `commit.gpgsign`, `tag.gpgsign`). Empty leaves signing off, and clearing it unsets those keys. |
| `hermes_native_api_server_port` | int | no | `8642` | Port the OpenAI-compatible API server listens on. |
| `hermes_native_api_server_model_name` | str | no | `hermes-agent` | Model name advertised by the API server (`API_SERVER_MODEL_NAME`). |
| `hermes_native_env_file` | str | no | `/etc/hermes-agent/env` | Path of the `EnvironmentFile` read by the systemd service unit. |
| `hermes_native_dashboard_enabled` | bool | no | `true` | When true, render and start `hermes-dashboard.service`. |
| `hermes_native_dashboard_port` | int | no | `9119` | Port the web dashboard listens on. |
| `hermes_native_dashboard_username` | str | no | `hermes` | Basic auth username for the dashboard. |
| `hermes_native_approvals_mode` | str | no | `smart` | `approvals.mode`: `smart` (a guardian model approves low-risk flagged commands and escalates the rest), `manual` (always ask) or `off`. Quote `"off"`; the role refuses a non-string, because Hermes reads a bare YAML `off` (false) as off without warning. |
| `hermes_native_approvals_cron_mode` | str | no | `deny` | `approvals.cron_mode`: `deny` blocks a flagged command in a cron run, `approve` (or `allow`) runs it. Hermes reads any other value, such as `auto`, as `deny`, so the role refuses it. The role checks both settings in `hermes_native_config_extra` and every profile too. |
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
        hermes_native_approvals_cron_mode: approve
        hermes_native_dashboard_traefik_enabled: true
        hermes_native_dashboard_traefik_hostname: hermes-dash.example.com
```

## What the Role Does

1. **Assert secrets**: fails fast if `hermes_native_anthropic_api_key` or
   `hermes_native_api_server_key` is empty.
2. **Create user and workspace**: creates the `hermes` system user with a home directory and
   the `hermes_native_workspace_dir` for agent repo work.
3. **Install system packages**: installs `git`, `nodejs`, `npm`, `libatomic` (for the node Hermes' runtime manager stages itself) and build tools via `dnf`.
4. **Install uv**: downloads and installs `uv` into the hermes user's home.
5. **Install gh CLI**: installs the GitHub CLI via the GitHub RPM repository.
6. **Clone and build hermes-agent**: clones the source repo (`force: true` to handle
   `package-lock.json` modifications from the dashboard npm build), creates the venv with
   `uv venv --python hermes_native_python_version` (rebuilding it when the existing venv was
   made with another Python), and runs `uv sync --frozen` with `hermes_native_uv_extras` when the source, the venv or
   the extras list changed.
7. **Configure systemd services**: renders `/etc/hermes-agent/env` (EnvironmentFile with all
   API keys and server config), merges the Ansible-owned keys into `~/config.yaml` (see
   Notes), writes `hermes-agent.service` (`hermes gateway run`), and — when
   `hermes_native_dashboard_enabled: true` — writes `hermes-dashboard.service` (`hermes
   dashboard --insecure`). Both units are enabled and started.
8. **Register with Traefik**: when `hermes_native_dashboard_traefik_enabled: true`, writes
   `hermes-dashboard.yml` into `hermes_native_traefik_conf_dir` so Traefik picks up the HTTPS
   route automatically.
9. **Configure git and gh**: sets `user.name`/`user.email` globally for the hermes user
   (plus SSH commit signing when `hermes_native_git_signing_key` is set), configures an HTTPS
   credential helper backed by `gh auth token`, authenticates `gh` with
   `hermes_native_gh_token`, and logs out every other github.com account `gh` holds.
10. **Provision profiles**: for each `hermes_native_profiles` entry, creates
    `~/profiles/<name>/` (0700) and merges its `config` into `config.yaml`. For entries with
    `api_server_key`, it checks that each key is at least 16 characters, then makes sure the
    line `API_SERVER_KEY=<key>` is in `~/profiles/<name>/.env` (0600, `no_log`), writing as
    the hermes user so a planted symlink can't redirect a root write. Only that line is managed.

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
- **A profile's own key**: Hermes v0.23 serves each profile at `/p/<name>/` and accepts only that profile's `API_SERVER_KEY`, read from its `.env`.
  - A profile with no key of its own refuses every request rather than accept the default key.
  - A key shorter than 16 characters is ignored, which is why the role refuses one.
  - Use this for a client that should reach one profile only, such as a desktop agent with its own revocable key.
  - **Revoking or rotating:** removing `api_server_key` from the inventory leaves the line in place, so the old key keeps working. To revoke, delete the `API_SERVER_KEY=` line from `~/profiles/<name>/.env` and restart `hermes-agent`; to rotate, set a new value and run the role. Runs started under the old key are tied to it, so after a rotation they answer 404.
  - **Written as the hermes user:** the profile folder, `config.yaml` and `.env` are all written as the hermes user, never root. The folder belongs to the agent, so a symlink it plants there can't redirect a root write or chown.
  - The molecule scenario `profiles` (`molecule test -s profiles`) checks:
    - the `.env` line and its mode, and that other lines are kept;
    - that a short key fails without being shown;
    - that a planted symlink, on `.env` or on the profile folder, leaves the root-owned target untouched;
    - that the key appears nowhere in `-vvv` output.
- **Swapping the GitHub identity**: `gh auth login --with-token` with a token for another
  account adds that account next to the old one and makes it active. The old token stays in
  `~/.config/gh/hosts.yml`, one `gh auth switch` away. So the role logs out every github.com
  account except the active one; the first run after a swap reports that logout as a change.
- **Signed commits need the key on GitHub too**: register the same public key on the account
  as a *signing* key (separate from an authentication key), or GitHub shows the commits as
  "Unverified". Pushes go over HTTPS with the `gh` token, so the key doesn't need to be an
  authentication key unless something pushes over SSH.
- **Platform-specific**: the role targets Fedora only. `dnf` tasks will fail on Debian/Ubuntu
  hosts.

## License

MIT
