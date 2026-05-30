# Changelog

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
