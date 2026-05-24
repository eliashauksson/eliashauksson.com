# Local Development

This guide starts from a fresh clone and runs the Flask site locally.

## 1. Create a Virtual Environment

```bash
python3 -m venv .venv
```

## 2. Activate the Virtual Environment

```bash
. .venv/bin/activate
```

## 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Create Local Environment File

```bash
cp .env.example .env
```

`.env` is ignored by git. Put local secrets there, never in tracked files.

## 5. Configure Proton SMTP

For local contact-form testing, edit `.env`:

```bash
MAIL_SERVER=smtp.protonmail.ch
MAIL_PORT=587
MAIL_USERNAME=contact@eliashauksson.com
MAIL_PASSWORD=your_proton_smtp_token
MAIL_USE_TLS=1
MAIL_USE_SSL=0
MAIL_DEFAULT_SENDER=contact@eliashauksson.com
MAIL_RECIPIENT=contact@eliashauksson.com
```

Notes:
- `MAIL_PASSWORD` must be a Proton SMTP token, not the Proton account password.
- Generate SMTP tokens in Proton Mail settings for `contact@eliashauksson.com`.
- Existing shell environment variables win over `.env`; the loader never overwrites them.
- Without valid mail settings, the site still runs and the contact form shows a friendly send error.

## 6. Run Locally

```bash
python main.py
```

Open:

```text
http://127.0.0.1:5000
```

Useful local routes:

```text
/home
/about
/contact
/de/home
/de/about
/de/contact
```

## 7. Test the Contact Form

1. Start the app with `python main.py`.
2. Open `http://127.0.0.1:5000/contact`.
3. Submit a test message.
4. Check the inbox for `contact@eliashauksson.com`.
5. If sending fails, check the terminal output for server-side mail logs.

The browser should never show raw SMTP exceptions.
