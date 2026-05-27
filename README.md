# ansible.hermes_setup

Install and operate [Hermes Agent](https://github.com/NousResearch/hermes-agent) on Rocky Linux 10 as a dedicated unprivileged user.

This role is intentionally conservative for sysadmin use:

- creates a dedicated `hermes` Linux user without sudo rights
- installs the packages needed for Hermes CLI and dashboard on Rocky Linux 10
- installs Hermes via the official upstream installer as user `hermes` (`--skip-setup --skip-browser` for non-interactive Ansible runs)
- optionally writes non-secret OpenAI Codex defaults into Hermes config
- prints the manual Codex OAuth command instead of trying to automate secrets/device-code auth
- installs and manages a `hermes-dashboard.service` systemd user service
- optionally installs Playwright runtime packages, the local Playwright npm package, and Chromium browser binaries

## Requirements

- Rocky Linux 10 target host
- Ansible 2.9 or newer
- root or passwordless sudo access for package installation, user creation, linger, and service setup
- outbound HTTPS access from the target host for the Hermes installer and optional Playwright browser download

## Installation

Install from GitHub into the Galaxy-style role path:

```bash
ansible-galaxy clone https://github.com/joe-speedboat/ansible.hermes_setup.git /etc/ansible/roles/joe-speedboat.hermes_setup
```

Or use it from a project-local `roles/joe-speedboat.hermes_setup` directory.

## Role Variables

Important defaults from `defaults/main.yml`:

- `hermes_user`: Linux user to create. Default: `hermes`
- `hermes_home`: home directory. Default: `/home/hermes`
- `hermes_dashboard_enabled`: install dashboard user service. Default: `true`
- `hermes_dashboard_host`: dashboard bind address. Default: `0.0.0.0`
- `hermes_dashboard_port`: dashboard port. Default: `8080`
- `hermes_dashboard_insecure`: pass `--insecure` to the dashboard. Default: `true`
- `configure_codex`: configure non-secret Codex defaults. Default: `true`
- `hermes_codex_provider`: default provider. Default: `openai-codex`
- `hermes_codex_model`: default model. Default: `gpt-5.5`
- `hermes_playwright_enabled`: install Playwright support. Default: `false`
- `hermes_playwright_browsers`: browser list for `npx playwright install`. Default: `['chromium']`

## Example Playbook

```yaml
---
- name: Install Hermes Agent on Rocky Linux 10
  hosts: hermes_servers
  become: true
  roles:
    - role: joe-speedboat.hermes_setup
      vars:
        configure_codex: true
        hermes_playwright_enabled: true
        hermes_dashboard_host: 0.0.0.0
        hermes_dashboard_port: 8080
...
```

## After the Role Run

Codex authentication is intentionally manual because it uses OAuth/device-code auth and must not be stored in the role:

```bash
sudo -iu hermes hermes auth add openai-codex
```

Alternative interactive setup:

```bash
sudo -iu hermes hermes model
```

Check Hermes and the dashboard:

```bash
sudo -iu hermes hermes --version
sudo -iu hermes hermes doctor
sudo -iu hermes systemctl --user status hermes-dashboard.service --no-pager
curl -I http://127.0.0.1:8080
```

If Playwright is enabled:

```bash
sudo -iu hermes bash -lc 'cd ~/.hermes/hermes-agent && npx playwright --version'
```

## Security Notes

- The `hermes` user is deliberately not added to `wheel` or any sudo group.
- The dashboard default binds to `0.0.0.0:8080` with `--insecure` because that matches the lab/server reference setup. For production, prefer `127.0.0.1` plus SSH tunnel or a reverse proxy with TLS/auth.
- Secrets belong in `/home/hermes/.hermes/.env`, `/home/hermes/.hermes/auth.json`, or Hermes' auth store. Do not put tokens into Ansible vars or Git.

## Manual Setup Documentation

For a copy/paste manual runbook that mirrors this role, see [`docs/manual-setup-rocky10.md`](docs/manual-setup-rocky10.md).

## License

GPLv3

Copyright (c) Chris Ruettimann <chris@bitbull.ch>
