from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_repo_packages_are_installed_before_base_packages_and_hermes_cli_tools_are_included():
    defaults = (ROOT / "defaults/main.yml").read_text()
    prepare_tasks = (ROOT / "tasks/rhelAll-10/10_prepare.yml").read_text()

    assert "hermes_repo_packages:" in defaults
    assert "  - epel-release" in defaults
    assert "  - ffmpeg-free" in defaults
    assert "  - git" in defaults
    assert "  - gh" in defaults
    assert "  - ripgrep" in defaults
    assert 'hermes_dashboard_nginx_fqdn: "adm-{{ ansible_fqdn | default(inventory_hostname) }}"' in defaults
    assert 'hermes_webui_nginx_fqdn: "{{ ansible_fqdn | default(inventory_hostname) }}"' in defaults
    assert "{{ hermes_dashboard_nginx_fqdn }}_tls.crt" in defaults
    assert "{{ hermes_dashboard_nginx_fqdn }}_tls.key" in defaults
    assert "hermes_dashboard_auth_username:" in defaults
    assert "hermes_dashboard_auth_password_hash:" in defaults
    assert "hermes_webui_enabled: true" in defaults
    assert "hermes_webui_password:" in defaults
    assert "hermes_webui_max_upload_mb: 220" in defaults
    assert 'hermes_nginx_client_max_body_size: "{{ hermes_webui_max_upload_mb }}m"' in defaults
    assert "HERMES_WEBUI_MAX_UPLOAD_MB={{ hermes_webui_max_upload_mb }}" in (ROOT / "templates/hermes-webui.env.j2").read_text()
    assert "hermes_bootstrap_dir: \"\"" in defaults
    assert "hermes_bootstrap_mode: disabled" in defaults
    assert "hermes_bootstrap_include_auth: false" in defaults
    assert "auth.json" not in defaults.split("hermes_bootstrap_items:", 1)[1]
    assert "hermes_ssh_setup: true" in defaults
    assert "hermes_ssh_generate_key: \"{{ hermes_ssh_setup }}\"" in defaults
    assert "hermes_ssh_key_type: ed25519" in defaults
    assert 'hermes_ssh_key_path: "{{ hermes_home }}/.ssh/id_ed25519"' in defaults
    assert "hermes_ssh_packages:" in defaults
    assert "  - openssh-clients" in defaults
    assert "hermes_dashboard_nginx_basic_auth" not in defaults
    assert "hermes_webui_nginx_basic_auth" not in defaults

    epel_task_index = prepare_tasks.index("Install repository packages before Hermes packages")
    base_task_index = prepare_tasks.index("Install Hermes base packages")
    runtime_task_index = prepare_tasks.index("Install Playwright runtime packages when enabled")
    build_tools_task_index = prepare_tasks.index("Install npm native build tools when explicitly enabled")
    user_task_index = prepare_tasks.index("Create dedicated Hermes user without sudo rights")

    assert epel_task_index < base_task_index
    assert base_task_index < runtime_task_index
    assert runtime_task_index < build_tools_task_index
    assert build_tools_task_index < user_task_index
    assert 'name: "{{ hermes_repo_packages }}"' in prepare_tasks
    assert "when: hermes_repo_packages | length > 0" in prepare_tasks
    assert 'name: "{{ hermes_base_packages }}"' in prepare_tasks
    assert 'name: "{{ hermes_playwright_build_tools_packages }}"' in prepare_tasks
    assert "hermes_playwright_build_tools_enabled | bool" in prepare_tasks
    assert "hermes_node_packages:" in defaults
    assert "  - nodejs-libs" in defaults
    assert "  - c-ares" in defaults
    assert "Synchronize Node.js runtime packages before Hermes packages" in prepare_tasks
    assert "state: latest" in prepare_tasks
    assert "Validate Node.js and npm runtime before Playwright installation" in (ROOT / "tasks/rhelAll-10/40_playwright.yml").read_text()


def test_bootstrap_task_supports_safe_modes_and_optional_auth():
    bootstrap_tasks = (ROOT / "tasks/rhelAll-10/22_bootstrap.yml").read_text()

    assert "hermes_bootstrap_mode in ['disabled', 'missing', 'overwrite']" in bootstrap_tasks
    assert "force: \"{{ hermes_bootstrap_mode == 'overwrite' }}\"" in bootstrap_tasks
    assert "hermes_bootstrap_include_auth | bool" in bootstrap_tasks
    assert "dest: \"{{ hermes_config_dir }}/auth.json\"" in bootstrap_tasks
    assert "no_log: true" in bootstrap_tasks
    handlers = (ROOT / "handlers/main.yml").read_text()
    assert "- name: restart Hermes gateway" in handlers
    assert "systemctl --user restart hermes-gateway.service" in handlers
    assert "restart Hermes dashboard" in bootstrap_tasks
    assert "restart Hermes WebUI" in bootstrap_tasks


def test_ssh_setup_is_persistent_and_does_not_overwrite_keys():
    defaults = (ROOT / "defaults/main.yml").read_text()
    ssh_tasks = (ROOT / "tasks/rhelAll-10/21_ssh.yml").read_text()

    assert "hermes_ssh_setup: true" in defaults
    assert "hermes_ssh_key_type in ['ed25519', 'rsa', 'ecdsa']" in ssh_tasks
    assert "hermes_ssh_key_path.startswith(hermes_home + '/.ssh/')" in ssh_tasks
    assert "state: touch" in ssh_tasks
    assert "mode: '0700'" in ssh_tasks
    assert "mode: '0644'" in ssh_tasks
    assert "ssh-keygen" in ssh_tasks
    assert "creates: \"{{ hermes_ssh_key_path }}\"" in ssh_tasks
    assert "not hermes_ssh_private_key_stat.stat.exists" in ssh_tasks
    prepare_tasks = (ROOT / "tasks/rhelAll-10/10_prepare.yml").read_text()
    assert "Install Hermes SSH client packages when enabled" in prepare_tasks
    assert "hermes_ssh_setup | bool" in prepare_tasks


def test_nginx_firewall_management_installs_and_starts_firewalld():
    nginx_tasks = (ROOT / "tasks/rhelAll-10/35_nginx.yml").read_text()

    package_task_index = nginx_tasks.index("Install nginx for Hermes reverse proxy")
    firewalld_package_index = nginx_tasks.index("'firewalld'")
    start_task_index = nginx_tasks.index("Enable and start firewalld for Hermes nginx firewall management")
    firewall_cmd_index = nginx_tasks.index("Remove legacy http/https firewalld services for Hermes nginx")

    assert package_task_index < firewalld_package_index < start_task_index < firewall_cmd_index
    assert "name: firewalld" in nginx_tasks
    assert "enabled: true" in nginx_tasks
    assert "state: started" in nginx_tasks
    assert "hermes_nginx_enable_firewall | bool" in nginx_tasks


def test_http_redirect_and_webroot_acme_are_the_defaults():
    defaults = (ROOT / "defaults/main.yml").read_text()
    nginx_tasks = (ROOT / "tasks/rhelAll-10/35_nginx.yml").read_text()
    nginx_template = (ROOT / "templates/nginx-hermes.conf.j2").read_text()

    assert "hermes_nginx_http_enabled: true" in defaults
    assert "hermes_nginx_letsencrypt_challenge_method: webroot" in defaults
    assert "hermes_nginx_http_enabled | bool" in nginx_template
    assert "hermes_nginx_letsencrypt_challenge_method == 'webroot'" in nginx_tasks
    assert "((hermes_nginx_http_enabled | bool) | ternary(['80/tcp'], []))" in nginx_tasks


def test_application_authentication_fails_without_required_credentials():
    configure_tasks = (ROOT / "tasks/rhelAll-10/20_install_configure.yml").read_text()

    dashboard_validation = configure_tasks.split(
        "- name: Read current Hermes dashboard application authentication settings", 1
    )[0]
    webui_validation = configure_tasks.split(
        "- name: Validate Hermes WebUI application authentication settings", 1
    )[1].split("- name: Read current Hermes dashboard application authentication settings", 1)[0]

    assert "- hermes_dashboard_enabled | bool" in dashboard_validation
    assert "- hermes_dashboard_auth_username | length > 0" in dashboard_validation
    assert "hermes_dashboard_auth_password_hash | length > 0" in dashboard_validation
    assert "hermes_dashboard_auth_password | length > 0" in dashboard_validation
    assert "when: hermes_webui_enabled | bool" in webui_validation
    assert "- hermes_webui_password | length > 0" in webui_validation
