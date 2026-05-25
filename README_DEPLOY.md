# Deployment Guide

This site is a Flask app served by Gunicorn behind Nginx, managed by systemd.

Production target:

```text
Domain: eliashauksson.com
Email:  contact@eliashauksson.com
App:    eliashaukssoncom
Port:   127.0.0.1:8000
Env:    /etc/eliashaukssoncom.env
```

The helper script `deploy/setup.sh` can perform most setup automatically, but this document also explains the manual pieces so the deployment is recoverable years later.

## 1. Server Requirements

Use an Ubuntu VPS with:

- Ubuntu 20.04, 22.04, or 24.04
- sudo/root access
- Python 3
- `python3-venv`
- `python3-pip`
- Nginx
- systemd
- DNS records pointing `eliashauksson.com` to the VPS

Install base packages manually if needed:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip nginx
```

## 2. Clone and Install

Clone the repository onto the server:

```bash
cd /var/www
sudo git clone <repo-url> eliashaukssoncom
sudo chown -R "$USER":"$USER" /var/www/eliashaukssoncom
cd /var/www/eliashaukssoncom
```

Create the virtual environment and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` includes `Flask-Limiter`, which provides the contact-form rate limits.

Alternative one-shot setup:

```bash
sudo bash deploy/setup.sh --domain eliashauksson.com
```

The script installs dependencies, creates `.venv`, writes a systemd service, creates `/etc/eliashaukssoncom.env` if missing, and configures Nginx.

## 3. Environment Setup

Production secrets live outside git in:

```text
/etc/eliashaukssoncom.env
```

Create or edit it:

```bash
sudo nano /etc/eliashaukssoncom.env
```

Recommended contents:

```bash
FLASK_ENV=production
PYTHONUNBUFFERED=1
SECRET_KEY=replace_with_a_random_secret
ADMIN_PASSWORD=replace_with_a_long_random_admin_password

MAIL_SERVER=smtp.protonmail.ch
MAIL_PORT=587
MAIL_USERNAME=contact@eliashauksson.com
MAIL_PASSWORD=your_proton_smtp_token
MAIL_USE_TLS=1
MAIL_USE_SSL=0
MAIL_DEFAULT_SENDER=contact@eliashauksson.com
MAIL_RECIPIENT=contact@eliashauksson.com
```

Variable meanings:

- `SECRET_KEY`: Stable Flask session signing key, required in production for contact-form timing protection, admin sessions, and CSRF tokens. Generate one with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`.
- `ADMIN_PASSWORD`: Enables `/admin`. Use a long random password, ideally 24+ characters. If missing, `/admin` returns `404`.
- `MAIL_SERVER`: Proton SMTP submission host.
- `MAIL_PORT`: SMTP submission port. Proton uses `587` with STARTTLS.
- `MAIL_USERNAME`: Proton custom-domain email address paired with the SMTP token.
- `MAIL_PASSWORD`: Proton SMTP token. This is a secret.
- `MAIL_USE_TLS`: `1` for STARTTLS.
- `MAIL_USE_SSL`: `0` for port 587 STARTTLS.
- `MAIL_DEFAULT_SENDER`: From address used by the website.
- `MAIL_RECIPIENT`: Inbox that receives contact form messages.

Lock down permissions:

```bash
sudo chown root:root /etc/eliashaukssoncom.env
sudo chmod 600 /etc/eliashaukssoncom.env
```

Do not create `.env` on the server unless intentionally debugging. Production should use `/etc/eliashaukssoncom.env`.

## 4. Gunicorn

Manual Gunicorn test:

```bash
cd /var/www/eliashaukssoncom
. .venv/bin/activate
gunicorn -w 2 -b 127.0.0.1:8000 main:app
```

In another shell:

```bash
curl -I http://127.0.0.1:8000/home
curl -I http://127.0.0.1:8000/de/home
```

Expected result: `HTTP/1.1 200 OK`.

## 5. systemd Service

Service file:

```text
/etc/systemd/system/eliashaukssoncom.service
```

Expected service:

```ini
[Unit]
Description=Gunicorn instance to serve eliashaukssoncom
After=network.target
StartLimitIntervalSec=500
StartLimitBurst=5

[Service]
Type=simple
User=<deploy-user>
Group=<deploy-user>
WorkingDirectory=/var/www/eliashaukssoncom
EnvironmentFile=/etc/eliashaukssoncom.env
ExecStart=/var/www/eliashaukssoncom/.venv/bin/gunicorn -w 2 -b 127.0.0.1:8000 main:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable eliashaukssoncom.service
sudo systemctl restart eliashaukssoncom.service
sudo systemctl status eliashaukssoncom.service
```

Logs:

```bash
journalctl -u eliashaukssoncom.service -f
```

## 6. Nginx Reverse Proxy

Nginx site file:

```text
/etc/nginx/sites-available/eliashaukssoncom.conf
```

Expected HTTP config before HTTPS:

```nginx
server {
    listen 80;
    server_name eliashauksson.com www.eliashauksson.com;

    client_max_body_size 10M;

    location ^~ /static/html/ {
        return 404;
    }

    location /static/ {
        alias /var/www/eliashaukssoncom/static/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host               $host;
        proxy_set_header X-Real-IP          $remote_addr;
        proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto  $scheme;
        proxy_redirect off;
    }
}
```

Enable and reload:

```bash
sudo ln -sf /etc/nginx/sites-available/eliashaukssoncom.conf /etc/nginx/sites-enabled/eliashaukssoncom.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 7. HTTPS Setup

Install Certbot:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
```

Issue certificate:

```bash
sudo certbot --nginx -d eliashauksson.com -d www.eliashauksson.com
```

Renewal check:

```bash
sudo certbot renew --dry-run
```

## 8. Deployment Update Procedure

Preferred one-command update from the live server checkout:

```bash
chmod +x deploy/update_live.sh
./deploy/update_live.sh
```

The helper refuses to run with uncommitted local changes, pulls `origin master`,
uses `.venv` when present, installs requirements, validates Python and
translation files, restarts `eliashaukssoncom`, and prints status/log output.

Manual equivalent:

```bash
cd /var/www/eliashaukssoncom
git pull origin master
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m compileall app
python -m json.tool translations/en.json > /dev/null
python -m json.tool translations/de.json > /dev/null
sudo systemctl restart eliashaukssoncom.service
sudo systemctl status eliashaukssoncom.service
journalctl -u eliashaukssoncom.service -n 100 --no-pager
```

Smoke test:

```bash
curl -I https://eliashauksson.com/home
curl -I https://eliashauksson.com/de/home
curl -I https://eliashauksson.com/contact
```

Contact anti-spam:

- Global rate limits: `200/day` and `50/hour` per IP.
- Contact POST limits: `5/hour` and `2/minute` per IP.
- Blocks use the generic contact send-error message; the response does not reveal whether timing, rate limiting, honeypots, disposable email, or structural checks triggered.
- Spam events are written to `logs/spam.log` in the app directory with timestamp, IP, reason, and email address only. Message bodies are not logged.

Admin security:

- Production requires a stable `SECRET_KEY`; the app refuses to start without one.
- `/admin` is enabled only when `ADMIN_PASSWORD` is set.
- Use `/admin` only over HTTPS.
- `/admin/login` is rate-limited.
- Admin uploads allow `jpg`, `jpeg`, `png`, `webp`, and `gif`; SVG is intentionally disabled.
- Deleted markdown files are moved to `content/.trash/`.
- Block `/static/html/` in Nginx so template source files are not served directly.

## 9. Troubleshooting

Mail:

- Confirm `/etc/eliashaukssoncom.env` exists.
- Confirm permissions: `sudo ls -l /etc/eliashaukssoncom.env`.
- Confirm `MAIL_USERNAME`, `MAIL_DEFAULT_SENDER`, and `MAIL_RECIPIENT` are `contact@eliashauksson.com`.
- Confirm `MAIL_PASSWORD` is a Proton SMTP token, not the Proton login password.
- Check service logs: `journalctl -u eliashaukssoncom.service -f`.
- If token was rotated, restart the service after editing the env file.

Nginx:

- Test config: `sudo nginx -t`.
- Reload: `sudo systemctl reload nginx`.
- Logs: `sudo tail -n 100 /var/log/nginx/error.log`.
- Confirm Nginx proxies to `127.0.0.1:8000`.

Gunicorn/systemd:

- Status: `sudo systemctl status eliashaukssoncom.service`.
- Logs: `journalctl -u eliashaukssoncom.service -n 100 --no-pager`.
- Confirm `WorkingDirectory` points to the clone.
- Confirm `.venv/bin/gunicorn` exists.

Permissions:

- App files should be readable by the service user.
- The service user needs write access to `logs/spam.log` in the app directory.
- `/etc/eliashaukssoncom.env` should be `root:root` and `600`.
- Other repository files do not need service write access.

DNS:

- Confirm `eliashauksson.com` resolves to the VPS public IP.
- Confirm `www.eliashauksson.com` resolves or redirects as expected.
- For Proton mail, confirm MX, SPF, DKIM, and DMARC records in Proton and GoDaddy.

## 10. Proton Email Notes

Contact form identity:

```text
contact@eliashauksson.com
```

Proton SMTP settings:

```text
Host: smtp.protonmail.ch
Port: 587
Encryption: STARTTLS
Username: contact@eliashauksson.com
Password: Proton SMTP token
```

Token storage:

- Local development: `.env` only.
- Production: `/etc/eliashaukssoncom.env` only.
- Never commit SMTP tokens.

Token rotation:

1. Log in to Proton Mail.
2. Open Settings -> All settings -> IMAP/SMTP -> SMTP tokens.
3. Generate a new SMTP token for `contact@eliashauksson.com`.
4. Put the new token in `/etc/eliashaukssoncom.env`.
5. Run `sudo chmod 600 /etc/eliashaukssoncom.env`.
6. Restart: `sudo systemctl restart eliashaukssoncom.service`.
7. Submit a contact form test.
8. Delete the old token in Proton after confirming the new one works.

Official Proton references:

- SMTP submission: https://proton.me/support/smtp-submission
- Custom domain setup: https://proton.me/support/custom-domain
