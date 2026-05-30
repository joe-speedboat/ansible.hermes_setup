from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_epel_is_installed_before_base_packages_and_ripgrep_is_included():
    defaults = (ROOT / "defaults/main.yml").read_text()
    prepare_tasks = (ROOT / "tasks/rhelAll-10/10_prepare.yml").read_text()

    assert "hermes_epel_enabled: true" in defaults
    assert "hermes_epel_release_package: epel-release" in defaults
    assert "  - ripgrep" in defaults

    epel_task_index = prepare_tasks.index("Install EPEL repository before Hermes packages")
    base_task_index = prepare_tasks.index("Install Hermes base packages")
    assert epel_task_index < base_task_index
    assert 'name: "{{ hermes_epel_release_package }}"' in prepare_tasks
    assert "when: hermes_epel_enabled | bool" in prepare_tasks
    assert 'name: "{{ hermes_base_packages }}"' in prepare_tasks
