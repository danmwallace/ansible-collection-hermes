# danmwallace.hermes.hermes

Deploys [Hermes Agent](https://hermes-agent.nousresearch.com/) as a Docker Compose stack under `/opt/hermes`. The role renders `docker-compose.yml` (with all environment variables inline) and a separate `data/.env` (for secrets the agent reads from disk), then brings the stack up via `community.docker.docker_compose_v2`. When Traefik integration is enabled (the default), the role emits router and service labels so the Hermes dashboard and OpenAI-compatible API server are reachable by hostname through the external `proxy_network`.

The dashboard is accessible at `hermes-<inventory_hostname>.<hermes_domain>` and the API server at `hermes-api-<inventory_hostname>.<hermes_domain>`, both over the `websecure` (443) entrypoint with a Cloudflare TLS cert resolver.

## Requirements

- Ansible >= 2.16
- `community.docker` collection on the controller
- Target host with Docker installed and the Docker daemon running
- An `ansible` user and a `docker` group on the target host — the role chowns all files to `ansible:docker`
- When `hermes_traefik_enabled: true` (the default): an external `proxy_network` Docker network and a running Traefik instance with a `cloudflare` cert resolver (e.g. from `danmwallace.docker.traefik`)

## Role Variables

| Variable | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `hermes_image` | str | no | `nousresearch/hermes-agent` | Hermes Agent Docker image name. |
| `hermes_image_tag` | str | no | `v0.23.3` | Image tag, pinned to an upstream release. Set it in inventory to stay on a version across collection upgrades. |
| `hermes_container_name` | str | no | `hermes` | Name of the running container. Must match `hermes_gateway` role if both are applied to the same host. |
| `hermes_deploy_dir` | str | no | `/opt/hermes` | Host directory for `docker-compose.yml`. |
| `hermes_data_dir` | str | no | `/opt/hermes/data` | Host path mounted as `/opt/data` inside the container (persistent agent storage). |
| `hermes_uid` | int | no | `10000` | UID the container process runs as (PUID). |
| `hermes_gid` | int | no | `10000` | GID the container process runs as (PGID). |
| `hermes_memory_limit` | str | no | `4G` | Docker memory limit (e.g. `4G`). |
| `hermes_cpu_limit` | str | no | `2.0` | Docker CPU limit (e.g. `2.0`). |
| `hermes_browser_tools_enabled` | bool | no | `false` | When true, sets `shm_size` on the container for Playwright/Chromium support. |
| `hermes_shm_size` | str | no | `1g` | Shared memory size when `hermes_browser_tools_enabled` is true. |
| `hermes_dashboard_enabled` | bool | no | `true` | Enable the Hermes web dashboard (`HERMES_DASHBOARD=1`). |
| `hermes_dashboard_host` | str | no | `0.0.0.0` | Address the dashboard binds to inside the container. Must not be `127.0.0.1`; see **Notes**. |
| `hermes_dashboard_port` | int | no | `9119` | Container port the dashboard binds to. |
| `hermes_dashboard_basic_auth_username` | str | no | `hermes` | Username for dashboard basic auth. |
| `hermes_dashboard_basic_auth_password` | str | yes* | `""` | Password for dashboard basic auth. Required when `hermes_dashboard_enabled`. **Supply from vault.** |
| `hermes_api_server_enabled` | bool | no | `true` | Enable the OpenAI-compatible API server. |
| `hermes_api_server_host` | str | no | `0.0.0.0` | Address the API server binds to inside the container. Must not be `127.0.0.1`; see **Notes**. |
| `hermes_api_server_port` | int | no | `8642` | Container port the API server binds to. |
| `hermes_api_server_key` | str | yes* | `""` | API authentication key (minimum 8 characters). Required when `hermes_api_server_enabled`. **Supply from vault.** |
| `hermes_api_server_cors_origins` | str | no | `""` | Comma-separated CORS allowed origins. Empty disables CORS. |
| `hermes_traefik_enabled` | bool | no | `true` | When true, emits Traefik labels and joins `hermes_traefik_network`. |
| `hermes_traefik_network` | str | no | `proxy_network` | External Docker network Traefik listens on. |
| `hermes_domain` | str | yes* | `""` | Base domain for Traefik host rules (e.g. `lab.example.com`). Required when `hermes_traefik_enabled`. |
| `hermes_anthropic_api_key` | str | no | `""` | Anthropic API key passed as `ANTHROPIC_API_KEY` to the container. **Supply from vault.** |
| `hermes_openai_api_key` | str | no | `""` | OpenAI API key passed as `OPENAI_API_KEY` to the container. **Supply from vault.** |
| `hermes_terminal_env` | str | no | *(unset)* | Written to `data/.env` as `TERMINAL_ENV`, the terminal backend the Hermes setup wizard records there (e.g. `local`). Unset or empty leaves the line out. See **Notes**. |
| `hermes_discord_bot_token` | str | no | `""` | Discord bot token passed as `DISCORD_BOT_TOKEN`; makes this container the bot's gateway connection. Empty disables Discord here. See **Notes**. **Supply from vault.** |
| `hermes_discord_allowed_users` | list | yes* | `[]` | Discord user IDs allowed to talk to the bot. Required when `hermes_discord_bot_token` is set. |
| `hermes_discord_allowed_channels` | list | no | `[]` | Discord channel IDs the bot responds in. Empty means every channel the bot can see. |
| `hermes_default_model` | dict | no | `{}` | Global model merged into the live `config.yaml` as `model.provider` and `model.default` (plus `base_url` and `api_key` when `base_url` is set). Accepts `provider`, `model`, and optionally `base_url` and `api_key`. Empty leaves `model` alone. See **config.yaml**. |
| `hermes_config_extra` | dict | no | `{}` | Dict merged recursively into the live `config.yaml` after `hermes_default_model`. Removing a key here does not remove it from the host. See **config.yaml**. |
| `hermes_pull_policy` | str | no | `missing` | Image pull policy for `docker_compose_v2` (`always`, `missing`, `never`, `build`). |
| `hermes_skip_compose` | bool | no | `false` | Skip the `docker_compose_v2` deploy task and its handler. Set `true` in Molecule/CI environments without Docker access. |

*Required conditionally — see description.

## Dependencies

None declared in `meta/main.yml`. In practice the target host needs Docker installed. When `hermes_traefik_enabled: true` (the default), `danmwallace.docker.traefik` or equivalent must have created the external `proxy_network` Docker network.

## Example Playbook

```yaml
- hosts: ai_servers
  become: true
  roles:
    - role: danmwallace.hermes.hermes
      vars:
        hermes_domain: lab.example.com
        hermes_dashboard_basic_auth_password: "{{ vault_hermes_dashboard_basic_auth_password }}"
        hermes_api_server_key: "{{ vault_hermes_api_server_key }}"
        hermes_anthropic_api_key: "{{ vault_hermes_anthropic_api_key }}"
```

## What the Role Does

1. Asserts `hermes_dashboard_basic_auth_password` is non-empty when `hermes_dashboard_enabled` (prevents a locked-out dashboard on first deploy).
2. Asserts `hermes_api_server_key` is non-empty when `hermes_api_server_enabled`.
3. Asserts `hermes_discord_allowed_users` is non-empty when `hermes_discord_bot_token` is set.
4. Ensures `/opt/hermes` and `/opt/hermes/data` exist (`ansible:docker`, 0755).
5. Renders `data/.env` from `env.j2` (`ansible:docker`, 0600, `no_log`).
6. Renders `docker-compose.yml` from `docker-compose.yml.j2` (`ansible:docker`, 0600, `no_log`).
7. Merges `hermes_default_model` and `hermes_config_extra` into the live `data/config.yaml` and writes it only when the result differs (see **config.yaml**).
8. Brings the stack up via `community.docker.docker_compose_v2` (skipped when `hermes_skip_compose: true`).

A `Restart hermes compose project` handler fires when either rendered file changes, so config edits take effect without manual intervention. The handler is also skipped when `hermes_skip_compose: true`.

## config.yaml

Hermes writes `data/config.yaml` itself: `_config_version` after a migration, `gateway.multiplex_profiles`, `model.options` and settings changed from chat or the dashboard. So the role doesn't template it. It reads the live file, merges its keys in recursively, and writes the result (`hermes_uid:hermes_gid`, 0640, `no_log`) only when the merged mapping differs from what's on disk. Reformatting by Hermes is not a change. A debug task names the top-level keys that change, since `no_log` hides the diff. A write notifies the restart handler for the deploy mode.

- `hermes_default_model` sets `model.provider` and `model.default`, and removes the legacy `model.model` key, which Hermes reads in preference to `model.default`.
- `hermes_config_extra` is then merged on top. Keys Hermes wrote beside yours, at any depth, are kept.
- Removing a key from either variable leaves it on the host. Delete it from the file by hand.
- With both variables empty (the default) the file is never written.
- The role reads the file as root, so it refuses to run if `config.yaml` is a symlink or anything other than a regular file. The agent can write to the data directory, and a planted link would otherwise merge a root-only file into one the agent can read.

This is the merge `hermes_gateway` used to do, with the same variable names, so inventories that set them for that role work unchanged. Running both roles with the same values is harmless: the second merge finds nothing to change. Unlike `hermes_gateway`, this role doesn't write `gateway.platforms.discord`; Discord is configured through `hermes_discord_bot_token` and the container environment.

## Notes

- The `hermes_gateway` role (retired) in this same collection configures agent profiles, Discord gateways, and per-profile `SOUL.md` identity files. This role now does its `config.yaml` merge, so a host that used `hermes_gateway` only for that can drop it. If you still apply it, do so after this role on the same host. Both roles share `hermes_container_name` and `hermes_data_dir` — keep the values consistent.
- **One process per Discord bot token.** Discord delivers every message to every connection that logs in with a token, so two processes holding the same token both answer. Set the token in exactly one place per bot: `hermes_discord_bot_token` here, a `gateways` entry in `hermes_gateway`'s `hermes_profiles`, or `hermes_native_discord_bot_token`. Prefer this role when the container also owns scheduled jobs: cron delivery to Discord is blocked ("no gateway credentials configured") unless the process that runs the job holds the token, and this container is the one with persistent state under `hermes_data_dir`.
- **`data/.env` is rendered whole.** Any line the role doesn't template is removed on the next run, which also restarts Hermes. The setup wizard (`hermes setup`) writes `TERMINAL_ENV` there; on a host where it did, set `hermes_terminal_env` to the same value (check with `sudo grep ^TERMINAL_ENV= /opt/hermes/data/.env`).
- No host ports are published. Traffic reaches the dashboard and API server exclusively through Traefik. If you set `hermes_traefik_enabled: false`, you are responsible for exposing the ports.
- **Bind addresses are inside the container.** `hermes_dashboard_host` and `hermes_api_server_host` default to `0.0.0.0`. Setting them to `127.0.0.1` binds the container's own loopback, which Traefik (a separate container) cannot reach, so both endpoints return 502. Because no host ports are published, `0.0.0.0` is reachable only over the Podman network, and upstream requires auth on any non-loopback bind. A running container keeps its old values until it restarts, so a wrong value can stay hidden for weeks.
- `hermes_image_tag` defaults to a pinned upstream release (`v0.23.3`), and the default moves when the collection is updated. Set it in inventory if a collection upgrade must not also upgrade the container.

## License

MIT
