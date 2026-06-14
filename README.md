# Ansible Collection — danmwallace.hermes

Deploys and configures [Hermes Agent](https://hermes-agent.nousresearch.com/) on Docker hosts. The collection provides two complementary roles: one that runs the agent as a Docker Compose stack behind Traefik, and one that configures its agent profiles, gateway connections (Discord), and per-profile identity files. The two roles are designed to run together on the same host but can be applied independently — the gateway role is re-runnable on its own to update agent config without redeploying the container.

## Requirements

- Ansible >= 2.16
- Collection dependencies (resolved automatically by `ansible-galaxy`):
  - `community.docker >= 3.0.0`

## Installation

```bash
ansible-galaxy collection install danmwallace.hermes
```

Or pin it in `requirements.yml`:

```yaml
collections:
  - name: danmwallace.hermes
    version: ">=1.0.0"
```

## Roles

| Role | Description |
| --- | --- |
| [`danmwallace.hermes.hermes`](roles/hermes/README.md) | Deploy Hermes Agent Docker Compose stack behind Traefik. |
| [`danmwallace.hermes.hermes_gateway`](roles/hermes_gateway/README.md) | Configure Hermes Agent profiles, gateways, and identity files. |

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

    - role: danmwallace.hermes.hermes_gateway
      vars:
        hermes_profiles:
          - name: assistant
            soul: |
              You are a helpful assistant.
            gateways:
              - type: discord
                bot_token: "{{ vault_hermes_discord_bot_token }}"
                allowed_users:
                  - "123456789012345678"
                admin_users:
                  - "123456789012345678"
```

## License

MIT
