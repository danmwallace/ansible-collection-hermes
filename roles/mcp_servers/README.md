# danmwallace.hermes.mcp_servers

Per-machine MCP servers for Claude Code, and on atomic-hyprland for every
agent on the desktop. Secrets never land in a plain file: each is stored as a
`systemd-creds --user` credential, tied to that machine and user, and
decrypted only when the server starts.

## Two ways in, chosen per host

| `mcp_servers_platform` | when (`auto`) | where the server goes | secrets |
|---|---|---|---|
| `registry` | `/run/ostree-booted` and `/usr/bin/hypr-mcp` exist (atomic-hyprland) | `~/.config/atomic-hyprland/mcp.d/<name>.json`; `hypr-mcp` syncs it into Claude Code and Gemini CLI, and Super+A / Fix it read it | `~/.config/atomic-hyprland/credentials/<name>-<env>.cred`, referenced as `{"credential": "<name>-<env>"}` and decrypted by `hypr-mcp run` |
| `claude_cli` | anything else (e.g. Fedora KDE) | `claude mcp add-json -s user`, pointing at a launcher in `~/.local/libexec/mcp-servers/<name>` | `~/.local/share/mcp-servers/credentials/<name>-<env>.cred`, decrypted by the launcher |

The same variables work on both, so a machine moving to atomic-hyprland only
needs the play run again.

## Variables

| Variable | Default | Meaning |
|---|---|---|
| `mcp_servers_user` | `ansible_user_id` | whose servers and credentials these are |
| `mcp_servers_list` | `[]` | the servers (below) |
| `mcp_servers_platform` | `auto` | `registry`, `claude_cli` or `auto` |
| `mcp_servers_claude_bin` | `""` | `claude_cli` mode: the CLI; empty finds `~/.local/bin/claude`, `/usr/bin/claude` or `/usr/local/bin/claude` |

Each server:

| Key | Meaning |
|---|---|
| `name` | server name (file stem, Claude Code name) |
| `command`, `args` | how to start it |
| `env` | plain environment |
| `secrets` | `ENV_NAME: value`; pass values from ansible-vault |
| `files` | `[{src, dest, mode}]` non-secret files it reads (`dest` may start with `~`; default mode 0600) |
| `npm_package` | optional `{name, version}`, installed globally (system npm, or Homebrew's node as the user) |
| `read_only_tools` | optional; registry `readOnlyTools` (no approval card on atomic-hyprland) |

## Example

```yaml
- role: danmwallace.hermes.mcp_servers
  vars:
    mcp_servers_user: dwallace
    mcp_servers_list:
      - name: mikromcp
        command: /usr/local/bin/mikromcp
        args: [serve]
        env: { MIKROMCP_CONFIG_PATH: /home/dwallace/.mikromcp/routers.yaml }
        secrets:
          ROUTER_HOME01_USER: "{{ vault_mikromcp_router_home01_user }}"
          ROUTER_HOME01_PASS: "{{ vault_mikromcp_router_home01_pass }}"
        files:
          - { src: files/mikromcp/routers.yaml, dest: ~/.mikromcp/routers.yaml }
        npm_package: { name: mikromcp, version: "1.6.0" }
```

## Gotchas

- A credential file `<n>.cred` is encrypted with `--name=<n>.cred`, because
  atomic-hyprland's `hypr-mcp run` decrypts without `--name` and systemd then
  expects the file's own name.
- `systemd-creds` output differs on every run, so a credential is rewritten
  only when decrypting the stored one gives a different value. A second run
  reports no change.
- `claude mcp add-json` runs only when `~/.claude.json` doesn't already start
  the launcher; an outdated entry of the same name is removed first.
- The npm install path isn't covered by the molecule test (no registry access
  in the container); it is checked by hand on the first host that needs it.

## Tests

```bash
cd roles/mcp_servers && molecule test   # podman; both platform modes, idempotence, decryption
```
