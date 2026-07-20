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
- installs, enables, and starts a loopback-only `hermes-webui.service` systemd user service by default
- exposes the dashboard through nginx HTTPS as a TLS reverse proxy; dashboard authentication is configured in Hermes itself
- exposes Hermes WebUI through a separate nginx HTTPS reverse proxy by default; WebUI password authentication is configured in the WebUI itself
- keeps `80/tcp` open when the nginx HTTP listener is enabled for ACME HTTP-01 challenges and HTTP-to-HTTPS redirects
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
- `hermes_webui_enabled`: install Hermes WebUI from `https://github.com/nesquena/hermes-webui`. Default: `true`; set to `false` for dashboard-only deployments
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
- `hermes_webui_max_upload_mb`: maximum WebUI upload size in MiB. Default: `220`; the WebUI receives this value as `HERMES_WEBUI_MAX_UPLOAD_MB`
- `hermes_ssh_setup`: create persistent `{{ hermes_home }}/.ssh` and `known_hosts`. Default: `true`
- `hermes_ssh_generate_key`: generate the configured keypair when the private key is missing. Default: follows `hermes_ssh_setup`
- `hermes_ssh_key_type`: SSH key type. Default: `ed25519`; supported values: `ed25519`, `rsa`, `ecdsa`
- `hermes_ssh_key_path`: private key path. Default: `{{ hermes_home }}/.ssh/id_ed25519`; paths must remain below `{{ hermes_home }}/.ssh`
- `hermes_ssh_known_hosts_path`: known-hosts path. Default: `{{ hermes_home }}/.ssh/known_hosts`
- `hermes_bootstrap_dir`: controller-side directory containing optional Hermes bootstrap files. Default: empty/disabled
- `hermes_bootstrap_mode`: bootstrap behavior: `disabled`, `missing` (preserve existing target files), or `overwrite`. Default: `disabled`
- `hermes_bootstrap_include_auth`: also copy `auth.json` from the bootstrap directory. Default: `false`; keep disabled unless the source is protected
- `hermes_nginx_enabled`: install nginx HTTPS reverse proxies for enabled browser UIs. Default: `true`
- `hermes_nginx_http_enabled`: enable the HTTP listener on `80/tcp` for the ACME webroot and HTTP-to-HTTPS redirect. Default: `true`
- `hermes_nginx_letsencrypt_challenge_method`: ACME challenge method (`tls-alpn-01` or `webroot`). Default: `webroot`
- `hermes_dashboard_nginx_fqdn`: public dashboard DNS name for the nginx vhost. Default: `adm-{{ ansible_fqdn | default(inventory_hostname) }}`
- `hermes_dashboard_nginx_conf`: nginx vhost config path. Default: `/etc/nginx/conf.d/{{ hermes_dashboard_nginx_fqdn }}.conf`
- `hermes_nginx_enable_firewall`: manage firewalld ports. Default: `true`
- `hermes_nginx_client_max_body_size`: nginx request-body limit. Default: `{{ hermes_webui_max_upload_mb }}m`, derived from the WebUI upload limit; override only when intentionally different
- `firewalld_open_ports`: base list of ports to open in firewalld when nginx firewall management is enabled. Default: `['443/tcp']`; `80/tcp` is added automatically when `hermes_nginx_http_enabled: true`
- `hermes_nginx_tls_dir`: directory for role-managed self-signed TLS material. Default: `/etc/pki/tls/hermes`
- `hermes_dashboard_nginx_tls_cert`: certificate path. Default: `{{ hermes_nginx_tls_dir }}/{{ hermes_dashboard_nginx_fqdn }}_tls.crt`
- `hermes_dashboard_nginx_tls_key`: private key path. Default: `{{ hermes_nginx_tls_dir }}/{{ hermes_dashboard_nginx_fqdn }}_tls.key`
- `hermes_nginx_generate_self_signed_cert`: generate a self-signed cert when no external cert is provided. Default: `true`
- `hermes_nginx_letsencrypt_enabled`: request and use a combined Let's Encrypt certificate for the enabled nginx vhosts. Default: `false`
- `hermes_nginx_letsencrypt_email`: ACME registration email. Default: `{{ hermes_user }}@{{ hermes_webui_nginx_fqdn }}`
- `hermes_dashboard_auth_username`: application-side dashboard username. Default: empty; required when `hermes_dashboard_enabled: true`
- `hermes_dashboard_auth_password_hash`: upstream scrypt password hash. Default: empty; either this or the plaintext fallback is required when `hermes_dashboard_enabled: true`
- `hermes_dashboard_auth_password`: plaintext fallback for the application config. Default: empty; prefer `hermes_dashboard_auth_password_hash`; one of the two password variables is required when `hermes_dashboard_enabled: true`
- `hermes_dashboard_auth_secret`: optional dashboard session-signing secret. Default: empty
- `hermes_webui_password`: application-side WebUI password. Default: empty; required when `hermes_webui_enabled: true`
- `hermes_webui_nginx_fqdn`: public WebUI DNS name for the second nginx vhost. Default: `{{ ansible_fqdn | default(inventory_hostname) }}`
- `hermes_webui_nginx_conf`: WebUI nginx vhost config path. Default: `/etc/nginx/conf.d/{{ hermes_webui_nginx_fqdn }}.conf`
- `hermes_webui_nginx_tls_cert`: WebUI certificate path. Default: `{{ hermes_nginx_tls_dir }}/{{ hermes_webui_nginx_fqdn }}_tls.crt`
- `hermes_webui_nginx_tls_key`: WebUI private key path. Default: `{{ hermes_nginx_tls_dir }}/{{ hermes_webui_nginx_fqdn }}_tls.key`
- `ansible_enable`: install a user-scope Ansible runtime for the dedicated Hermes user via `https://ansible-uv.bitbull.ch`. Default: `false`
- `ansible_home`: Ansible userspace install directory. Default: `{{ hermes_home }}/ansible`
- `configure_codex`: configure non-secret Codex defaults. Default: `true`
- `hermes_codex_provider`: default provider. Default: `openai-codex`
- `hermes_codex_model`: default model. Default: `gpt-5.5`
- `hermes_playwright_enabled`: install Playwright support. Default: `true`
- `hermes_playwright_browsers`: browser list for `npx playwright install`. Default: `['chromium']`
- `hermes_playwright_ldd_check_enabled`: run `ldd` against Playwright's Chromium headless shell and fail if direct shared libraries are missing. Default: `true`
- `hermes_playwright_smoke_test_enabled`: run a real Chromium headless smoke test after Playwright install. Default: `true`
- `hermes_playwright_build_tools_enabled`: install build tools for npm native module rebuilds used by Playwright/Hermes dependencies such as `node-pty`. Default: `true`

> The role fails fast when the dashboard is enabled without a username and password/hash, or when the WebUI is enabled without a password. Configure `hermes_dashboard_auth_*` and `hermes_webui_password` with Ansible Vault; the role contains no default password. nginx does not store or enforce application credentials.

### Optional bootstrap

Set `hermes_bootstrap_dir` to a directory on the Ansible controller containing any of:

```text
SOUL.md
config.yaml
.env
memories/
skills/
plugins/
cron/
workspace/
auth.json              # excluded by default
```

Use `hermes_bootstrap_mode: missing` to copy only files that are not already present on the target, or `hermes_bootstrap_mode: overwrite` to replace matching files. The default is `disabled`. `auth.json` is copied only when `hermes_bootstrap_include_auth: true` is explicitly set; store the bootstrap source outside the repository and protect it like a credential file. Bootstrap content is copied to `{{ hermes_home }}/.hermes` and the configured WebUI workspace, with Hermes ownership and restrictive file modes.

Example:

```yaml
hermes_bootstrap_dir: "{{ playbook_dir }}/files/hermes-bootstrap"
hermes_bootstrap_mode: missing
hermes_bootstrap_include_auth: false
```

### Example Playbook: single Hermes dashboard behind nginx

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

        hermes_dashboard_auth_username: dashboard-admin
        hermes_dashboard_auth_password_hash: "{{ vault_hermes_dashboard_password_hash }}"

        hermes_webui_enabled: false

        hermes_nginx_enabled: true
        hermes_dashboard_nginx_fqdn: hermes.example.ch
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
        hermes_nginx_letsencrypt_enabled: true
        hermes_nginx_letsencrypt_email: chris@example.com
        # Built-in Hermes dashboard:
        hermes_dashboard_nginx_fqdn: hermes1-adm.example.ch
        # Hermes WebUI:
        hermes_webui_nginx_fqdn: hermes1.example.ch

        hermes_dashboard_auth_username: dashboard-admin
        hermes_dashboard_auth_password_hash: "{{ vault_hermes_password_hash }}"
        hermes_webui_password: "{{ vault_hermes_webui_password }}"
...
```

## Example Playbook: multiple Hermes users via DNS vhosts

Use one Linux user, one loopback dashboard port, and one nginx vhost per Hermes instance. This avoids subfolder rewrites for `/api/...` and WebSocket endpoints.

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
        hermes_dashboard_auth_username: "{{ hermes_instance.auth_user }}"
        hermes_dashboard_auth_password: "{{ hermes_instance.auth_password }}"
        hermes_webui_enabled: false
...
```

## Why vhosts instead of subfolders?

Hermes dashboard and Hermes WebUI use root-relative frontend assets, REST API routes under `/api/...`, and WebSocket endpoints. DNS vhosts keep those paths unchanged per interface and per instance. Subfolder deployments would require fragile path rewriting and are not recommended.

For the built-in dashboard, the nginx template forwards the configured dashboard bind address as `Host` and clears `Origin` so Hermes' dashboard Host/Origin protections continue to work behind the reverse proxy. For Hermes WebUI, the template preserves the browser-visible `Host` and `X-Forwarded-*` headers and configures `HERMES_WEBUI_ALLOWED_ORIGINS` for the WebUI service. Authentication is handled by the target application; nginx does not add, remove, or enforce Basic Auth credentials.

For large WebUI uploads, configure the same limit in the application and nginx. The role defaults to `220 MiB` via `hermes_webui_max_upload_mb: 220`; nginx derives `hermes_nginx_client_max_body_size` as `220m`. If you override either value, keep nginx at least as large as the WebUI limit so nginx does not reject the request first.

When `hermes_nginx_enabled: true`, the role exposes the enabled browser interfaces through nginx on HTTPS port `443/tcp`. Because `hermes_nginx_http_enabled` defaults to `true`, it also opens `80/tcp`; port 80 serves only the ACME challenge path and redirects all other requests to HTTPS. Set `hermes_nginx_http_enabled: false` only when using a certificate workflow that does not require HTTP-01 and you explicitly want HTTPS-only behavior.

When `hermes_nginx_letsencrypt_enabled: true`, the role keeps self-signed certificates as the bootstrap fallback, serves HTTP-01 challenges from `/.well-known/acme-challenge/`, requests one combined Let's Encrypt certificate for the dashboard FQDN plus the WebUI FQDN when WebUI is enabled, and re-renders both nginx vhosts to use `/etc/letsencrypt/live/{{ hermes_dashboard_nginx_fqdn }}/fullchain.pem` and `privkey.pem` after issuance. Port `80/tcp` must be reachable from the Internet for HTTP-01 validation; when `hermes_nginx_enable_firewall: true`, the role adds it automatically.

For a real disposable cloud lab checklist covering Hetzner VM creation, LuaDNS records, Let's Encrypt issuance, application-auth checks, and idempotency expectations, see [`docs/hetzner-lab-letsencrypt.md`](docs/hetzner-lab-letsencrypt.md).
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

If `ansible_enable: true`, the role installs Ansible below `{{ hermes_home }}/ansible`, wires the runtime profile into the Hermes user's `.bashrc`, verifies the executable runtime at `{{ hermes_home }}/ansible/current/bin/ansible`, and reports its version during the run. Manual check:

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

If `hermes_nginx_enabled: true`, check nginx and the application endpoint:

```bash
sudo nginx -t
curl -skI https://hermes.example.ch/ | sed -n '1,8p'
```

The HTTP status and login behavior are supplied by the dashboard/WebUI application configuration, not nginx.

When WebUI is enabled, check its second vhost with a GET request. The WebUI backend does not implement `HEAD` on `/`, so `curl -I` may return `501 Not Implemented` even when a normal browser GET works:

```bash
curl -sk https://hermes1.example.ch/
```

If Playwright is enabled, the role first synchronizes the Rocky Node.js runtime packages (`nodejs`, `nodejs-libs`, `npm`, and `c-ares`) before running npm. This repairs hosts with a partial Node/c-ares update that would otherwise fail with a `symbol lookup error`. It then installs the Rocky/RHEL runtime libraries via `dnf`, installs Chromium with `npx playwright install chromium`, checks direct shared-library dependencies with `ldd`, and runs a real Chromium headless smoke test.

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
- For browser access, prefer `hermes_nginx_enabled: true` with HTTPS; application authentication is configured in Hermes dashboard/WebUI.
- Use one DNS vhost per Hermes user. Subfolder deployments are not recommended for Hermes dashboard.
- Secrets belong in `/home/<user>/.hermes/.env`, `/home/<user>/.hermes/auth.json`, Hermes' auth store, or Ansible Vault variables. Do not commit tokens, dashboard password hashes, or WebUI passwords to Git.

## Manual Setup Documentation

For a copy/paste manual runbook that mirrors this role, see [`docs/manual-setup-rocky10.md`](https://github.com/joe-speedboat/ansible.hermes_setup/blob/master/docs/manual-setup-rocky10.md).

## License

GPLv3

Copyright (c) Chris Ruettimann <chris@bitbull.ch>
