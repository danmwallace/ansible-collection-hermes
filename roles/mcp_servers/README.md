# danmwallace.hermes.mcp_servers

Per-machine [MCP](https://modelcontextprotocol.io) servers for Claude Code, and on
atomic-hyprland for every agent on the desktop. Each entry in `mcp_servers_list` is either
a stdio server (`command`) or an HTTP/SSE server (`url`). The role can install the server
first, from npm, a sha256-pinned GitHub release, or `uv tool install` from a pinned git
tag. Secrets never land in a plain file: each is stored as a `systemd-creds --user`
credential, tied to that machine and user, and only a reference to it is written.

Where a server goes depends on the host:

| `mcp_servers_platform` | when (`auto`) | where the server goes | secrets |
| --- | --- | --- | --- |
| `registry` | `/run/ostree-booted` and `/usr/bin/hypr-mcp` exist (atomic-hyprland) | `~/.config/atomic-hyprland/mcp.d/<name>.json`; `hypr-mcp` syncs it into Claude Code and Gemini CLI, and Super+A / Fix it read it | `~/.config/atomic-hyprland/credentials/<name>-<env>.cred` (env) and `<name>-hdr-<header>.cred` (headers), referenced as `{"credential": "..."}`; `hypr-mcp run` decrypts env ones when the server starts, `hypr-mcp headers` (Claude Code's `headersHelper`) header ones when a url server connects |
| `claude_cli` | anything else (e.g. Fedora KDE) | `claude mcp add-json -s user`, pointing at a launcher in `~/.local/libexec/mcp-servers/<name>` | `~/.local/share/mcp-servers/credentials/<name>-<env>.cred`, decrypted by the launcher |

The same variables work on both, so a machine moving to atomic-hyprland only needs the
play run again. `url` servers, `deny_tools` and `ask_every_time` need the registry.

## Requirements

- Ansible >= 2.16
- `community.general` on the controller (`dict_kv`, `npm`, `homebrew`)
- Target: systemd with `systemd-creds --user` (256 or later)
- `npm_package`: the system npm, or Homebrew (its node is installed as the user)
- `github_release`: network access to `mcp_servers_github_url`, and `tar`/`gzip` (or
  `unzip`) for archive assets
- `uv_tool`: `uv` and `git` on the target, and access to the source repo as the user (for
  a private repo over SSH, the user's key)
- `url` servers: atomic-hyprland with `hypr-mcp headers` (the image release that added
  secret headers); older images write the headers but no client can resolve them

## Role Variables

| Variable | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `mcp_servers_user` | str | no | `{{ ansible_facts['user_id'] }}` | The account whose MCP servers, credentials and Claude Code config these are. |
| `mcp_servers_list` | list of dict | no | `[]` | One entry per server (keys below). |
| `mcp_servers_platform` | str | no | `auto` | `auto`, `registry` or `claude_cli` (see the table above). |
| `mcp_servers_claude_bin` | str | no | `""` | `claude_cli` mode: the claude binary. Empty finds `~/.local/bin/claude`, `/usr/bin/claude` or `/usr/local/bin/claude`. |
| `mcp_servers_github_url` | str | no | `https://github.com` | Base URL `github_release` downloads from (a test can point it at a local server). |
| `mcp_servers_download_dir` | str | no | `/var/cache/mcp-servers` | Where `github_release` keeps assets, by server, version and sha256. |
| `mcp_servers_uv_bin` | str | no | `""` | `uv` for `uv_tool`. Empty finds `~/.local/bin/uv`, `/usr/bin/uv` or `/home/linuxbrew/.linuxbrew/bin/uv`. |

Each `mcp_servers_list` entry:

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | str | yes | Server name (registry file stem, Claude Code name): letters, digits, `.`, `_`, `-`. |
| `command` | str | one of `command`/`url` | Absolute path of a stdio server. |
| `args` | list of str | no | Arguments for `command`. |
| `url` | str | one of `command`/`url` | URL of an HTTP or SSE server. Registry mode only. |
| `type` | str | no | `http` (when left out) or `sse`; `url` servers only. |
| `env` | dict | no | Plain environment for a stdio server. |
| `secrets` | dict | no | `ENV_NAME: value` for a stdio server; stored as credential `<name>-<env_name>`. **Supply from vault.** |
| `headers` | dict | no | Plain headers for a `url` server, written as they are. A name that usually carries a credential (`Authorization`, `Proxy-Authorization`, `Cookie`, or one containing `token`, `secret`, `key`, `auth` or `pass`, in any case) is refused: put it in `header_secrets`. |
| `header_secrets` | dict | no | `Header-Name: value` for a `url` server (the whole value, e.g. `Bearer …`); stored as credential `<name>-hdr-<header>`. **Supply from vault.** |
| `files` | list of dict | no | `[{src, dest, mode}]` non-secret files the server reads; `dest` may start with `~`, `mode` defaults to `0600`. |
| `npm_package` | dict | no | `{name, version}`, installed globally (system npm, or Homebrew's node as the user). |
| `github_release` | dict | no | `{repo, version, asset, sha256, member}`: installs `command` (which must be in `/usr/local/bin`) from that release asset, checked against `sha256` (64 hex characters). `member` is the binary's path inside a `.tar.gz`/`.tgz`/`.zip`; leave it out for a bare binary. |
| `uv_tool` | dict | no | `{source, version}`: `uv tool install --force git+<source>@<version>` as the user; `command` is then the console script, e.g. `/home/<user>/.local/bin/<script>`. |
| `read_only_tools` | list of str | no | Registry `readOnlyTools`: no approval card on atomic-hyprland, usable in ask mode. |
| `deny_tools` | list of str | no | Registry `denyTools`: no agent or client may call them. Registry mode only. |
| `ask_every_time` | list of str | no | Registry `askEveryTime`: tools that need approval on every call and are never offered "always allow" (a card in the desktop agent, an ask rule in Claude Code, excluded from Gemini CLI). Written to the root-owned machine layer, `/etc/atomic-hyprland/mcp.d/<name>.json`, as a list-only file, so the user account can't drop it from its own entry. Registry mode only; a tool can't also be in `read_only_tools`. |
| `tool_notes` | dict | no | Registry `toolNotes`: tool → how to undo it, shown on its approval card. |

## Dependencies

None declared in `meta/main.yml`. On atomic-hyprland the registry, `hypr-mcp` and its sync
unit come from the image; elsewhere the claude CLI must already be installed (for example
by `danmwallace.hermes.claude_code`).

## Example Playbook

```yaml
- hosts: claude_machines
  become: true
  roles:
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
          - name: truenas
            command: /usr/local/bin/truenas-mcp
            args: [--read-only]
            env: { TRUENAS_URL: nas.example.com, TRUENAS_API_USER: mcp-readonly }
            secrets: { TRUENAS_API_KEY: "{{ vault_truenas_mcp_readonly_api_key }}" }
            github_release:
              repo: truenas/truenas-mcp
              version: v1.0.0
              asset: truenas-mcp-linux-amd64.tar.gz
              member: truenas-mcp-linux-amd64
              sha256: "<sha256 of the asset, checked against the release's checksums.txt>"
            read_only_tools: [system_info, list_pools]
          - name: n8n
            url: https://n8n.example.com/mcp-server/http
            header_secrets: { Authorization: "Bearer {{ vault_n8n_mcp_token }}" }
            deny_tools: [update_workflow]
```

## What the Role Does

1. Checks every entry on a copy that holds only names, never secret values: a valid name
   and env keys, exactly one of `command` or `url`, `headers`/`header_secrets`/`type` only
   on `url` servers, plain header names, no credential-style name (such as `Authorization`)
   in plain `headers`, no tool both read-only and denied, a
   `github_release` command in `/usr/local/bin` with a 64-hex-character sha256. (The
   argument spec also checks types and refuses unknown keys.)
2. Looks up the user's home and settles the platform (`auto`: atomic-hyprland if
   `/run/ostree-booted` and `/usr/bin/hypr-mcp` exist).
3. On a `claude_cli` host, refuses `url` servers, `deny_tools` and `ask_every_time` before writing anything. A tool in both `read_only_tools` and `deny_tools` or `ask_every_time` is refused too.
4. Ensures the private credential folder exists.
5. For each server, in this order:
   1. installs the npm package, the GitHub release binary (download checked against
      `sha256`, unpacked, installed as root with mode 0755) or the uv tool (as the user,
      only when the stamp in `~/.local/share/mcp-servers` shows a different source or tag,
      or the console script is missing);
   2. copies its `files`;
   3. stores each `secrets` and `header_secrets` value as a `systemd-creds --user`
      credential, as the user, rewriting it only when the value changed;
   4. writes the registry entry (registry mode), plus, when `ask_every_time` is set, a root-owned
      list-only file in `/etc/atomic-hyprland/mcp.d` (removed when it isn't), or the launcher and Claude Code entry
      (`claude_cli` mode). In registry mode it also retires a `claude_cli` setup left from
      before a move to atomic-hyprland.

The role has no handlers: `hypr-mcp-sync.path` on atomic-hyprland picks up registry changes.

6. In registry mode, when an entry or ask list changed, starts `hypr-mcp-sync.service` as the user (`systemctl --user start --no-block`), so a new server is registered and its ask rules written now, not at the next login. Without a running user manager this does nothing, and the sync runs at login.

## Notes

- **Credential names.** An env secret is `<name>-<env_name lowercased>`, a header secret
  `<name>-hdr-<header lowercased>`. A file `<n>.cred` is encrypted with `--name=<n>.cred`,
  because `hypr-mcp` decrypts without `--name` and systemd then expects the file's own name.
- **Credentials are handled as the user, never root.** The files live in the user's home,
  where a root write or chown could be redirected by a symlink; something other than a
  plain file at a credential's path stops the role.
- **No secret reaches the output, even at `-v`.** Entries are validated on a copy without
  the values, the loops are `no_log`, `secrets`/`header_secrets` are `no_log` in the
  argument spec, and `~/.claude.json` is read as the user and not shown.
- **Idempotent.** `systemd-creds` output differs on every run, so a credential is rewritten
  only when decrypting the stored one gives a different value. `claude mcp add-json` runs
  only when `~/.claude.json` doesn't already start the launcher. A release version or pin
  already downloaded does nothing; a new version or a new `sha256` downloads and unpacks
  into its own folder, so a binary unpacked from an older asset is never reused. `uv_tool`
  reinstalls only when its source or tag changes or the script is missing.
- **Dry runs** work on a fresh host: release steps with nothing downloaded yet are skipped,
  and the uv install (a `command`) is skipped as `command` tasks are in check mode.
- **`uv_tool` is pinned less tightly than `github_release`.** `version` is any git ref; a
  full commit SHA is a stronger pin than a tag, which can be moved. There is no hash check
  of what is fetched, and `uv tool install` resolves the package's dependencies at install
  time (it does not use the package's lockfile), so pin them in the package itself.
- **The npm path isn't covered by molecule.** It's checked by hand on the first host that
  needs it.

### Tests

```bash
cd roles/mcp_servers && molecule test              # podman; needs network (uv_tool fetches setuptools)
bash roles/mcp_servers/tests/check-verbose-log.sh  # the same at -v, failing if a secret is printed
```

The scenario covers both platforms, idempotence, credential decryption, the move to the
registry, a `url` server with a header secret, a release served locally (including a wrong
`sha256` and a re-pin under the same tag), a `uv_tool` from a local git tag, and twelve
entries the role must refuse.

## License

MIT
