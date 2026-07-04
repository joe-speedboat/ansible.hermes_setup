# Manual Hermes Setup on Rocky Linux 10

This document shows the manual equivalent of the `joe-speedboat.hermes_setup` role. It is useful for audits, troubleshooting, and understanding exactly what the role automates.

## 1. Update Rocky Linux 10

Run as an existing admin/root user:

```bash
sudo dnf update -y
sudo reboot
```

Verify the OS:

```bash
cat /etc/os-release
```

Expected: Rocky Linux 10.x.

## 2. Install Base Packages

Enable EPEL first because some Hermes helper packages, such as `ffmpeg-free` and `ripgrep`, are resolved from the extended package set on Rocky/RHEL 10:

```bash
sudo dnf install -y epel-release
sudo dnf install -y \
  bash \
  ca-certificates \
  curl \
  git \
  gh \
  ffmpeg-free \
  jq \
  openssl \
  python3 \
  python3-pip \
  ripgrep \
  tar \
  unzip \
  which \
  nodejs \
  npm
```

## 3. Create the `hermes` User Without Sudo Rights

```bash
sudo useradd --create-home --shell /bin/bash hermes
sudo passwd hermes
```

Make sure the user is not in `wheel`:

```bash
id hermes
sudo gpasswd -d hermes wheel || true
```

Enable linger so systemd user services can run after logout:

```bash
sudo loginctl enable-linger hermes
sudo systemctl start user@$(id -u hermes).service
```

Ensure shell sessions for the lingered user know how to reach the systemd user bus:

```bash
sudo tee -a /home/hermes/.bashrc >/dev/null <<'EOF'

# systemd --user / D-Bus session for lingered user services
export XDG_RUNTIME_DIR="/run/user/$UID"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
EOF
sudo chown hermes:hermes /home/hermes/.bashrc
```

## 4. Install Hermes Agent

Switch to the dedicated user:

```bash
sudo -iu hermes
```

Install Hermes with the official installer:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- --skip-setup --skip-browser
```

Verify:

```bash
~/.local/bin/hermes --version
~/.local/bin/hermes doctor
```

## 5. Configure Codex Defaults

The role can set non-secret Codex defaults when `configure_codex: true`:

```bash
sudo -iu hermes hermes config set model.provider openai-codex
sudo -iu hermes hermes config set model.default gpt-5.5
```

Authentication remains manual:

```bash
sudo -iu hermes hermes auth add openai-codex
```

Alternative:

```bash
sudo -iu hermes hermes model
```

## 6. Gateway systemd User Service

The Ansible role installs and enables this service by default:

```yaml
hermes_gateway_enabled: true
hermes_gateway_service_enabled: true
hermes_gateway_service_state: started
```

Run `hermes gateway setup` first if you want a configured platform such as Telegram, Discord, Slack, or Matrix.

Create the user service directory:

```bash
sudo install -d -o hermes -g hermes -m 0755 /home/hermes/.config/systemd/user
```

Do not use `sudo -iu hermes mkdir -p ~/.config/systemd/user` from a root/admin shell: many shells expand `~` before `sudo` runs, which tries to create `/root/.config/...` as the unprivileged `hermes` user.

Create `/home/hermes/.config/systemd/user/hermes-gateway.service`:

```ini
[Unit]
Description=Hermes Agent Gateway
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart=/home/hermes/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace
WorkingDirectory=/home/hermes/.hermes/hermes-agent
Environment="PATH=/home/hermes/.hermes/hermes-agent/venv/bin:/home/hermes/.hermes/hermes-agent/node_modules/.bin:/home/hermes/.hermes/node/bin:/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=/home/hermes/.hermes/hermes-agent/venv"
Environment="HERMES_HOME=/home/hermes/.hermes"
Restart=always
RestartSec=5
RestartMaxDelaySec=300
RestartSteps=5
RestartForceExitStatus=75
KillMode=mixed
KillSignal=SIGTERM
ExecReload=/bin/kill -USR1 $MAINPID
TimeoutStopSec=210
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hermes-gateway

[Install]
WantedBy=default.target
```

Reload and start:

```bash
uid=$(id -u hermes)
sudo runuser -u hermes -- env \
  XDG_RUNTIME_DIR=/run/user/$uid \
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$uid/bus \
  systemctl --user daemon-reload

sudo runuser -u hermes -- env \
  XDG_RUNTIME_DIR=/run/user/$uid \
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$uid/bus \
  systemctl --user enable --now hermes-gateway.service
```

Verify:

```bash
sudo runuser -u hermes -- env \
  XDG_RUNTIME_DIR=/run/user/$(id -u hermes) \
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u hermes)/bus \
  systemctl --user status hermes-gateway.service --no-pager

sudo runuser -u hermes -- env \
  XDG_RUNTIME_DIR=/run/user/$(id -u hermes) \
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u hermes)/bus \
  systemctl --user is-enabled hermes-gateway.service
```

## 7. Dashboard systemd User Service

The Ansible role installs and enables this service by default:

```yaml
hermes_dashboard_enabled: true
hermes_dashboard_service_enabled: true
hermes_dashboard_service_state: started
```

Create the user service directory:

```bash
sudo install -d -o hermes -g hermes -m 0755 /home/hermes/.config/systemd/user
```

Create `/home/hermes/.config/systemd/user/hermes-dashboard.service`:

```ini
[Unit]
Description=Hermes Agent Dashboard
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart=/home/hermes/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main dashboard --port 8080 --host 127.0.0.1
WorkingDirectory=/home/hermes/.hermes/hermes-agent
Environment="PATH=/home/hermes/.hermes/hermes-agent/venv/bin:/home/hermes/.hermes/hermes-agent/node_modules/.bin:/home/hermes/.hermes/node/bin:/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=/home/hermes/.hermes/hermes-agent/venv"
Environment="HERMES_HOME=/home/hermes/.hermes"
Restart=always
RestartSec=5
RestartMaxDelaySec=300
RestartSteps=5
RestartForceExitStatus=75
KillMode=mixed
KillSignal=SIGTERM
ExecReload=/bin/kill -USR1 $MAINPID
TimeoutStopSec=210
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hermes-dashboard

[Install]
WantedBy=default.target
```

Reload and start:

```bash
uid=$(id -u hermes)
sudo runuser -u hermes -- env \
  XDG_RUNTIME_DIR=/run/user/$uid \
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$uid/bus \
  systemctl --user daemon-reload

sudo runuser -u hermes -- env \
  XDG_RUNTIME_DIR=/run/user/$uid \
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$uid/bus \
  systemctl --user enable --now hermes-dashboard.service
```

Verify:

```bash
sudo runuser -u hermes -- env \
  XDG_RUNTIME_DIR=/run/user/$(id -u hermes) \
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u hermes)/bus \
  systemctl --user status hermes-dashboard.service --no-pager

sudo runuser -u hermes -- env \
  XDG_RUNTIME_DIR=/run/user/$(id -u hermes) \
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u hermes)/bus \
  systemctl --user is-enabled hermes-dashboard.service

for i in {1..30}; do
  curl -fsS http://127.0.0.1:8080 >/dev/null && break
  sleep 2
done
curl -fsS http://127.0.0.1:8080 >/dev/null
```

The dashboard listens on loopback only. Do **not** open `8080/tcp` in firewalld for browser access. Use SSH tunnelling or the nginx reverse proxy pattern below.

## 8. Optional Hermes WebUI systemd User Service

The Ansible role can install and enable the separate Hermes WebUI service when requested:

```yaml
hermes_webui_enabled: true
hermes_webui_service_enabled: true
hermes_webui_service_state: started
hermes_webui_repo_url: https://github.com/nesquena/hermes-webui.git
hermes_webui_repo_version: master
hermes_webui_app_dir: /home/hermes/app/hermes-webui
hermes_webui_host: 127.0.0.1
hermes_webui_port: 8787
hermes_webui_state_dir: /home/hermes/.hermes/webui
hermes_webui_default_workspace: /home/hermes/work
hermes_webui_allowed_origins: https://web-hermes.example.ch
```

Install the WebUI checkout and local state/workspace directories:

```bash
sudo install -d -o hermes -g hermes -m 0755 /home/hermes/app /home/hermes/.hermes/webui /home/hermes/work
sudo runuser -u hermes -- git clone https://github.com/nesquena/hermes-webui.git /home/hermes/app/hermes-webui
```

Create `/home/hermes/app/hermes-webui/.env`. This file contains local service configuration only; do not put secrets into it:

```bash
sudo tee /home/hermes/app/hermes-webui/.env >/dev/null <<'EOF'
HERMES_HOME=/home/hermes/.hermes
HERMES_WEBUI_AGENT_DIR=/home/hermes/.hermes/hermes-agent
HERMES_WEBUI_PYTHON=/home/hermes/.hermes/hermes-agent/venv/bin/python
HERMES_WEBUI_HOST=127.0.0.1
HERMES_WEBUI_PORT=8787
HERMES_WEBUI_STATE_DIR=/home/hermes/.hermes/webui
HERMES_WEBUI_DEFAULT_WORKSPACE=/home/hermes/work
HERMES_WEBUI_ALLOWED_ORIGINS=https://web-hermes.example.ch
EOF
sudo chown hermes:hermes /home/hermes/app/hermes-webui/.env
sudo chmod 0640 /home/hermes/app/hermes-webui/.env
```

Create `/home/hermes/.config/systemd/user/hermes-webui.service`:

```ini
[Unit]
Description=Hermes WebUI
Documentation=https://github.com/nesquena/hermes-webui/
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
WorkingDirectory=/home/hermes/app/hermes-webui
EnvironmentFile=/home/hermes/app/hermes-webui/.env
Environment=PYTHONUNBUFFERED=1
Environment=HERMES_WEBUI_FOREGROUND=1
ExecStart=/home/hermes/.hermes/hermes-agent/venv/bin/python /home/hermes/app/hermes-webui/bootstrap.py --no-browser --foreground --host 127.0.0.1 8787
Restart=on-failure
RestartSec=5s
TimeoutStopSec=20s
KillSignal=SIGTERM
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hermes-webui

# Keep the WebUI private on loopback; nginx is the public TLS/auth endpoint.
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=full
ProtectHome=read-only
ReadWritePaths=/home/hermes /tmp

[Install]
WantedBy=default.target
```

Reload, start, and verify:

```bash
uid=$(id -u hermes)
sudo runuser -u hermes -- env \
  XDG_RUNTIME_DIR=/run/user/$uid \
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$uid/bus \
  systemctl --user daemon-reload

sudo runuser -u hermes -- env \
  XDG_RUNTIME_DIR=/run/user/$uid \
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$uid/bus \
  systemctl --user enable --now hermes-webui.service

for i in {1..30}; do
  curl -fsS http://127.0.0.1:8787/health >/dev/null && break
  sleep 2
done
curl -fsS http://127.0.0.1:8787/health >/dev/null
```

The WebUI also listens on loopback only. Expose it with its own DNS vhost, for example `web-hermes.example.ch`, instead of sharing the dashboard vhost.

## 9. Optional nginx HTTPS + Basic Auth Reverse Proxy

The Ansible role can enable this automatically with `hermes_nginx_enabled: true`. It renders separate vhosts for the built-in dashboard and, when `hermes_webui_enabled: true`, the WebUI. For public DNS names, set `hermes_nginx_letsencrypt_enabled: true` to have the role request one combined Let's Encrypt certificate for the enabled nginx vhosts. For manual setup, install nginx and keep both browser UIs bound to loopback:

```bash
sudo dnf install -y nginx openssl policycoreutils-python-utils firewalld certbot
sudo mkdir -p /etc/pki/tls/hermes
sudo openssl req -x509 -newkey rsa:4096 -sha256 -days 825 -nodes \
  -keyout /etc/pki/tls/hermes/hermes.example.ch_tls.key \
  -out /etc/pki/tls/hermes/hermes.example.ch_tls.crt \
  -subj '/CN=hermes.example.ch' \
  -addext 'subjectAltName=DNS:hermes.example.ch'
sudo openssl req -x509 -newkey rsa:4096 -sha256 -days 825 -nodes \
  -keyout /etc/pki/tls/hermes/web-hermes.example.ch_tls.key \
  -out /etc/pki/tls/hermes/web-hermes.example.ch_tls.crt \
  -subj '/CN=web-hermes.example.ch' \
  -addext 'subjectAltName=DNS:web-hermes.example.ch'
sudo chmod 0600 /etc/pki/tls/hermes/hermes.example.ch_tls.key /etc/pki/tls/hermes/web-hermes.example.ch_tls.key
```

Create `/etc/nginx/.htpasswd-hermes-hermes.example.ch` with a SHA-512 crypt hash. Use a real password, ideally sourced from a secret manager or Ansible Vault:

```bash
python3 - <<'PY' | sudo tee /etc/nginx/.htpasswd-hermes-hermes.example.ch >/dev/null
import crypt, getpass
user = 'chris'
password = getpass.getpass('Basic Auth password: ')
print(f'{user}:{crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))}')
PY
sudo chown root:nginx /etc/nginx/.htpasswd-hermes-hermes.example.ch
sudo chmod 0640 /etc/nginx/.htpasswd-hermes-hermes.example.ch

python3 - <<'PY' | sudo tee /etc/nginx/.htpasswd-hermes-web-hermes.example.ch >/dev/null
import crypt, getpass
user = 'chris'
password = getpass.getpass('WebUI Basic Auth password: ')
print(f'{user}:{crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))}')
PY
sudo chown root:nginx /etc/nginx/.htpasswd-hermes-web-hermes.example.ch
sudo chmod 0640 /etc/nginx/.htpasswd-hermes-web-hermes.example.ch
```

Create the dashboard vhost `/etc/nginx/conf.d/hermes.example.ch.conf`:

```nginx
server {
    listen 80;
    server_name hermes.example.ch;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name hermes.example.ch;

    ssl_certificate /etc/pki/tls/hermes/hermes.example.ch_tls.crt;
    ssl_certificate_key /etc/pki/tls/hermes/hermes.example.ch_tls.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    client_max_body_size 100m;

    auth_basic "hermes.example.ch";
    auth_basic_user_file /etc/nginx/.htpasswd-hermes-hermes.example.ch;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;

        proxy_set_header Host 127.0.0.1:8080;
        proxy_set_header Origin "";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Authorization "";

        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

Create a separate WebUI vhost `/etc/nginx/conf.d/web-hermes.example.ch.conf` when `hermes_webui_enabled: true`. Use a separate FQDN, certificate/key, and htpasswd file:

```nginx
server {
    listen 80;
    server_name web-hermes.example.ch;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name web-hermes.example.ch;

    ssl_certificate /etc/pki/tls/hermes/web-hermes.example.ch_tls.crt;
    ssl_certificate_key /etc/pki/tls/hermes/web-hermes.example.ch_tls.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    client_max_body_size 100m;

    auth_basic "web-hermes.example.ch";
    auth_basic_user_file /etc/nginx/.htpasswd-hermes-web-hermes.example.ch;

    location / {
        proxy_pass http://127.0.0.1:8787;
        proxy_http_version 1.1;

        proxy_set_header Host web-hermes.example.ch;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

Enable nginx and firewalld, then open HTTPS. Start `firewalld` before running `firewall-cmd`; fresh Rocky 10 minimal cloud images may not include or start it by default.

```bash
sudo setsebool -P httpd_can_network_connect 1
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl enable --now firewalld
sudo firewall-cmd --permanent --remove-service=http || true
sudo firewall-cmd --permanent --remove-service=https || true
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

Verify:

```bash
curl -skI https://hermes.example.ch/ | sed -n '1,8p'
curl -skI -u chris:'<password>' https://hermes.example.ch/ | sed -n '1,8p'
curl -skI https://web-hermes.example.ch/ | sed -n '1,8p'
curl -skI -u chris:'<password>' https://web-hermes.example.ch/ | sed -n '1,8p'
```

For multiple Hermes users, use one DNS vhost per Linux user and browser UI port, for example `chris-hermes.example.ch -> 127.0.0.1:8081` and `dev-hermes.example.ch -> 127.0.0.1:8082`. Keep certificate files, private keys, and htpasswd files scoped by FQDN (as shown above) so one vhost cannot overwrite another. Avoid subfolders because Hermes uses root-relative `/api/...` and WebSocket endpoints.

## 10. Pair Messaging Platforms such as Telegram

To reconfigure missing/basic Hermes settings quickly:

```bash
sudo -iu hermes hermes setup --quick
```

For messaging, the more important step is pairing a messenger. Run the Hermes gateway setup wizard as the `hermes` user:

```bash
sudo -iu hermes hermes gateway setup
```

For Telegram, select Telegram in the wizard and enter the bot token from BotFather. Then restart the already enabled gateway service:

```bash
sudo -iu hermes systemctl --user restart hermes-gateway.service
sudo -iu hermes systemctl --user status hermes-gateway.service --no-pager
```

Restart all enabled role-managed services as the `hermes` user:

```bash
sudo -iu hermes systemctl --user restart hermes-gateway.service
sudo -iu hermes systemctl --user restart hermes-dashboard.service
sudo -iu hermes systemctl --user restart hermes-webui.service
```

When a user sends a message to the bot, Hermes creates a pending pairing code. List and approve it:

```bash
sudo -iu hermes hermes pairing list
sudo -iu hermes hermes pairing approve telegram <CODE>
```

Useful gateway maintenance commands:

```bash
sudo -iu hermes hermes gateway restart
sudo -iu hermes hermes gateway stop
sudo -iu hermes hermes gateway status
```

## 11. Playwright Setup

The Ansible role installs Playwright support by default:

```yaml
hermes_playwright_enabled: true
hermes_playwright_browsers:
  - chromium
hermes_playwright_ldd_check_enabled: true
hermes_playwright_smoke_test_enabled: true
```

Disable it only when the server must not download browser binaries or will never use Hermes browser automation:

```yaml
hermes_playwright_enabled: false
```

Install npm native build tools before Playwright/npm work. The role enables this by default because fresh Rocky 10 minimal hosts may need to compile native modules such as `node-pty` with `node-gyp`:

```bash
sudo dnf install -y make gcc gcc-c++
```

Install runtime libraries as admin/root:

```bash
sudo dnf install -y \
  liberation-fonts dejavu-sans-fonts pulseaudio-libs libxshmfence \
  nspr nss nss-util \
  atk at-spi2-atk at-spi2-core \
  libX11 libXcomposite libXdamage libXext libXfixes libXrandr \
  libxcb libxkbcommon \
  cups-libs \
  mesa-libgbm libdrm \
  alsa-lib \
  pango cairo gdk-pixbuf2 gtk3
```

Install Playwright package and Chromium browser as user `hermes`:

```bash
sudo -iu hermes bash -lc 'cd ~/.hermes/hermes-agent && npm install --no-save playwright'
sudo -iu hermes bash -lc 'cd ~/.hermes/hermes-agent && npx playwright install chromium'
```

Check direct Chromium shared-library dependencies. If this prints nothing, the direct `ldd` dependencies are satisfied:

```bash
sudo -iu hermes bash -lc 'ldd ~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell | grep "not found"'
```

Playwright also has `sudo npx playwright install-deps chromium`, but on Rocky Linux it is not the preferred path. Playwright may warn that the OS is not officially supported and fall back to Ubuntu dependency assumptions.

Smoke test:

```bash
sudo -iu hermes bash -lc 'cd ~/.hermes/hermes-agent && node -e "(async()=>{const {chromium}=require(\"playwright\"); const b=await chromium.launch({headless:true}); const p=await b.newPage(); await p.goto(\"data:text/html,<h1>playwright-ok</h1>\"); console.log(await p.textContent(\"h1\")); await b.close();})().catch(e=>{console.error(e.stack||e); process.exit(1)})"'
```

Expected output:

```text
playwright-ok
```

## 12. Production Hardening Hints

For production browser access, prefer `hermes_nginx_enabled: true`: keep the dashboard and WebUI loopback-only and expose only nginx HTTPS with Basic Auth. SSH tunnelling is also fine for single-admin maintenance. Do not expose `8080/tcp` directly unless the surrounding network is trusted and separately protected.

For multiple operators or customers, use one Linux user and one DNS vhost per Hermes instance. Subfolder deployments are intentionally avoided because Hermes dashboard and WebUI use root-relative `/api/...` and WebSocket endpoints.

Secrets should never be stored in this repository. Put Hermes provider secrets in the user's Hermes home or auth store, and put nginx Basic Auth passwords in Ansible Vault or another secret manager.
