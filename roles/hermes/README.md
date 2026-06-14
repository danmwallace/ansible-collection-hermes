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
| `hermes_image_tag` | str | no | `latest` | Image tag. Pin to a specific release tag in production. |
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
| `hermes_dashboard_port` | int | no | `9119` | Container port the dashboard binds to. |
| `hermes_dashboard_basic_auth_username` | str | no | `hermes` | Username for dashboard basic auth. |
| `hermes_dashboard_basic_auth_password` | str | yes* | `""` | Password for dashboard basic auth. Required when `hermes_dashboard_enabled`. **Supply from vault.** |
| `hermes_api_server_enabled` | bool | no | `true` | Enable the OpenAI-compatible API server. |
| `hermes_api_server_port` | int | no | `8642` | Container port the API server binds to. |
| `hermes_api_server_key` | str | yes* | `""` | API authentication key (minimum 8 characters). Required when `hermes_api_server_enabled`. **Supply from vault.** |
| `hermes_api_server_cors_origins` | str | no | `""` | Comma-separated CORS allowed origins. Empty disables CORS. |
| `hermes_traefik_enabled` | bool | no | `true` | When true, emits Traefik labels and joins `hermes_traefik_network`. |
| `hermes_traefik_network` | str | no | `proxy_network` | External Docker network Traefik listens on. |
| `hermes_domain` | str | yes* | `""` | Base domain for Traefik host rules (e.g. `lab.example.com`). Required when `hermes_traefik_enabled`. |
| `hermes_anthropic_api_key` | str | no | `""` | Anthropic API key passed as `ANTHROPIC_API_KEY` to the container. **Supply from vault.** |
| `hermes_openai_api_key` | str | no | `""` | OpenAI API key passed as `OPENAI_API_KEY` to the container. **Supply from vault.** |
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
3. Ensures `/opt/hermes` and `/opt/hermes/data` exist (`ansible:docker`, 0755).
4. Renders `data/.env` from `env.j2` (`ansible:docker`, 0600, `no_log`).
5. Renders `docker-compose.yml` from `docker-compose.yml.j2` (`ansible:docker`, 0600, `no_log`).
6. Brings the stack up via `community.docker.docker_compose_v2` (skipped when `hermes_skip_compose: true`).

A `Restart hermes compose project` handler fires when either rendered file changes, so config edits take effect without manual intervention. The handler is also skipped when `hermes_skip_compose: true`.

## Notes

- The `hermes_gateway` role in this same collection configures agent profiles, Discord gateways, and per-profile `SOUL.md` identity files. Apply it after this role on the same host. Both roles share `hermes_container_name` and `hermes_data_dir` — keep the values consistent.
- No host ports are published. Traffic reaches the dashboard and API server exclusively through Traefik. If you set `hermes_traefik_enabled: false`, you are responsible for exposing the ports.
- `hermes_image_tag` defaults to `latest`. Pin it to a digest or version tag before running in production to get reproducible deploys.

## License

MIT
