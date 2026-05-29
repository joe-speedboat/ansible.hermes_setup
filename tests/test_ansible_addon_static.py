from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ansible_addon_is_opt_in_and_runs_as_hermes_user():
    defaults = (ROOT / "defaults/main.yml").read_text()
    tasks = (ROOT / "tasks/rhelAll-10/25_ansible.yml").read_text()
    readme = (ROOT / "README.md").read_text()

    assert "ansible_enable: false" in defaults
    assert "ansible_install_url: https://ansible-uv.bitbull.ch" in defaults
    assert 'ansible_home: "{{ hermes_home }}/ansible"' in defaults

    assert "runuser -u {{ hermes_user }}" in tasks
    assert "HOME={{ hermes_home | quote }}" in tasks
    assert "SCOPE=user" in tasks
    assert "ANSIBLE_HOME={{ ansible_home | quote }}" in tasks
    assert "{{ ansible_install_url | quote }}" in tasks
    assert "when: ansible_enable | bool" in tasks
    assert "{{ ansible_home }}/apps/profile.d/ansible.sh" in tasks
    assert "ansible --version" in tasks

    assert "`ansible_enable`: install a user-scope Ansible runtime" in readme
    assert "sudo -iu hermes ansible --version" in readme
