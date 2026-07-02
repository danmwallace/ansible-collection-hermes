# danmwallace.hermes.claude_code

Installs the [Anthropic Claude Code CLI](https://github.com/anthropics/claude-code) (`@anthropic-ai/claude-code`) via npm on a Fedora Server host. Creates the user's `~/.claude/` config directory and writes `settings.json` from a template. Optionally writes a global `CLAUDE.md`.

This role does **not** authenticate. After deployment, the target user must run `claude` and complete browser OAuth, or set `ANTHROPIC_API_KEY` in their environment.

## Requirements

- Ansible >= 2.15
- `community.general` collection (for `npm` module)
- Fedora 40+ target host with dnf available

## Role Variables

| Variable | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `claude_code_user` | str | no | `hermes` | OS user under whose home directory `~/.claude/` is created. |
| `claude_code_version` | str | no | `latest` | npm package version. `latest` always installs newest; pin with e.g. `1.0.3`. |
| `claude_code_npm_scope` | str | no | `global` | npm install scope. `global` installs to `/usr/lib/node_modules` (requires root). |
| `claude_code_config_dir` | str | no | `/home/{{ claude_code_user }}/.claude` | Path to the user's Claude config directory. |
| `claude_code_global_claude_md` | str | no | `""` | Contents of `~/.claude/CLAUDE.md`. Written only when non-empty. |
| `claude_code_settings` | dict | no | `{}` | Settings merged on top of role defaults and written to `settings.json`. |

## Dependencies

None.

## Example Playbook

```yaml
- hosts: ai_hosts
  become: true
  roles:
    - role: danmwallace.hermes.claude_code
      vars:
        claude_code_user: hermes
        claude_code_version: latest
        claude_code_settings:
          permissions:
            allow:
              - Bash(*)
```

## What the Role Does

1. Installs `nodejs` and `npm` via dnf.
2. Installs `@anthropic-ai/claude-code` globally via npm (pinned or latest, per `claude_code_version`).
3. Creates `~/.claude/` and `~/.claude/commands/` directories owned by `claude_code_user`.
4. Writes `~/.claude/settings.json` from a Jinja2 template, merging `claude_code_settings`.
5. Writes `~/.claude/CLAUDE.md` from `claude_code_global_claude_md` when the variable is non-empty.

## Notes

Authentication is a manual step. After running the role, SSH as the target user and run `claude` to complete browser OAuth, or export `ANTHROPIC_API_KEY` in the user's shell profile.

## License

MIT
