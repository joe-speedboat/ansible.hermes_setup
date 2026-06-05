# ansible.hermes_setup

Install and operate [Hermes Agent](https://github.com/NousResearch/hermes-agent) on Rocky Linux 10 as a dedicated unprivileged user.

This role is intentionally conservative for sysadmin use:

- creates a dedicated `hermes` Linux user without sudo rights
- installs the packages needed for Hermes CLI on Rocky Linux 10
- installs Hermes via the official upstream installer as user `hermes` (`--skip-setup --skip-browser` for non-interactive Ansible runs)
- optionally writes non-secret OpenAI Codex defaults into Hermes config
- prints the manual Codex OAuth command instead of trying to automate secrets/device-code auth
- installs, enables, and starts a `hermes-gateway.service` systemd user service by default
- installs, enables, and starts a loopback-only `hermes-dashboard.service` systemd user service by default
- optionally installs, enables, and starts a loopback-only `hermes-webui.service` systemd user service
- optionally exposes the dashboard through nginx HTTPS + Basic Auth
- optionally exposes Hermes WebUI through a separate nginx HTTPS + Basic Auth DNS vhost
- optionally installs a user-scope Ansible runtime for the dedicated `hermes` user
- installs Playwright runtime packages, the local Playwright npm package, and Chromium browser binaries by default

## Requirements

- Rocky Linux 10 target host
- Ansible 2.9 or newer
- root or passwordless sudo access for package installation, user creation, linger, and service setup
- outbound HTTPS access from the target host for the Hermes installer and the default Playwright browser download
- DNS records for every public Hermes dashboard/WebUI vhost when `hermes_nginx_enabled: true`

## Installation

Install the role with one of these methods.

1. Direct GitHub checkout into a Galaxy-style role path:

```bash
git clone https://github.com/joe-speedboat/ansible.hermes_setup.git /etc/ansible/roles/joe-speedboat.hermes_setup
```

For project-local checkouts, clone it into `roles/joe-speedboat.hermes_setup` below your Ansible project.

2. Ansible Galaxy:

```bash
ansible-galaxy role install joe-speedboat.hermes_setup
```

## Role Variables

Important defaults from `defaults/main.yml`:

- `hermes_user`: Linux user to create. Default: `hermes`
- `hermes_home`: home directory. Default: `/home/hermes`
- `hermes_gateway_enabled`: install gateway user service. Default: `true`
- `hermes_gateway_service_enabled`: enable gateway service at boot when gateway is installed. Default: `true`
- `hermes_gateway_service_state`: gateway runtime state when gateway is installed. Default: `started`
- `hermes_gateway_extra_args`: extra args appended to `hermes gateway run --replace`. Default: `""`
- `hermes_dashboard_enabled`: install dashboard user service. Default: `true`
- `hermes_dashboard_service_enabled`: enable dashboard service at boot when dashboard is installed. Default: `true`
- `hermes_dashboard_service_state`: dashboard runtime state when dashboard is installed. Default: `started`
- `hermes_dashboard_host`: dashboard bind address. Default: `127.0.0.1`
- `hermes_dashboard_port`: dashboard port. Default: `8080`
- `hermes_dashboard_insecure`: pass `--insecure` to the dashboard. Default: `false`
- `hermes_webui_enabled`: install Hermes WebUI from `https://github.com/nesquena/hermes-webui`. Default: `false`
- `hermes_webui_service_enabled`: enable WebUI service at boot when WebUI is installed. Default: `true`
- `hermes_webui_service_state`: WebUI runtime state when WebUI is installed. Default: `started`
- `hermes_webui_repo_url`: WebUI Git repository URL. Default: `https://github.com/nesquena/hermes-webui.git`
- `hermes_webui_repo_version`: WebUI Git version. Default: `master`
- `hermes_webui_app_dir`: WebUI checkout directory. Default: `{{ hermes_home }}/app/hermes-webui`
- `hermes_webui_host`: WebUI bind address. Default: `127.0.0.1`
- `hermes_webui_port`: WebUI port. Default: `8787`
- `hermes_webui_state_dir`: WebUI state directory. Default: `{{ hermes_config_dir }}/webui`
- `hermes_webui_default_workspace`: default WebUI workspace. Default: `{{ hermes_home }}/work`
- `hermes_webui_allowed_origins`: WebUI allowed browser origin. Default: `https://{{ hermes_webui_nginx_fqdn }}`
- `hermes_nginx_enabled`: install nginx HTTPS reverse proxies for enabled browser UIs. Default: `true`
- `hermes_dashboard_nginx_fqdn`: public dashboard DNS name for the nginx vhost. Default: target FQDN/inventory name
- `hermes_dashboard_nginx_conf`: nginx vhost config path. Default: `/etc/nginx/conf.d/{{ hermes_dashboard_nginx_fqdn }}.conf`
- `hermes_nginx_enable_firewall`: manage firewalld ports. Default: `true`
- `firewalld_open_ports`: list of ports to open in firewalld when nginx firewall management is enabled. Default: `['443/tcp']`
- `hermes_nginx_tls_dir`: directory for role-managed self-signed TLS material. Default: `/etc/pki/tls/hermes`
- `hermes_dashboard_nginx_tls_cert`: certificate path. Default: `{{ hermes_nginx_tls_dir }}/{{ hermes_dashboard_nginx_fqdn }}_tls.crt`
- `hermes_dashboard_nginx_tls_key`: private key path. Default: `{{ hermes_nginx_tls_dir }}/{{ hermes_dashboard_nginx_fqdn }}_tls.key`
- `hermes_nginx_generate_self_signed_cert`: generate a self-signed cert when no external cert is provided. Default: `true`
- `hermes_dashboard_nginx_basic_auth_enabled`: enable nginx Basic Auth. Default: `true`
- `hermes_dashboard_nginx_basic_auth_file`: htpasswd file path. Default: `/etc/nginx/.htpasswd-hermes-{{ hermes_dashboard_nginx_fqdn }}`
- `hermes_dashboard_nginx_basic_auth_realm`: Basic Auth realm shown by browsers. Default: `{{ hermes_dashboard_nginx_fqdn }}`
- `hermes_dashboard_nginx_basic_auth_user`: Basic Auth username. Default: `hermes`
- `hermes_dashboard_nginx_basic_auth_password`: Basic Auth password. Default: `changeme`
- `hermes_webui_nginx_fqdn`: public WebUI DNS name for the second nginx vhost. Default: `webui-{{ hermes_dashboard_nginx_fqdn }}`
- `hermes_webui_nginx_conf`: WebUI nginx vhost config path. Default: `/etc/nginx/conf.d/{{ hermes_webui_nginx_fqdn }}.conf`
- `hermes_webui_nginx_tls_cert`: WebUI certificate path. Default: `{{ hermes_nginx_tls_dir }}/{{ hermes_webui_nginx_fqdn }}_tls.crt`
- `hermes_webui_nginx_tls_key`: WebUI private key path. Default: `{{ hermes_nginx_tls_dir }}/{{ hermes_webui_nginx_fqdn }}_tls.key`
- `hermes_webui_nginx_basic_auth_enabled`: enable WebUI nginx Basic Auth. Default: `{{ hermes_dashboard_nginx_basic_auth_enabled }}`
- `hermes_webui_nginx_basic_auth_user`: WebUI Basic Auth username. Default: `{{ hermes_dashboard_nginx_basic_auth_user }}`
- `hermes_webui_nginx_basic_auth_password`: WebUI Basic Auth password. Default: `{{ hermes_dashboard_nginx_basic_auth_password }}`
- `ansible_enable`: install a user-scope Ansible runtime for the dedicated Hermes user via `https://ansible-uv.bitbull.ch`. Default: `false`
- `ansible_home`: Ansible userspace install directory. Default: `{{ hermes_home }}/ansible`
- `configure_codex`: configure non-secret Codex defaults. Default: `true`
- `hermes_codex_provider`: default provider. Default: `openai-codex`
- `hermes_codex_model`: default model. Default: `gpt-5.5`
- `hermes_playwright_enabled`: install Playwright support. Default: `true`
- `hermes_playwright_browsers`: browser list for `npx playwright install`. Default: `['chromium']`
- `hermes_playwright_ldd_check_enabled`: run `ldd` against Playwright's Chromium headless shell and fail if direct shared libraries are missing. Default: `true`
- `hermes_playwright_smoke_test_enabled`: run a real Chromium headless smoke test after Playwright install. Default: `true`
- `hermes_playwright_build_tools_enabled`: explicitly install build tools for npm native module rebuilds. Default: `false`

> Override `hermes_dashboard_nginx_basic_auth_password` with Ansible Vault for every deployment that exposes nginx beyond a disposable lab. The default `hermes` / `changeme` pair is only there so the role converges from defaults.

## Example Playbook: single Hermes dashboard behind nginx

```yaml
---
- name: Install Hermes Agent on Rocky Linux 10
  hosts: hermes_servers
  become: true
  roles:
    - role: joe-speedboat.hermes_setup
      vars:
        configure_codex: true
        hermes_gateway_enabled: true
        hermes_dashboard_enabled: true
        hermes_dashboard_host: 127.0.0.1
        hermes_dashboard_port: 8080
        hermes_dashboard_insecure: false

        hermes_nginx_enabled: true
        hermes_dashboard_nginx_fqdn: hermes.example.ch
        hermes_dashboard_nginx_basic_auth_user: chris
        hermes_dashboard_nginx_basic_auth_password: "{{ vault_hermes_dashboard_password }}"
...
```

## Example Playbook: dashboard and Hermes WebUI on separate vhosts

Use two DNS names for one Hermes instance when both browser interfaces are enabled. The built-in dashboard and Hermes WebUI each keep their own root-relative routes and WebSocket/API endpoints.

```yaml
---
- name: Install Hermes dashboard and WebUI on Rocky Linux 10
  hosts: hermes_servers
  become: true
  roles:
    - role: joe-speedboat.hermes_setup
      vars:
        hermes_gateway_enabled: true
        hermes_dashboard_enabled: true
        hermes_dashboard_host: 127.0.0.1
        hermes_dashboard_port: 8080

        hermes_webui_enabled: true
        hermes_webui_host: 127.0.0.1
        hermes_webui_port: 8787

        hermes_nginx_enabled: true
        # Built-in Hermes dashboard:
        hermes_dashboard_nginx_fqdn: hermes1-adm.example.ch
        # Hermes WebUI:
        hermes_webui_nginx_fqdn: hermes1.example.ch

        hermes_dashboard_nginx_basic_auth_user: chris
        hermes_dashboard_nginx_basic_auth_password: "{{ vault_hermes_password }}"
...
```

## Example Playbook: multiple Hermes users via DNS vhosts

Use one Linux user, one loopback dashboard port, and one nginx vhost per Hermes instance. This avoids subfolder rewrites for `/api/...` and WebSocket endpoints. The nginx TLS certificate/key and htpasswd defaults include `hermes_dashboard_nginx_fqdn`, so multiple role invocations on one VM do not overwrite each other.

```yaml
---
- name: Install multiple Hermes dashboard instances
  hosts: hermes_servers
  become: true
  vars:
    hermes_instances:
      - user: hermes-chris
        fqdn: chris-hermes.example.ch
        dashboard_port: 8081
        auth_user: chris
        auth_password: "{{ vault_hermes_chris_password }}"
      - user: hermes-dev
        fqdn: dev-hermes.example.ch
        dashboard_port: 8082
        auth_user: dev
        auth_password: "{{ vault_hermes_dev_password }}"
  tasks:
    - name: Install Hermes instance
      ansible.builtin.include_role:
        name: joe-speedboat.hermes_setup
      loop: "{{ hermes_instances }}"
      loop_control:
        loop_var: hermes_instance
      vars:
        hermes_user: "{{ hermes_instance.user }}"
        hermes_group: "{{ hermes_instance.user }}"
        hermes_home: "/home/{{ hermes_instance.user }}"

        hermes_dashboard_host: 127.0.0.1
        hermes_dashboard_port: "{{ hermes_instance.dashboard_port }}"
        hermes_dashboard_insecure: false

        hermes_nginx_enabled: true
        hermes_dashboard_nginx_fqdn: "{{ hermes_instance.fqdn }}"
        # FQDN-scoped defaults keep TLS/key material and htpasswd files separate per vhost.
        hermes_nginx_tls_dir: /etc/pki/tls/hermes
        hermes_dashboard_nginx_basic_auth_user: "{{ hermes_instance.auth_user }}"
        hermes_dashboard_nginx_basic_auth_password: "{{ hermes_instance.auth_password }}"
...
```

## Why vhosts instead of subfolders?

Hermes dashboard and Hermes WebUI use root-relative frontend assets, REST API routes under `/api/...`, and WebSocket endpoints. DNS vhosts keep those paths unchanged per interface and per instance. Subfolder deployments would require fragile path rewriting and are not recommended.

For the built-in dashboard, the nginx template forwards `Host: 127.0.0.1:<port>` and clears `Origin` so Hermes' dashboard Host/Origin protections continue to work behind the reverse proxy. For Hermes WebUI, the template preserves the browser-visible `Host` and `X-Forwarded-*` headers and configures `HERMES_WEBUI_ALLOWED_ORIGINS` for the WebUI service. Basic Auth credentials are not forwarded to either backend.

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

If `ansible_enable: true`, the role installs Ansible below `{{ hermes_home }}/ansible`, wires the runtime profile into the Hermes user's `.bashrc`, and verifies it during the run. Manual check:

```bash
sudo -iu hermes ansible --version
```

If `hermes_gateway_enabled: true`, check the gateway user service:

```bash
sudo -iu hermes systemctl --user status hermes-gateway.service --no-pager
sudo -iu hermes systemctl --user is-enabled hermes-gateway.service
```

If `hermes_dashboard_enabled: true`, check the loopback dashboard:

```bash
sudo -iu hermes systemctl --user status hermes-dashboard.service --no-pager
sudo -iu hermes systemctl --user is-enabled hermes-dashboard.service
curl -fsS http://127.0.0.1:8080 >/dev/null
```

If `hermes_webui_enabled: true`, check the loopback WebUI:

```bash
sudo -iu hermes systemctl --user status hermes-webui.service --no-pager
sudo -iu hermes systemctl --user is-enabled hermes-webui.service
curl -fsS http://127.0.0.1:8787/health
```

If `hermes_nginx_enabled: true`, check nginx and the authenticated HTTPS endpoint:

```bash
sudo nginx -t
curl -skI https://hermes.example.ch/ | sed -n '1,8p'
curl -skI -u chris:"${HERMES_DASHBOARD_PASSWORD}" https://hermes.example.ch/ | sed -n '1,8p'
```

Expected behaviour: the unauthenticated request returns `401 Unauthorized`; the authenticated request reaches the Hermes dashboard.

When WebUI is enabled, check its second vhost with a GET request. The WebUI backend does not implement `HEAD` on `/`, so `curl -I` may return `501 Not Implemented` even when a normal browser GET works:

```bash
curl -sk https://hermes1.example.ch/ -u chris:"${HERMES_WEBUI_PASSWORD}" | grep -Eo '<title>[^<]+'
```

If Playwright is enabled, the role installs the Rocky/RHEL runtime libraries via `dnf`, installs Chromium with `npx playwright install chromium`, checks direct shared-library dependencies with `ldd`, and then runs a real Chromium headless smoke test. Manual checks:

```bash
sudo -iu hermes bash -lc 'ldd ~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell | grep "not found"'
sudo -iu hermes bash -lc 'cd ~/.hermes/hermes-agent && node -e '\''(async()=>{const {chromium}=require("playwright"); const browser=await chromium.launch({headless:true}); const page=await browser.newPage(); await page.goto("data:text/html,<h1>playwright-ok</h1>"); console.log(await page.textContent("h1")); await browser.close();})().catch(error=>{console.error(error.stack||error); process.exit(1);})'\'''
```

The direct `dnf` package list is intentional. Playwright's own `npx playwright install-deps chromium` is primarily Debian/Ubuntu-oriented and may print `BEWARE: your OS is not officially supported by Playwright; installing dependencies for ubuntu24.04-x64 as a fallback` on Rocky Linux.

## Messaging Gateway / Telegram Pairing

To reconfigure the existing Hermes install quickly, use:

```bash
sudo -iu hermes hermes setup --quick
```

For messaging, the more important step is gateway/platform pairing. Configure Telegram or another messenger with the gateway wizard as the `hermes` user:

```bash
sudo -iu hermes hermes gateway setup
```

For Telegram, choose Telegram in the wizard and provide the bot token from BotFather. The role installs and enables `hermes-gateway.service` by default; restart it after changing gateway config:

```bash
sudo -iu hermes systemctl --user restart hermes-gateway.service
sudo -iu hermes systemctl --user status hermes-gateway.service --no-pager
```

Restart both role-managed services as the `hermes` user:

```bash
sudo -iu hermes systemctl --user restart hermes-gateway.service
sudo -iu hermes systemctl --user restart hermes-dashboard.service
```

When a user messages the bot, approve the pairing code:

```bash
sudo -iu hermes hermes pairing list
sudo -iu hermes hermes pairing approve telegram <CODE>
```

## Security Notes

- The Hermes Linux user is deliberately not added to `wheel` or any sudo group.
- The dashboard service is loopback-only by default (`127.0.0.1:8080`) and does not need a direct firewall rule.
- For browser access, prefer `hermes_nginx_enabled: true` with HTTPS and Basic Auth. The default TLS and htpasswd paths are scoped by `hermes_dashboard_nginx_fqdn` to support several Hermes vhosts on the same VM.
- Use one DNS vhost per Hermes user. Subfolder deployments are not recommended for Hermes dashboard.
- Secrets belong in `/home/<user>/.hermes/.env`, `/home/<user>/.hermes/auth.json`, Hermes' auth store, or Ansible Vault variables. Do not commit tokens or real Basic Auth passwords to Git.

## Manual Setup Documentation

For a copy/paste manual runbook that mirrors this role, see [`docs/manual-setup-rocky10.md`](https://github.com/joe-speedboat/ansible.hermes_setup/blob/master/docs/manual-setup-rocky10.md).

## License

GPLv3

Copyright (c) Chris Ruettimann <chris@bitbull.ch>
