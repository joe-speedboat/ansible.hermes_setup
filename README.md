# ansible.hermes_setup

Install and operate [Hermes Agent](https://github.com/NousResearch/hermes-agent) on Rocky Linux 10 as a dedicated unprivileged user.

This role is intentionally conservative for sysadmin use:

- creates a dedicated `hermes` Linux user without sudo rights
- installs the packages needed for Hermes CLI on Rocky Linux 10
- installs Hermes via the official upstream installer as user `hermes` (`--skip-setup --skip-browser` for non-interactive Ansible runs)
- optionally writes non-secret OpenAI Codex defaults into Hermes config
- prints the manual Codex OAuth command instead of trying to automate secrets/device-code auth
- optionally installs and manages a `hermes-dashboard.service` systemd user service
- optionally installs Playwright runtime packages, the local Playwright npm package, and Chromium browser binaries

## Requirements

- Rocky Linux 10 target host
- Ansible 2.9 or newer
- root or passwordless sudo access for package installation, user creation, linger, and service setup
- outbound HTTPS access from the target host for the Hermes installer and optional Playwright browser download

## Installation

Install from GitHub into the Galaxy-style role path:

```bash
git clone https://github.com/joe-speedboat/ansible.hermes_setup.git /etc/ansible/roles/joe-speedboat.hermes_setup
```

`ansible-galaxy` has no `clone` subcommand. For a direct GitHub checkout, use `git clone` as shown above, or use it from a project-local `roles/joe-speedboat.hermes_setup` directory.

## Role Variables

Important defaults from `defaults/main.yml`:

- `hermes_user`: Linux user to create. Default: `hermes`
- `hermes_home`: home directory. Default: `/home/hermes`
- `hermes_dashboard_enabled`: install dashboard user service. Default: `false`
- `hermes_dashboard_service_enabled`: enable dashboard service at boot when dashboard is installed. Default: `true`
- `hermes_dashboard_service_state`: dashboard runtime state when dashboard is installed. Default: `started`
- `hermes_dashboard_host`: dashboard bind address. Default: `0.0.0.0`
- `hermes_dashboard_port`: dashboard port. Default: `8080`
- `hermes_dashboard_insecure`: pass `--insecure` to the dashboard. Default: `true`
- `configure_codex`: configure non-secret Codex defaults. Default: `true`
- `hermes_codex_provider`: default provider. Default: `openai-codex`
- `hermes_codex_model`: default model. Default: `gpt-5.5`
- `hermes_playwright_enabled`: install Playwright support. Default: `false`
- `hermes_playwright_browsers`: browser list for `npx playwright install`. Default: `['chromium']`
- `hermes_playwright_ldd_check_enabled`: run `ldd` against Playwright's Chromium headless shell and fail if direct shared libraries are missing. Default: `true`
- `hermes_playwright_smoke_test_enabled`: run a real Chromium headless smoke test after Playwright install. Default: `true`

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
        hermes_dashboard_enabled: true
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

Check Hermes:

```bash
sudo -iu hermes hermes --version
sudo -iu hermes hermes doctor
```

If `hermes_dashboard_enabled: true`, check the dashboard:

```bash
sudo -iu hermes systemctl --user status hermes-dashboard.service --no-pager
curl -fsS http://127.0.0.1:8080 >/dev/null
```

If Playwright is enabled, the role installs the Rocky/RHEL runtime libraries via `dnf`, installs Chromium with `npx playwright install chromium`, checks direct shared-library dependencies with `ldd`, and then runs a real Chromium headless smoke test. Manual checks:

```bash
sudo -iu hermes bash -lc 'ldd ~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell | grep "not found"'
sudo -iu hermes bash -lc 'cd ~/.hermes/hermes-agent && node -e '\''(async()=>{const {chromium}=require("playwright"); const browser=await chromium.launch({headless:true}); const page=await browser.newPage(); await page.goto("data:text/html,<h1>playwright-ok</h1>"); console.log(await page.textContent("h1")); await browser.close();})().catch(error=>{console.error(error.stack||error); process.exit(1);})'\'''
```

The direct `dnf` package list is intentional. Playwright's own `npx playwright install-deps chromium` is primarily Debian/Ubuntu-oriented and may print `BEWARE: your OS is not officially supported by Playwright; installing dependencies for ubuntu24.04-x64 as a fallback` on Rocky Linux.

## Messaging Gateway / Telegram Pairing

To configure Telegram or another messenger, run the interactive gateway wizard as the `hermes` user:

```bash
sudo -iu hermes hermes gateway setup
```

For Telegram, choose Telegram in the wizard and provide the bot token from BotFather. Then install/start the gateway service:

```bash
sudo -iu hermes hermes gateway install
sudo -iu hermes hermes gateway start
sudo -iu hermes hermes gateway status
```

When a user messages the bot, approve the pairing code:

```bash
sudo -iu hermes hermes pairing list
sudo -iu hermes hermes pairing approve telegram <CODE>
```

## Security Notes

- The `hermes` user is deliberately not added to `wheel` or any sudo group.
- The dashboard is disabled by default. Enable it with `hermes_dashboard_enabled: true`. If enabled, the default binds to `0.0.0.0:8080` with `--insecure` because that matches the lab/server reference setup. For production, prefer `127.0.0.1` plus SSH tunnel or a reverse proxy with TLS/auth.
- Secrets belong in `/home/hermes/.hermes/.env`, `/home/hermes/.hermes/auth.json`, or Hermes' auth store. Do not put tokens into Ansible vars or Git.

## Manual Setup Documentation

For a copy/paste manual runbook that mirrors this role, see [`docs/manual-setup-rocky10.md`](docs/manual-setup-rocky10.md).

## License

GPLv3

Copyright (c) Chris Ruettimann <chris@bitbull.ch>
