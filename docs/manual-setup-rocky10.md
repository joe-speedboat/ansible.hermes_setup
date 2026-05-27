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

```bash
sudo dnf install -y \
  bash \
  ca-certificates \
  curl \
  git \
  jq \
  openssl \
  python3 \
  python3-pip \
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
sudo -iu hermes mkdir -p ~/.config/systemd/user
```

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
sudo -iu hermes mkdir -p ~/.config/systemd/user
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

curl -fsS http://127.0.0.1:8080 >/dev/null
```

The dashboard listens on loopback only. Do **not** open `8080/tcp` in firewalld for browser access. Use SSH tunnelling or the nginx reverse proxy pattern below.

## 8. Optional nginx HTTPS + Basic Auth Reverse Proxy

The Ansible role can enable this automatically with `hermes_nginx_enabled: true`. For manual setup, install nginx and keep the Hermes dashboard bound to `127.0.0.1`:

```bash
sudo dnf install -y nginx openssl
sudo mkdir -p /etc/pki/tls/hermes
sudo openssl req -x509 -newkey rsa:4096 -sha256 -days 825 -nodes \
  -keyout /etc/pki/tls/hermes/tls.key \
  -out /etc/pki/tls/hermes/tls.crt \
  -subj '/CN=hermes.example.ch' \
  -addext 'subjectAltName=DNS:hermes.example.ch'
sudo chmod 0600 /etc/pki/tls/hermes/tls.key
```

Create `/etc/nginx/.htpasswd-hermes` with a SHA-512 crypt hash. Use a real password, ideally sourced from a secret manager or Ansible Vault:

```bash
python3 - <<'PY' | sudo tee /etc/nginx/.htpasswd-hermes >/dev/null
import crypt, getpass
user = 'chris'
password = getpass.getpass('Basic Auth password: ')
print(f'{user}:{crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))}')
PY
sudo chown root:nginx /etc/nginx/.htpasswd-hermes
sudo chmod 0640 /etc/nginx/.htpasswd-hermes
```

Create `/etc/nginx/conf.d/hermes.conf`:

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

    ssl_certificate /etc/pki/tls/hermes/tls.crt;
    ssl_certificate_key /etc/pki/tls/hermes/tls.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    client_max_body_size 100m;

    auth_basic "Hermes";
    auth_basic_user_file /etc/nginx/.htpasswd-hermes;

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

Enable nginx and open HTTPS:

```bash
sudo setsebool -P httpd_can_network_connect 1
sudo nginx -t
sudo systemctl enable --now nginx
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

Verify:

```bash
curl -skI https://hermes.example.ch/ | sed -n '1,8p'
curl -skI -u chris:'<password>' https://hermes.example.ch/ | sed -n '1,8p'
```

For multiple Hermes users, use one DNS vhost per Linux user and dashboard port, for example `chris-hermes.example.ch -> 127.0.0.1:8081` and `dev-hermes.example.ch -> 127.0.0.1:8082`. Avoid subfolders because Hermes uses root-relative `/api/...` and WebSocket endpoints.

## 9. Pair Messaging Platforms such as Telegram

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

Restart both role-managed services as the `hermes` user:

```bash
sudo -iu hermes systemctl --user restart hermes-gateway.service
sudo -iu hermes systemctl --user restart hermes-dashboard.service
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

## 10. Playwright Setup

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

## 11. Production Hardening Hints

For production dashboard access, prefer `hermes_nginx_enabled: true`: keep the dashboard loopback-only and expose only nginx HTTPS with Basic Auth. SSH tunnelling is also fine for single-admin maintenance. Do not expose `8080/tcp` directly unless the surrounding network is trusted and separately protected.

For multiple operators or customers, use one Linux user and one DNS vhost per Hermes instance. Subfolder deployments are intentionally avoided because Hermes dashboard uses root-relative `/api/...` and WebSocket endpoints.

Secrets should never be stored in this repository. Put Hermes provider secrets in the user's Hermes home or auth store, and put nginx Basic Auth passwords in Ansible Vault or another secret manager.
