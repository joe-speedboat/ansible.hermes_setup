# Changelog

## Unreleased

### Features

- Adds optional nginx Let's Encrypt support controlled by `hermes_nginx_letsencrypt_enabled`, disabled by default.
- Adds `hermes_nginx_letsencrypt_email` with the requested default `{{ hermes_user }}@{{ hermes_webui_nginx_fqdn }}`.
- Keeps `hermes_nginx_letsencrypt_staging`, `hermes_nginx_letsencrypt_mode`, webroot, and live certificate paths as internal role vars.
- Uses Certbot webroot HTTP-01 validation, opens `80/tcp` when nginx firewall management is enabled, and serves `/.well-known/acme-challenge/` without Basic Auth.
- Requests one combined certificate for the dashboard vhost plus the WebUI vhost when WebUI is enabled, then re-renders both vhosts to use `/etc/letsencrypt/live/{{ hermes_dashboard_nginx_fqdn }}/fullchain.pem` and `privkey.pem`.
- Installs a certbot deploy hook that reloads nginx after renewals and enables `certbot-renew.timer` when available.

### Documentation

- Documents the new defaults and public-DNS usage in `README.md`.
- Updates the Rocky 10 manual setup runbook with the Certbot dependency and role behavior.

### Tests and validation

- Verified locally:
  - YAML parse of all role playbooks/task files -> ok
  - `ansible-playbook tests/nginx_render.yml -i localhost, -c local` -> assertions passed
  - `ansible-playbook tests/nginx_tasks_syntax.yml -i localhost, -c local --syntax-check` -> ok
  - full role syntax check through the role symlink harness with Let's Encrypt enabled -> ok
  - `git diff --check` -> ok
- Verified on Hetzner Rocky Linux 10.1 with `hermes_nginx_letsencrypt_enabled: true`:
  - `certbot-4.2.0-1.el10_2.noarch` installed by the role
  - HTTP-01 challenge webroot returned `200 acme-ok` for both nginx FQDNs before issuance
  - combined Let's Encrypt certificate issued for `dashboard-hermes.lab.bitbull.ch` and `hermes.lab.bitbull.ch`
  - nginx config uses `/etc/letsencrypt/live/dashboard-hermes.lab.bitbull.ch/fullchain.pem` for both vhosts
  - `nginx -t` -> ok
  - `certbot-renew.timer` -> enabled and active
  - public HTTPS GET with Basic Auth returned `HTTP 200` for both dashboard and WebUI
  - steady-state idempotence pass -> `changed=0 failed=0`

## ansible.hermes_setup v1.2.1 - 2026-07-02

Target branch: `master`

### Highlights

- Fixes fresh Rocky Linux 10 minimal-host convergence for the default nginx/firewalld and Playwright setup.
- Keeps `hermes_nginx_enable_firewall: true` usable on cloud images that do not preinstall `firewalld`.
- Makes the default Playwright-enabled install self-contained when npm falls back to native `node-gyp` builds such as `node-pty`.

### Fixes

- Installs `firewalld` with the nginx reverse-proxy prerequisites.
- Enables and starts `firewalld` before running any `firewall-cmd` tasks.
- Changes `hermes_playwright_build_tools_enabled` default to `true` so `make`, `gcc`, and `gcc-c++` are present before Playwright/npm native module builds.

### Documentation

- Updates the Rocky 10 manual setup runbook to include `epel-release`, `ffmpeg-free`, `ripgrep`, `firewalld`, `policycoreutils-python-utils`, and default Playwright build tools.
- Updates the install flowchart so Phase 35 shows `firewalld` installation/start before port management.
- Confirms README variables already match the v1.2.1 defaults.

### Tests and validation

- Verified before release preparation:
  - static Python assertions for role defaults and task ordering -> passed
  - `ansible-playbook tests/nginx_tasks_syntax.yml --syntax-check` -> ok
  - clean Hetzner Rocky 10.1 lab converge with dashboard and WebUI enabled: `ok=101 changed=3 failed=0` after the fixes
  - steady-state idempotence pass: `ok=100 changed=0 failed=0`
  - independent service checks: `nginx`, `firewalld`, `hermes-gateway.service`, `hermes-dashboard.service`, and `hermes-webui.service` active
  - loopback checks: dashboard `HTTP 200`, WebUI `/health` `HTTP 200`
  - `nginx -t` -> ok
  - `firewall-cmd --list-ports` -> `443/tcp`
  - Playwright Chromium smoke test -> `playwright-ok`
  - dashboard and WebUI HTTPS vhosts verified with Basic Auth via `curl --resolve`

### Merged pull requests since v1.2.0

- #25 - Fix Rocky 10 nginx firewall prerequisites.

### Changed files since v1.2.0

- `README.md`
- `CHANGELOG.md`
- `defaults/main.yml`
- `docs/install-flowchart.md`
- `docs/manual-setup-rocky10.md`
- `tasks/rhelAll-10/35_nginx.yml`
- `tests/test_prepare_static.py`

## ansible.hermes_setup v1.2.0 - 2026-06-06

Target branch: `master`

### Highlights

- Adds optional Hermes WebUI installation and management as a dedicated loopback-only systemd user service.
- Adds a separate nginx HTTPS + Basic Auth vhost for Hermes WebUI, with dashboard/WebUI-specific variable names.
- Fixes clean Rocky 10 lab convergence when `ansible_enable: true`, `hermes_webui_enabled: true`, and Playwright build tools are enabled.
- Keeps the Ansible user runtime below `{{ ansible_home }}` and prevents `runuser` from inheriting `/root` as its working directory.
- Installs npm native build tools before service startup when explicitly enabled, so dashboard/WebUI native modules can build on clean hosts.

### Features

#### Hermes WebUI service

- New opt-in `hermes_webui_enabled` default, disabled by default.
- New WebUI repository, checkout, bind, state, workspace, and allowed-origin defaults.
- New `hermes-webui.service` user unit template.
- Role-managed health check waits for the WebUI `/health` endpoint when enabled.

#### WebUI nginx vhost

- Adds WebUI-specific nginx FQDN, config path, TLS certificate/key, Basic Auth file, Basic Auth realm, and upstream defaults.
- Renders dashboard and WebUI reverse proxies from the shared nginx template while keeping component-specific variables clear.
- Documents the requirement for DNS records for every public dashboard/WebUI vhost.

### Fixes

- Adds `chdir: "{{ hermes_home }}"` to Ansible runtime shell tasks so the `ansible-uv` installer does not fail from an inaccessible `/root` working directory.
- Moves `hermes_playwright_build_tools_packages` installation into phase 10, before services start and before any `npm install` can require native build tooling.
- Adds `gh` to the Rocky/RHEL base package list for GitHub CLI workflows on installed Hermes hosts.
- Adjusts the default WebUI vhost naming to `web-{{ hermes_dashboard_nginx_fqdn }}`.

### Documentation

- Updates README variables and examples for Hermes WebUI service and nginx vhost support.
- Updates the Rocky 10 manual runbook references for the new WebUI endpoint behavior.
- Updates post-install next steps to mention the generated WebUI vhost.

### Tests and validation

- Extends nginx render and syntax coverage for dashboard plus WebUI vhosts.
- Extends static tests for WebUI defaults, package ordering, and Ansible installer working directory.
- Verified before release preparation:
  - clean Rocky 10.1 lab converge with `ansible_enable: true`, `hermes_webui_enabled: true`, and `hermes_playwright_build_tools_enabled: true`: `ok=106 changed=37 failed=0`
  - steady-state idempotence pass: `ok=103 changed=0 failed=0`
  - independent service checks: `hermes-gateway.service`, `hermes-dashboard.service`, and `hermes-webui.service` active
  - loopback checks: dashboard `HTTP 200`, WebUI health `HTTP 200`
  - `nginx -t` -> ok
  - Playwright Chromium smoke test -> `playwright-ok`
  - `git diff --check` -> ok
  - `uvx --python 3.12 --from pytest --with pyyaml pytest -q` -> `2 passed`
  - `ansible-playbook tests/test.yml -i localhost, -c local --syntax-check` with temporary `ANSIBLE_ROLES_PATH` -> ok
  - `ansible-playbook tests/nginx_render.yml -i localhost, -c local --syntax-check` with temporary `ANSIBLE_ROLES_PATH` -> ok
  - `ansible-playbook tests/nginx_tasks_syntax.yml -i localhost, -c local --syntax-check` with temporary `ANSIBLE_ROLES_PATH` -> ok
  - `ansible-playbook tests/nginx_render.yml -i localhost, -c local` with temporary `ANSIBLE_ROLES_PATH` -> assertions passed

### Merged pull requests since v1.1.1

- #22 - Add Hermes WebUI vhost support.
- #23 - Fix Hermes setup lab converge on Rocky 10.

### Changed files since v1.1.1

- `CHANGELOG.md`
- `README.md`
- `defaults/main.yml`
- `docs/manual-setup-rocky10.md`
- `tasks/rhelAll-10/10_prepare.yml`
- `tasks/rhelAll-10/20_install_configure.yml`
- `tasks/rhelAll-10/25_ansible.yml`
- `tasks/rhelAll-10/30_services.yml`
- `tasks/rhelAll-10/35_nginx.yml`
- `tasks/rhelAll-10/40_playwright.yml`
- `tasks/rhelAll-10/50_next_steps.yml`
- `templates/hermes-webui.env.j2`
- `templates/hermes-webui.service.j2`
- `templates/nginx-hermes.conf.j2`
- `tests/nginx_render.yml`
- `tests/nginx_tasks_syntax.yml`
- `tests/test_ansible_addon_static.py`
- `tests/test_prepare_static.py`
- `vars/main.yml`

## ansible.hermes_setup v1.1.1 - 2026-06-01

Target branch: `docs/fqdn-scoped-nginx-defaults`

### Highlights

- Makes the default nginx reverse-proxy artefacts safe for multi-instance Hermes deployments on one VM.
- Scopes generated TLS certificate/key paths and Basic Auth files by `hermes_dashboard_nginx_fqdn`.
- Uses the vhost FQDN as the default Basic Auth realm, making browser prompts clearer for multi-vhost setups.
- Updates README and the Rocky 10 manual setup runbook to match the new defaults.

### Changed defaults

- `hermes_dashboard_nginx_fqdn`: now defaults to `dash-{{ ansible_fqdn | default(inventory_hostname) }}`.
- `hermes_webui_nginx_fqdn`: now defaults to `web-{{ hermes_dashboard_nginx_fqdn }}`.
- `hermes_dashboard_nginx_tls_cert`: now defaults to `{{ hermes_nginx_tls_dir }}/{{ hermes_dashboard_nginx_fqdn }}_tls.crt`.
- `hermes_dashboard_nginx_tls_key`: now defaults to `{{ hermes_nginx_tls_dir }}/{{ hermes_dashboard_nginx_fqdn }}_tls.key`.
- `hermes_dashboard_nginx_basic_auth_file`: now defaults to `/etc/nginx/.htpasswd-hermes-{{ hermes_dashboard_nginx_fqdn }}`.
- `hermes_dashboard_nginx_basic_auth_realm`: now defaults to `{{ hermes_dashboard_nginx_fqdn }}`.

### Why this changed

The role supports one Linux user, one loopback dashboard port, and one nginx vhost per Hermes instance. With the previous defaults, repeated role invocations on the same VM reused shared paths such as `/etc/pki/tls/hermes/tls.crt`, `/etc/pki/tls/hermes/tls.key`, and `/etc/nginx/.htpasswd-hermes`. That made multi-instance setups prone to overwriting or unintentionally sharing TLS and Basic Auth artefacts between vhosts.

The new FQDN-scoped defaults make the common multi-instance pattern safe without requiring every playbook to override the TLS and htpasswd paths manually.

### Documentation

- Documents the FQDN-scoped nginx TLS certificate/key defaults and Basic Auth file/realm defaults in `README.md`.
- Updates the multi-instance README example to rely on FQDN-scoped defaults instead of per-user custom paths.
- Updates `docs/manual-setup-rocky10.md` so the manual nginx example uses FQDN-scoped TLS and htpasswd paths.
- Adds a security note explaining that the default TLS and htpasswd paths are scoped by `hermes_dashboard_nginx_fqdn` for multiple Hermes vhosts on the same VM.

### Tests and validation

- Extends `tests/test_prepare_static.py` with assertions for the FQDN-scoped nginx defaults.
- Verified before release preparation:
  - `uvx --python 3.12 pytest -v` -> `2 passed`
  - `ansible-playbook tests/test.yml -i localhost, -c local --syntax-check` with temporary `ANSIBLE_ROLES_PATH` -> ok
  - `ansible-playbook tests/nginx_render.yml -i localhost, -c local --syntax-check` with temporary `ANSIBLE_ROLES_PATH` -> ok
  - `ansible-playbook tests/nginx_tasks_syntax.yml -i localhost, -c local --syntax-check` with temporary `ANSIBLE_ROLES_PATH` -> ok
  - `ansible-playbook tests/nginx_render.yml -i localhost, -c local` with temporary `ANSIBLE_ROLES_PATH` -> assertions passed
  - `git diff --check` -> ok

### Changed files since v1.1.0

- `CHANGELOG.md`
- `README.md`
- `defaults/main.yml`
- `docs/manual-setup-rocky10.md`
- `tests/test_prepare_static.py`

## ansible.hermes_setup v1.1.0 - 2026-05-30

Target commit: `86b27a2` (`master`)

### Highlights

- Adds an optional user-scope Ansible runtime for the dedicated Hermes user.
- Makes Hermes CLI helper packages more complete on Rocky/RHEL 10 by installing EPEL first and adding `ripgrep` plus `ffmpeg-free`.
- Fixes the Ansible runtime installer environment so Rundeck/automation environment variables cannot make the install target the wrong user.
- Adds a full install-flow Mermaid diagram documenting all role phases.
- Adds static regression coverage for the Ansible runtime installer and repository/base package ordering.

### Features

#### Optional Ansible runtime for Hermes user

- New opt-in `ansible_enable` default, disabled by default.
- New `ansible_install_url` default: `https://ansible-uv.bitbull.ch`.
- New `ansible_home` default: `{{ hermes_home }}/ansible`.
- New phase `25_ansible.yml` installs a user-scope Ansible runtime below the Hermes home directory.
- The role wires the runtime profile into the Hermes user's `.bashrc`.
- The role verifies the installed runtime with `ansible --version` when enabled.

#### Repository packages before application packages

- New generic `hermes_repo_packages` list for packages that enable repositories before runtime packages are installed.
- Default repository package: `epel-release`.
- Repository packages are installed before `hermes_base_packages`, so EPEL-provided packages resolve reliably on Rocky/RHEL 10.

#### Hermes CLI helper packages

- Adds `ripgrep` to `hermes_base_packages` for Hermes' fast file search support.
- Adds `gh` to `hermes_base_packages` so Hermes installs include the GitHub CLI for repository and PR workflows.
- Adds `ffmpeg-free` to `hermes_base_packages`, providing `/usr/bin/ffmpeg` on Rocky/RHEL 10 from EPEL.

### Fixes

- Fixes the `ansible-uv` installer call to pass `INSTALL_USER={{ hermes_user }}` explicitly.
- Prevents inherited automation/Rundeck environment values such as `INSTALL_USER=rundeck-ops` from breaking unprivileged user installs.
- Keeps repository-enabling packages separate from runtime packages, avoiding package resolution failures when EPEL packages are needed.

### Documentation

- Adds `docs/install-flowchart.md` with a Mermaid install flow covering all role phases:
  - Phase 10: system preparation
  - Phase 20: Hermes install/configure
  - Phase 25: optional Ansible runtime
  - Phase 30: systemd user services
  - Phase 35: nginx reverse proxy
  - Phase 40: Playwright browsers
  - Phase 50: next steps
- Fixes the README/manual setup link to use the absolute GitHub URL.

### Tests and validation

- Adds `tests/test_ansible_addon_static.py` for the optional Ansible runtime installer.
- Adds `tests/test_prepare_static.py` for repository package ordering and required CLI helper packages.
- Verified before release preparation:
  - `uv run --python 3.12 pytest -v` -> `2 passed`
  - `ansible-playbook tests/test.yml -i localhost, -c local --syntax-check` -> ok
  - `ansible-playbook tests/nginx_render.yml -i localhost, -c local --syntax-check` -> ok
  - `ansible-playbook tests/nginx_tasks_syntax.yml -i localhost, -c local --syntax-check` -> ok
  - `ansible-playbook tests/nginx_render.yml -i localhost, -c local` -> assertions passed
  - `git diff --check` -> ok
- Rocky 10.1 lab validation for the package changes was completed on `test-hermes1`:
  - first successful role run: `ok=41 changed=7 failed=0 skipped=48`
  - idempotency run: `ok=40 changed=0 failed=0 skipped=49`
  - verified packages/commands: `epel-release`, `ripgrep`, `ffmpeg-free`, `/usr/bin/rg`, `/usr/bin/ffmpeg`

### Merged pull requests since v1.0.0

- #15 - docs: use absolute manual runbook link
- #16 - feat: add optional Ansible runtime install
- #17 - docs: add Mermaid install flowchart for all 7 Ansible phases
- #18 - fix: pass explicit `INSTALL_USER` into ansible-uv installer
- #19 - fix: install EPEL before Hermes packages

### Changed files since v1.0.0

- `README.md`
- `defaults/main.yml`
- `docs/install-flowchart.md`
- `tasks/rhelAll-10/10_prepare.yml`
- `tasks/rhelAll-10/25_ansible.yml`
- `tests/test_ansible_addon_static.py`
- `tests/test_prepare_static.py`

## ansible.hermes_setup v1.0.0

Initial tagged release.
