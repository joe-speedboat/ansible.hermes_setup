# AGENTS.md

This file is the agent-facing contribution and verification guide for `joe-speedboat.hermes_setup`.
It follows the open `AGENTS.md` convention described at [agents.md](https://agents.md/): keep repository context, commands, conventions, and verification requirements in a predictable Markdown file at the repository root.

## Project overview

`ansible.hermes_setup` is an Ansible role for installing and operating Hermes Agent on Rocky Linux 10 as a dedicated unprivileged Linux user.

The role can manage these independent components:

- Hermes Agent/gateway: the core user service.
- Hermes dashboard: a browser-facing application on the internal dashboard port.
- Hermes WebUI: a separate browser-facing application on the internal WebUI port.
- nginx: the public TLS reverse proxy for enabled browser interfaces.
- firewalld: nginx firewall management, including HTTPS and the conditional HTTP listener.
- Playwright/Chromium: browser automation support.
- user-scope Ansible runtime: an optional Ansible installation for the `hermes` user.

Read `README.md`, `defaults/main.yml`, the selected task files, and the existing tests before changing behavior. Do not infer behavior from documentation alone.

## Repository layout

- `defaults/main.yml` — public role defaults.
- `vars/main.yml` — role variables and derived values.
- `tasks/main.yml` and `tasks/include-file.yml` — task dispatcher.
- `tasks/rhelAll-10/` — Rocky/RHEL 10 implementation, executed in numeric order.
- `templates/` — systemd units, nginx configuration, and application environment files.
- `handlers/main.yml` — service and nginx handlers.
- `tests/` — static tests and Ansible render/syntax fixtures.
- `docs/` — manual setup and flow documentation.
- `CHANGELOG.md` — release history and current unreleased changes.

## Working rules

1. Inspect first. Check `git status --short --branch`, remotes, the current branch, relevant defaults, task files, templates, tests, README, changelog, and applicable docs before editing.
2. Never overwrite user work, secrets, inventories, or unrelated changes.
3. Keep code, documentation, tests, and changelog changes synchronized.
4. Keep tasks idempotent and safe to rerun. A successful first run is not sufficient.
5. Prefer fully qualified Ansible module names such as `ansible.builtin.command` and `ansible.builtin.dnf`.
6. Preserve Rocky/RHEL behavior and check package names against the target distribution.
7. Use `ansible.builtin.command` for direct executable checks when shell profile side effects are not part of the behavior being tested.
8. Mark credential-bearing tasks `no_log: true`; never place passwords, hashes, tokens, cookies, private keys, or real internal endpoints in Git, examples, test output, or PR text.
9. Public examples must use `example.com` and placeholders or Ansible Vault variables.
10. English is required for code, documentation, scripts, tests, commits, and PRs.
11. Do not claim a scenario was tested unless the exact scenario was executed and its output was inspected.

## Development and validation commands

Run these from the repository root:

```bash
pytest -q
ANSIBLE_ROLES_PATH=/home/hermes/work ansible-playbook tests/nginx_render.yml --syntax-check
ANSIBLE_ROLES_PATH=/home/hermes/work ansible-playbook tests/nginx_render.yml
ANSIBLE_ROLES_PATH=/home/hermes/work ansible-playbook tests/nginx_tasks_syntax.yml --syntax-check
git diff --check
```

Use the exact controller environment and role path that will execute the consumer playbook, especially for Rundeck/AWX. A local checkout test does not prove that `/etc/ansible/roles/joe-speedboat.hermes_setup` or the controller's collections are current.

For a real target, use a disposable Rocky/RHEL lab host and a separate harness. The minimum real-run sequence is:

```bash
ANSIBLE_ROLES_PATH=roles ansible-playbook -i inventory.ini setup.yml --syntax-check
ANSIBLE_ROLES_PATH=roles ansible-playbook -i inventory.ini setup.yml --diff
ANSIBLE_ROLES_PATH=roles ansible-playbook -i inventory.ini setup.yml --diff
```

The second real run must be reviewed for idempotency. Do not use a production or personal VM as a disposable test target.

For enabled addon paths, run the real downstream command, not only syntax or template checks:

- `ansible_enable: true`: verify the active `{{ ansible_home }}/current/bin/ansible` runtime as user `hermes`.
- `hermes_playwright_enabled: true`: run npm installation, browser installation, the Chromium smoke test, and the direct `ldd` dependency check.

For a full lifecycle change, test install, idempotency, uninstall, reinstall, and final idempotency. Remove generated `__pycache__/` directories before committing.

## Configuration semantics

The role defaults currently enable the gateway, dashboard, WebUI, nginx, HTTP ACME/redirect handling, and Playwright. Required application credentials remain empty and must be supplied by the consumer, normally through Ansible Vault.

### Authentication variables

Dashboard authentication is application-owned:

```yaml
hermes_dashboard_auth_username: "{{ vault_hermes_dashboard_username }}"
hermes_dashboard_auth_password_hash: "{{ vault_hermes_dashboard_password_hash }}"
# Or use hermes_dashboard_auth_password as a protected plaintext fallback.
```

WebUI authentication is application-owned:

```yaml
hermes_webui_password: "{{ vault_hermes_webui_password }}"
```

The role must fail fast when an enabled dashboard lacks a username plus password/hash, or when an enabled WebUI lacks its password. nginx must not use Basic Auth or `.htpasswd` files for these applications.

### Controller-side bootstrap

Bootstrap is implemented in `tasks/rhelAll-10/22_bootstrap.yml`, after the Hermes/WebUI directories are created by phase 20 and before the optional Ansible runtime in phase 25. It uses only `ansible.builtin.assert`, `ansible.builtin.stat`, and `ansible.builtin.copy`; `meta/main.yml` intentionally remains `dependencies: []`, and the repository has no `requirements.yml` or `galaxy.yml` dependency file.

The controller source is selected with:

```yaml
hermes_bootstrap_dir: "{{ playbook_dir }}/files/hermes-bootstrap"
hermes_bootstrap_mode: missing       # disabled, missing, or overwrite
hermes_bootstrap_include_auth: false
```

Supported entries are `SOUL.md`, `config.yaml`, `.env`, `memories/`, `skills/`, `plugins/`, `cron/`, and `workspace/`. `missing` preserves existing target content; `overwrite` replaces matching content; `disabled` is the safe default. `auth.json` is excluded unless the explicit opt-in is enabled, and credential-bearing copy tasks use `no_log: true`. Bootstrap changes notify the gateway, dashboard, and WebUI handlers; each user-service handler first checks that its unit exists.

For bootstrap changes, verify source validation, both copy modes, excluded auth, ownership and modes, service behavior, and a second run. Keep the source outside the repository when it contains private state. The flowchart in `docs/install-flowchart.md` and the detailed role documentation in `README.md` and `docs/manual-setup-rocky10.md` must remain synchronized with this task order.

### Network contract

- nginx HTTPS is public on `443/tcp`.
- When `hermes_nginx_http_enabled: true`, `80/tcp` is also opened automatically.
- Port 80 serves the ACME HTTP-01 webroot and redirects every other request to HTTPS.
- Dashboard and WebUI backend ports must remain internal and must not be opened in firewalld.
- The dashboard and WebUI use separate DNS names because their routes and WebSocket/API paths are root-relative.

## Required setup-combination test protocol

Every change that can affect defaults, enablement conditions, credentials, services, nginx, firewall behavior, package installation, templates, or task ordering must test all five supported setup combinations below. Do not test only the all-enabled default.

Use a fresh disposable target for each combination when practical. If the same target is reused, explicitly reset the previous component state and record that reset. Use Vault or an external secret mechanism for credentials; never put real values in the playbook committed to the repository.

### Combination matrix

| ID | Setup | Gateway | Dashboard | WebUI | nginx/public UI | Required application auth |
|---|---|---:|---:|---:|---:|---|
| A | Agent only | enabled | disabled | disabled | disabled | none for dashboard/WebUI |
| B | Agent + dashboard | enabled | enabled | disabled | enabled | dashboard username + password/hash |
| C | Agent + WebUI | enabled | disabled | enabled | enabled | WebUI password |
| D | Agent + dashboard + WebUI | enabled | enabled | enabled | enabled | dashboard username + password/hash and WebUI password |
| E | Auth protection and boundary checks | enabled | enabled and/or WebUI enabled | test the enabled UI(s) | enabled | negative and positive checks for every enabled UI |

The fifth row is a cross-cutting security protocol, not a different service topology. It must be executed for every enabled browser interface in B, C, and D. A should confirm that no browser interface or public nginx endpoint is accidentally enabled.

### A — Agent only

Example intent:

```yaml
hermes_gateway_enabled: true
hermes_dashboard_enabled: false
hermes_webui_enabled: false
hermes_nginx_enabled: false
hermes_playwright_enabled: false  # unless browser support is deliberately being tested
```

Verify:

- the Hermes user and CLI are installed;
- `hermes-gateway.service` is enabled/running as configured;
- no dashboard or WebUI unit is installed or active;
- nginx is not installed/enabled by this role and no role-managed public UI ports are opened;
- the second Ansible run is convergent.

### B — Agent + dashboard

Example intent:

```yaml
hermes_gateway_enabled: true
hermes_dashboard_enabled: true
hermes_webui_enabled: false
hermes_nginx_enabled: true
hermes_dashboard_auth_username: "{{ vault_hermes_dashboard_username }}"
hermes_dashboard_auth_password_hash: "{{ vault_hermes_dashboard_password_hash }}"
hermes_dashboard_nginx_fqdn: dashboard.example.com
```

Verify:

- gateway and dashboard services are active;
- the local dashboard endpoint is reachable on its configured internal port;
- nginx renders only the dashboard vhost;
- HTTPS works on the dashboard hostname;
- HTTP port 80 either provides the ACME challenge and redirects `/`, or is disabled when that policy is explicitly selected;
- the dashboard backend port is not exposed through firewalld;
- invalid dashboard credentials are rejected with the application response, normally `401`;
- valid credentials establish the expected authenticated session;
- nginx config contains no `auth_basic` or `auth_basic_user_file`;
- the second Ansible run reports no persistent changes.

### C — Agent + WebUI

Example intent:

```yaml
hermes_gateway_enabled: true
hermes_dashboard_enabled: false
hermes_webui_enabled: true
hermes_nginx_enabled: true
hermes_webui_password: "{{ vault_hermes_webui_password }}"
hermes_dashboard_nginx_fqdn: unused-dashboard.example.com
hermes_webui_nginx_fqdn: webui.example.com
```

The role currently validates a dashboard FQDN whenever nginx is enabled, even when the dashboard service is disabled; provide a non-public placeholder or an explicit consumer override as required by the current task contract and verify the rendered result.

Verify:

- gateway and WebUI services are active;
- the local WebUI health endpoint is reachable on its configured internal port;
- nginx renders the WebUI vhost and does not proxy the disabled dashboard;
- HTTPS, HTTP redirect, and ACME behavior work for the WebUI hostname;
- invalid WebUI credentials are rejected;
- valid WebUI credentials reach the authenticated application session;
- the WebUI backend port is not exposed through firewalld;
- nginx contains no Basic Auth directives;
- the second Ansible run is idempotent.

### D — Agent + dashboard + WebUI

Example intent:

```yaml
hermes_gateway_enabled: true
hermes_dashboard_enabled: true
hermes_webui_enabled: true
hermes_nginx_enabled: true
hermes_dashboard_auth_username: "{{ vault_hermes_dashboard_username }}"
hermes_dashboard_auth_password_hash: "{{ vault_hermes_dashboard_password_hash }}"
hermes_webui_password: "{{ vault_hermes_webui_password }}"
hermes_dashboard_nginx_fqdn: dashboard.example.com
hermes_webui_nginx_fqdn: webui.example.com
```

Verify the complete combined deployment:

- all three user services are active;
- both vhosts render and route to the correct distinct backend;
- both public HTTPS hostnames work independently;
- port 80 serves ACME and redirects normal requests for both names;
- dashboard and WebUI authentication are tested independently with wrong and correct credentials;
- cookies/session state for one application cannot be mistaken for authentication to the other;
- both backend ports remain internal;
- certificate SANs cover every enabled public hostname when using the combined Let's Encrypt mode;
- a second role run is idempotent.

### E — Authentication protection protocol

Run this protocol for every enabled browser interface, for both the direct application endpoint where safe and the public nginx endpoint:

1. Confirm the service is active and the local health endpoint responds.
2. Send a request without credentials and record the status and redirect/JSON behavior.
3. Send a request with deliberately invalid credentials and confirm rejection, normally `401`.
4. Send a request with valid credentials and confirm the expected `200`/session result.
5. Confirm the response is application-owned, not nginx Basic Auth: inspect `WWW-Authenticate`, response shape, cookies, and rendered nginx directives.
6. Confirm `/etc/nginx/.htpasswd*` files are absent and backend ports are not open in firewalld.
7. Test a normal browser GET; do not rely only on `HEAD`, because the WebUI may not implement `HEAD /`.
8. Remove temporary cookies, response bodies, and credential-bearing files after the test.
9. Never include passwords, hashes, cookies, or authorization headers in reports, diffs, logs, or PR descriptions.

For public HTTPS checks, use the real hostname or a controlled `--resolve` mapping so cookie-domain behavior matches production. A manually supplied `Host:` header with a different URL can produce misleading cookie results.

## Change-specific test selection

Use this minimum decision rule after changes:

- Defaults, credential asserts, service conditions, or nginx conditions: run all A–E.
- Dashboard-only code/templates: run A, B, D, and E.
- WebUI-only code/templates: run A, C, D, and E.
- Shared package, user, systemd, firewall, or dispatcher code: run all A–E.
- Ansible addon changes: run the normal matrix with the addon disabled and a dedicated enabled-path converge, then verify the active `current/bin/ansible` executable.
- Playwright/Node changes: run the normal matrix with Playwright disabled where browser support is not under test, plus a dedicated enabled-path converge that executes npm, browser installation, `ldd`, and the Chromium smoke test.

If a requested combination cannot be executed because a lab target, DNS record, certificate, or credential is unavailable, report it as **not tested**. Do not substitute a syntax check or a local render for the missing real scenario.

## Definition of done

Before committing or opening a PR:

1. The changed task path was executed, not only parsed.
2. All required setup combinations and the authentication protocol were completed or explicitly marked not tested.
3. The second real run was reviewed for idempotency.
4. Services, local endpoints, public proxy behavior, firewall ports, and rendered configuration were checked.
5. Static tests, Ansible syntax/render tests, `git diff --check`, and a secret/internal-value scan passed.
6. Documentation, examples, tests, and `CHANGELOG.md` describe the new behavior.
7. Generated artifacts such as `__pycache__/` are removed.
8. The PR head SHA is verified on GitHub after pushing.

A green static test suite alone is not evidence that an enabled deployment works.
