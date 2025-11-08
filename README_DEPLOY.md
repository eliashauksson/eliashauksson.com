Deployment: Ubuntu + systemd + Nginx

This repository includes a one-shot setup script to deploy the site on an Ubuntu server.

What it does
- Installs system dependencies (python3-venv, pip, and optionally nginx)
- Creates a Python virtual environment in .venv and installs requirements
- Creates a systemd service that runs Gunicorn bound to 127.0.0.1:8000
- Optionally configures Nginx as a reverse proxy
- Creates an environment file at /etc/eliashaukssoncom.env for runtime settings (email)

Prerequisites
- Ubuntu 20.04/22.04/24.04 with sudo access
- DNS for your domain pointing to the server (optional but recommended)

Quick start
1) Copy this project onto the server (e.g., via git clone or scp)

   git clone https://github.com/you/eliashaukssoncom.git
   cd eliashaukssoncom

2) Run the setup script as root (sudo). Include your domain if you want Nginx configured now:

   sudo bash deploy/setup.sh --domain example.com

   If you do not want Nginx managed by the script:

   sudo bash deploy/setup.sh --no-nginx

3) Check the service status and logs:

   systemctl status eliashaukssoncom.service
   journalctl -u eliashaukssoncom.service -f

4) Configure email (optional, for the Contact form)
   Edit /etc/eliashaukssoncom.env and fill at least the following:

   MAIL_SERVER=smtp.example.com
   MAIL_PORT=587
   MAIL_USERNAME=me@example.com
   MAIL_PASSWORD=your_app_password
   MAIL_USE_TLS=1
   MAIL_USE_SSL=0
   MAIL_DEFAULT_SENDER=me@example.com
   MAIL_RECIPIENT=me@example.com

   Then restart the service:

   sudo systemctl restart eliashaukssoncom.service

5) Enable HTTPS (recommended)
   If you set up Nginx with a real domain, install Certbot and obtain a certificate:

   sudo apt-get install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d example.com

Project layout notes
- Flask app factory is in app/__init__.py and the WSGI entry point is main.py (exposes app)
- Templates live under static/html and are registered accordingly in the factory
- Static assets are served by Nginx directly from the project static/ directory

Common operations
- Restart service: sudo systemctl restart eliashaukssoncom.service
- View logs:       journalctl -u eliashaukssoncom.service -f
- Update code:
  git pull
  . .venv/bin/activate && pip install -r requirements.txt
  sudo systemctl restart eliashaukssoncom.service

Troubleshooting
- If Gunicorn fails to start, check environment variables in /etc/eliashaukssoncom.env
- Ensure the WorkingDirectory in the systemd unit points to the correct project path
- Run the app locally on the server for quick validation:

  . .venv/bin/activate
  FLASK_ENV=development python main.py

  Then curl http://127.0.0.1:5000 to verify it serves before using Gunicorn.
