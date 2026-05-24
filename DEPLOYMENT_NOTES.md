# Deployment Notes

Human notes for future-me. These are not secrets.

## Ownership

- Domain provider: GoDaddy
- Email provider: Proton Mail
- Website domain: `eliashauksson.com`
- Contact address: `contact@eliashauksson.com`
- Flask app name/service name: `eliashaukssoncom`
- Production env file: `/etc/eliashaukssoncom.env`

## DNS Records Used

Website records in GoDaddy:

- `A` record for `@` -> VPS public IPv4 address
- Optional `A` or `CNAME` record for `www` -> same site

Proton mail records in GoDaddy:

- MX records supplied by Proton
- SPF TXT record supplied by Proton
- DKIM CNAME/TXT records supplied by Proton
- DMARC TXT record supplied by Proton or chosen policy

Do not trust old copied DNS values blindly. Always compare GoDaddy DNS records with the current Proton domain setup screen.

## Secrets

Local secrets:

```text
.env
```

Production secrets:

```text
/etc/eliashaukssoncom.env
```

Expected production permissions:

```bash
sudo chown root:root /etc/eliashaukssoncom.env
sudo chmod 600 /etc/eliashaukssoncom.env
```

Never commit:

- `.env`
- SMTP tokens
- VPS private keys
- Proton account credentials

## Local Workflow

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Open:

```text
http://127.0.0.1:5000
```

## Deployment Workflow

```bash
cd /var/www/eliashaukssoncom
git pull
. .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart eliashaukssoncom.service
sudo systemctl status eliashaukssoncom.service
journalctl -u eliashaukssoncom.service -n 100 --no-pager
```

## Recovery if the VPS Dies

1. Create a new Ubuntu VPS.
2. Point GoDaddy `A` records to the new VPS public IP.
3. Clone this repository to `/var/www/eliashaukssoncom`.
4. Run `sudo bash deploy/setup.sh --domain eliashauksson.com`.
5. Recreate `/etc/eliashaukssoncom.env` from a secure password manager or generate a new Proton SMTP token.
6. Set `sudo chmod 600 /etc/eliashaukssoncom.env`.
7. Run Certbot for HTTPS.
8. Test `/home`, `/de/home`, and `/contact`.

## Regenerate Proton SMTP Token

1. Log in to Proton Mail.
2. Go to Settings -> All settings -> IMAP/SMTP -> SMTP tokens.
3. Generate a token for `contact@eliashauksson.com`.
4. Save the token immediately; Proton will not show it again after closing the popup.
5. Update `.env` locally or `/etc/eliashaukssoncom.env` on the server.
6. Restart the app in production.
7. Submit a contact form test.
8. Delete the old token after confirming the new token works.

## Reconfigure Mail

Production env values:

```bash
MAIL_SERVER=smtp.protonmail.ch
MAIL_PORT=587
MAIL_USERNAME=contact@eliashauksson.com
MAIL_PASSWORD=<smtp-token>
MAIL_USE_TLS=1
MAIL_USE_SSL=0
MAIL_DEFAULT_SENDER=contact@eliashauksson.com
MAIL_RECIPIENT=contact@eliashauksson.com
```

Restart after changes:

```bash
sudo systemctl restart eliashaukssoncom.service
```

## Common Commands

Service:

```bash
sudo systemctl status eliashaukssoncom.service
sudo systemctl restart eliashaukssoncom.service
journalctl -u eliashaukssoncom.service -f
```

Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo tail -n 100 /var/log/nginx/error.log
```

HTTPS:

```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

Smoke tests:

```bash
curl -I https://eliashauksson.com/home
curl -I https://eliashauksson.com/de/home
curl -I https://eliashauksson.com/contact
```

## Known TODOs

- Add CSRF protection or a stronger anti-spam mechanism if contact form spam becomes a problem.
- Add rate limiting at Nginx or Flask level if bots target `/contact`.
- Move templates out of `static/html` in a future architecture cleanup; they are not secrets, but serving templates from the static tree is unconventional.
- Keep Proton SMTP/DNS details synced with the current Proton dashboard because provider settings may change.
