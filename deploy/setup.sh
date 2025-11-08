#!/usr/bin/env bash
# Setup script for hosting this Flask site on Ubuntu with systemd + Nginx.
# Usage: run from the project root (the directory containing main.py)
#   sudo bash deploy/setup.sh --domain example.com [--no-nginx]
# The script will:
#   - Install required packages
#   - Create a Python virtualenv in .venv and install requirements
#   - Create a systemd service to run Gunicorn on 127.0.0.1:8000
#   - Optionally configure Nginx to reverse-proxy to Gunicorn
#   - Create an environment file at /etc/eliashaukssoncom.env (if it doesn't exist)

set -euo pipefail

APP_NAME="eliashaukssoncom"
SERVICE_NAME="$APP_NAME.service"
ENV_FILE="/etc/${APP_NAME}.env"
PORT="8000"
DOMAIN=""
SETUP_NGINX=1

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --domain)
      DOMAIN="$2"; shift 2;;
    --no-nginx)
      SETUP_NGINX=0; shift;;
    *)
      echo "Unknown argument: $1" >&2; exit 1;;
  esac
done

PROJECT_DIR="$(pwd)"
if [[ ! -f "$PROJECT_DIR/main.py" ]]; then
  echo "Error: run this script from the project root (main.py not found)." >&2
  exit 1
fi

# Ensure we're root for system changes
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root. Use: sudo bash deploy/setup.sh --domain yourdomain" >&2
  exit 1
fi

# Detect primary user to own files and run the service (default to current sudo user)
RUN_USER="${SUDO_USER:-$(logname 2>/dev/null || echo ubuntu)}"
RUN_GROUP="${RUN_USER}"

# 1) Install dependencies
apt-get update -y
apt-get install -y python3-venv python3-pip
if [[ "$SETUP_NGINX" -eq 1 ]]; then
  apt-get install -y nginx
fi

# 2) Python virtualenv and packages
sudo -u "$RUN_USER" bash -c "cd '$PROJECT_DIR' && python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

# 3) Environment file (create if missing)
if [[ ! -f "$ENV_FILE" ]]; then
  cat >/tmp/${APP_NAME}.env <<'EOF'
# Environment variables for the website service
# Flask environment
FLASK_ENV=production
PYTHONUNBUFFERED=1

# Mail settings (fill in to enable contact form)
#MAIL_SERVER=smtp.gmail.com
#MAIL_PORT=587
#MAIL_USERNAME=your_username
#MAIL_PASSWORD=your_password
#MAIL_USE_TLS=1
#MAIL_USE_SSL=0
#MAIL_DEFAULT_SENDER=me@example.com
#MAIL_RECIPIENT=me@example.com
EOF
  mv /tmp/${APP_NAME}.env "$ENV_FILE"
  chown root:root "$ENV_FILE"
  chmod 640 "$ENV_FILE"
  echo "Created env file at $ENV_FILE. Review and edit it to configure email."
fi

# 4) systemd service
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"
cat >"$SERVICE_PATH" <<EOF
[Unit]
Description=Gunicorn instance to serve ${APP_NAME}
After=network.target
StartLimitIntervalSec=500
StartLimitBurst=5

[Service]
Type=simple
User=${RUN_USER}
Group=${RUN_GROUP}
WorkingDirectory=${PROJECT_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${PROJECT_DIR}/.venv/bin/gunicorn -w 2 -b 127.0.0.1:${PORT} main:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

# 5) Nginx reverse proxy
if [[ "$SETUP_NGINX" -eq 1 ]]; then
  if [[ -z "$DOMAIN" ]]; then
    echo "No domain provided. You can pass --domain example.com to set server_name. Using _ as default."
    DOMAIN="_"
  fi
  NGINX_SITE_PATH="/etc/nginx/sites-available/${APP_NAME}.conf"
  cat >"$NGINX_SITE_PATH" <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    # Max upload size (if needed for forms)
    client_max_body_size 10M;

    location /static/ {
        alias ${PROJECT_DIR}/static/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:${PORT};
        proxy_set_header Host               \$host;
        proxy_set_header X-Real-IP          \$remote_addr;
        proxy_set_header X-Forwarded-For    \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto  \$scheme;
        proxy_redirect off;
    }
}
EOF
  ln -sf "$NGINX_SITE_PATH" "/etc/nginx/sites-enabled/${APP_NAME}.conf"
  # Disable default site if exists
  if [[ -f /etc/nginx/sites-enabled/default ]]; then
    rm -f /etc/nginx/sites-enabled/default
  fi
  nginx -t && systemctl reload nginx
fi

# 6) Final status
systemctl --no-pager --full status "$SERVICE_NAME" || true

cat <<MSG

Setup complete.
- Service: systemctl status ${SERVICE_NAME}
- Logs:    journalctl -u ${SERVICE_NAME} -f
- Env:     ${ENV_FILE} (edit to configure email delivery)
- App dir: ${PROJECT_DIR}
- Nginx:   ${SETUP_NGINX:+enabled at /etc/nginx/sites-available/${APP_NAME}.conf}

If you set a domain with DNS pointing to this server, you can now access: http://${DOMAIN}/
Consider enabling HTTPS with Certbot: sudo apt-get install -y certbot python3-certbot-nginx && sudo certbot --nginx -d ${DOMAIN}
MSG
