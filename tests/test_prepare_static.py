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
    assert 'hermes_dashboard_nginx_fqdn: "dash-{{ ansible_fqdn | default(inventory_hostname) }}"' in defaults
    assert 'hermes_webui_nginx_fqdn: "web-{{ hermes_dashboard_nginx_fqdn }}"' in defaults
    assert "{{ hermes_dashboard_nginx_fqdn }}_tls.crt" in defaults
    assert "{{ hermes_dashboard_nginx_fqdn }}_tls.key" in defaults
    assert "hermes_dashboard_auth_username:" in defaults
    assert "hermes_dashboard_auth_password_hash:" in defaults
    assert "hermes_webui_password:" in defaults
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
    assert "hermes_playwright_build_tools_enabled: true" in defaults


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
