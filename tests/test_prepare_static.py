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
    assert "/etc/nginx/.htpasswd-hermes-{{ hermes_dashboard_nginx_fqdn }}" in defaults
    assert 'hermes_dashboard_nginx_basic_auth_realm: "{{ hermes_dashboard_nginx_fqdn }}"' in defaults
    assert 'hermes_webui_nginx_basic_auth_enabled: "{{ hermes_dashboard_nginx_basic_auth_enabled }}"' in defaults
    assert 'hermes_webui_nginx_basic_auth_password: "{{ hermes_dashboard_nginx_basic_auth_password }}"' in defaults

    epel_task_index = prepare_tasks.index("Install repository packages before Hermes packages")
    base_task_index = prepare_tasks.index("Install Hermes base packages")
    assert epel_task_index < base_task_index
    assert 'name: "{{ hermes_repo_packages }}"' in prepare_tasks
    assert "when: hermes_repo_packages | length > 0" in prepare_tasks
    assert 'name: "{{ hermes_base_packages }}"' in prepare_tasks
