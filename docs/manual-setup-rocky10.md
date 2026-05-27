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

## 6. Optional Gateway systemd User Service

The Ansible role only installs this service when:

```yaml
hermes_gateway_enabled: true
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
```

## 7. Optional Dashboard systemd User Service

The Ansible role only installs this service when:

```yaml
hermes_dashboard_enabled: true
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
ExecStart=/home/hermes/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main dashboard --port 8080 --host 0.0.0.0 --insecure
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

curl -fsS http://127.0.0.1:8080 >/dev/null
```

## 8. Pair Messaging Platforms such as Telegram

Run the Hermes gateway setup wizard as the `hermes` user:

```bash
sudo -iu hermes hermes gateway setup
```

For Telegram, select Telegram in the wizard and enter the bot token from BotFather. If the service was installed by the role or by section 6, restart it:

```bash
sudo -iu hermes systemctl --user restart hermes-gateway.service
sudo -iu hermes systemctl --user status hermes-gateway.service --no-pager
```

If you did not install the role-managed service, use Hermes' built-in installer instead:

```bash
sudo -iu hermes hermes gateway install
sudo -iu hermes hermes gateway start
sudo -iu hermes hermes gateway status
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

## 9. Optional Playwright Setup

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

## 10. Production Hardening Hints

For production, do not expose the dashboard directly unless the surrounding network is trusted. Prefer one of these patterns:

- bind the dashboard to `127.0.0.1` and use SSH tunnelling
- place it behind a reverse proxy with TLS and authentication
- restrict access with firewall rules or VPN

Secrets should never be stored in this repository or in role variables.
