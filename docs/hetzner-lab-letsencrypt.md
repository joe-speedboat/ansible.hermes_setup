# Hetzner Lab with LuaDNS and Let's Encrypt

This checklist documents the real-lab path for deploying `joe-speedboat.hermes_setup` on a disposable Hetzner Cloud Rocky Linux 10 VM with public nginx vhosts, LuaDNS records, Basic Auth, and Let's Encrypt certificates.

Use example hostnames in public documentation. Replace them with the real lab names only in private inventory or vault files.

## Target shape

Example deployment:

```text
dashboard.example.com -> Hetzner VM public IP
webui.example.com     -> Hetzner VM public IP
```

Role variables:

```yaml
hermes_webui_enabled: true
ansible_enable: true

hermes_nginx_enabled: true
hermes_nginx_letsencrypt_enabled: true
hermes_nginx_letsencrypt_email: hermes@webui.example.com

hermes_dashboard_nginx_fqdn: dashboard.example.com
hermes_webui_nginx_fqdn: webui.example.com

hermes_dashboard_nginx_basic_auth_enabled: true
hermes_dashboard_nginx_basic_auth_user: hermes
hermes_dashboard_nginx_basic_auth_password: "{{ vault_hermes_basic_auth_password }}"
hermes_webui_nginx_basic_auth_enabled: true
hermes_webui_nginx_basic_auth_user: hermes
hermes_webui_nginx_basic_auth_password: "{{ vault_hermes_basic_auth_password }}"
```

## Ordering that matters

1. Create the temporary Hetzner VM and record its public IPv4/IPv6 address.
2. Create or update DNS records for every public nginx vhost before running the role with Let's Encrypt enabled.
3. Verify public DNS resolution from public resolvers.
4. Run the Ansible playbook.
5. Verify nginx, Certbot, services, public HTTPS, Basic Auth, and idempotency.

Do not run Certbot before DNS points at the VM. HTTP-01 validation must reach the nginx ACME webroot on port `80/tcp`.

## DNS checks

For LuaDNS-backed labs, list existing records before changes, then upsert the records to the VM IP.

Generic verification:

```bash
dig +short dashboard.example.com A @1.1.1.1
dig +short dashboard.example.com A @8.8.8.8
dig +short webui.example.com A @1.1.1.1
dig +short webui.example.com A @8.8.8.8
```

Expected output is the VM public address for both names.

If recursive DNS is briefly inconsistent immediately after record creation, verify authoritative/API state first and retry public resolvers. For browser or HTTPS smoke tests during propagation, `curl --resolve <name>:443:<ip>` can prove the VM-side nginx and certificate behavior independently of the local resolver cache.

## Playbook prechecks

Use a harness directory outside the role checkout and set `ANSIBLE_ROLES_PATH` to a local `roles/` directory containing a Galaxy-style symlink:

```bash
mkdir -p lab-harness/roles
ln -sfn /path/to/ansible.hermes_setup lab-harness/roles/joe-speedboat.hermes_setup
```

Run basic connectivity and syntax checks before the full converge:

```bash
ANSIBLE_HOST_KEY_CHECKING=False ansible -i inventory.ini hermes_lab -m raw -a 'python3 --version; cat /etc/os-release | grep PRETTY_NAME'
ANSIBLE_HOST_KEY_CHECKING=False ansible -i inventory.ini hermes_lab -m ping
ANSIBLE_ROLES_PATH=roles ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i inventory.ini test.yml --syntax-check
```

If the controller has broken global SSH includes, isolate the lab with a clean SSH config and reference it from inventory:

```ini
[hermes_lab]
hermes-rocky10 ansible_host=192.0.2.10 ansible_user=root ansible_ssh_common_args='-F /absolute/path/to/lab/ssh_config'
```

## Expected role behavior

With `hermes_nginx_letsencrypt_enabled: true`, the role:

- installs `nginx`, `firewalld`, `certbot`, and SELinux proxy prerequisites;
- renders bootstrap vhosts with self-signed certificates so nginx can start before ACME succeeds;
- serves `/.well-known/acme-challenge/` on port 80 without Basic Auth;
- reloads nginx before Certbot so the challenge location is active;
- requests one combined Let's Encrypt certificate named after `hermes_dashboard_nginx_fqdn`;
- includes `hermes_webui_nginx_fqdn` as a second SAN when `hermes_webui_enabled: true`;
- re-renders both dashboard and WebUI vhosts to use the combined live certificate;
- installs a deploy hook that reloads nginx after renewals;
- enables `certbot-renew.timer` when available.

Both vhosts use the same live certificate paths after issuance:

```text
/etc/letsencrypt/live/<dashboard-fqdn>/fullchain.pem
/etc/letsencrypt/live/<dashboard-fqdn>/privkey.pem
```

## Post-run verification

Run these checks on the VM:

```bash
systemctl is-active nginx firewalld certbot-renew.timer
sudo -iu hermes systemctl --user is-active hermes-gateway.service hermes-dashboard.service hermes-webui.service
nginx -t
certbot certificates
openssl x509 -in /etc/letsencrypt/live/dashboard.example.com/fullchain.pem -noout -issuer -subject -ext subjectAltName
curl -fsS http://127.0.0.1:8080/ >/dev/null
curl -fsS http://127.0.0.1:8787/health >/dev/null
```

Expected service state:

```text
nginx: active
firewalld: active
certbot-renew.timer: active
hermes-gateway.service: active
hermes-dashboard.service: active
hermes-webui.service: active
```

Expected certificate SANs:

```text
DNS:dashboard.example.com, DNS:webui.example.com
```

## Public HTTPS and Basic Auth checks

From outside the VM:

```bash
curl -sS -o /dev/null -w '%{http_code} %{ssl_verify_result}\n' https://dashboard.example.com/
curl -sS -o /dev/null -w '%{http_code} %{ssl_verify_result}\n' -u hermes:"${HERMES_BASIC_AUTH_PASSWORD}" https://dashboard.example.com/
curl -sS -o /dev/null -w '%{http_code} %{ssl_verify_result}\n' https://webui.example.com/
curl -sS -o /dev/null -w '%{http_code} %{ssl_verify_result}\n' -u hermes:"${HERMES_BASIC_AUTH_PASSWORD}" https://webui.example.com/
```

Expected behavior:

```text
without Basic Auth: HTTP 401
with Basic Auth:    HTTP 200
ssl_verify_result:  0
```

Use a normal GET for WebUI. Some WebUI routes may not implement `HEAD`, so `curl -I` is not a complete health check for that vhost.

## Idempotency expectation

After the first converge and any one-time service restarts settle, run the playbook again:

```bash
ANSIBLE_ROLES_PATH=roles ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i inventory.ini test.yml
```

The final steady-state run should end with:

```text
changed=0 failed=0
```

A first immediate re-run can still show transient changes if an upstream Git checkout or service unit was updated during the initial converge. Run a final pass before claiming idempotency.

## Cleanup

For disposable Hetzner labs, keep resources labelled at creation time and delete them after validation unless the VM is intentionally being handed over for further work. DNS records should be removed or updated when the VM is destroyed so stale hostnames do not point at recycled addresses.
