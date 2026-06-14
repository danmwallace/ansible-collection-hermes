# danmwallace.hermes.hermes_gateway

Configures [Hermes Agent](https://hermes-agent.nousresearch.com/) profiles, gateway connections, and per-profile identity files on a host where the `danmwallace.hermes.hermes` role has already deployed the container. The role templates `config.yaml` (global model selection and Discord gateway config) and per-profile `SOUL.md` identity files into the Hermes data directory, then optionally runs `hermes profile create` inside the container via `docker exec` to register any new profiles.

This role is re-runnable independently of the `hermes` role — it can be applied on its own to update agent config without re-deploying the compose stack.

## Requirements

- Ansible >= 2.16
- `community.docker` collection on the controller
- Target host with Docker installed and the Hermes container running (unless `hermes_gateway_create_profiles: false` and `hermes_gateway_skip_docker: true`)
- An `ansible` user and a `docker` group on the target host

## Role Variables

| Variable | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `hermes_container_name` | str | no | `hermes` | Name of the running Hermes container. Must match the `hermes` role value on the same host. |
| `hermes_data_dir` | str | no | `/opt/hermes/data` | Hermes data directory on the host. Must match the `hermes` role value. |
| `hermes_default_model` | dict | no | `{provider: anthropic, model: claude-sonnet-4-6}` | Global model config written to `config.yaml`. Accepts `provider`, `model`, and optionally `base_url` and `api_key`. |
| `hermes_profiles` | list | **yes** | — | List of agent profile dicts. Each entry needs at minimum `name` (str). Optional keys: `soul` (str — written as `SOUL.md`), `gateways` (list of gateway dicts). Discord gateway dicts require `type: discord`, `bot_token` (**Supply from vault.**), `allowed_users` (list of snowflake IDs), and `admin_users` (list). |
| `hermes_gateway_create_profiles` | bool | no | `true` | When true, runs `hermes profile create <name>` via docker exec for each profile. Set `false` before the container is running (e.g. first converge or Molecule). |
| `hermes_gateway_skip_docker` | bool | no | `false` | Skip the `docker_container` restart handler. Set `true` in Molecule/CI environments without Docker access. |
| `hermes_config_extra` | dict | no | `{}` | Dict merged verbatim into the top level of `config.yaml`. Use this for schema fields not explicitly modelled by the template. |

## Dependencies

None declared in `meta/main.yml`. Practically this role is a companion to `danmwallace.hermes.hermes` — that role must have deployed and started the container before `hermes_gateway_create_profiles: true` will succeed.

## Example Playbook

```yaml
- hosts: ai_servers
  become: true
  roles:
    - role: danmwallace.hermes.hermes_gateway
      vars:
        hermes_profiles:
          - name: assistant
            soul: |
              You are a helpful assistant. Be concise and accurate.
            gateways:
              - type: discord
                bot_token: "{{ vault_hermes_discord_bot_token }}"
                allowed_users:
                  - "123456789012345678"
                admin_users:
                  - "123456789012345678"
```

## What the Role Does

1. Asserts that `hermes_data_dir` and `hermes_profiles` are non-empty.
2. Ensures `{{ hermes_data_dir }}/profiles/<name>/` exists for each profile (`ansible:docker`, 0755).
3. Runs `hermes profile create <name>` inside the container via `community.docker.docker_container_exec` for each profile (skipped when `hermes_gateway_create_profiles: false`; idempotent — tolerates "already exists" exit).
4. Renders `{{ hermes_data_dir }}/config.yaml` from `config.yaml.j2` (`ansible:docker`, 0600, `no_log`).
5. Renders `{{ hermes_data_dir }}/profiles/<name>/SOUL.md` for each profile where `soul` is defined (`ansible:docker`, 0644).

A `Restart hermes container` handler fires when `config.yaml` or any `SOUL.md` changes, issuing a `docker restart` on `hermes_container_name` so the agent picks up the new config without a full compose redeploy. The handler is skipped when `hermes_gateway_skip_docker: true`.

## Notes

- **Discord gateway**: the template extracts the first Discord gateway it finds across all profiles and writes it as the single top-level `gateway:` block in `config.yaml`. Hermes Agent supports only one active gateway at a time; multi-gateway support is not currently modelled.
- **`hermes_container_name` and `hermes_data_dir`** share the `hermes_` prefix (not `hermes_gateway_`) intentionally — they are the shared contract between this role and the `hermes` role. Keep them in sync.
- **Profile `soul`** values are written verbatim into `SOUL.md`. Multi-line YAML block scalars work well here.
- Run this role with `hermes_gateway_create_profiles: false` on a fresh host where the container hasn't started yet, then re-run with `true` (or let the `hermes` role start the container first).

## License

MIT
