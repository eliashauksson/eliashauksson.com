Local Development

Setup
1. Create and activate a virtual environment:

   python3 -m venv .venv
   . .venv/bin/activate

2. Install dependencies:

   pip install -r requirements.txt

3. Create a local environment file for email settings:

   cp .env.example .env

4. Fill in the values in .env:

   MAIL_SERVER=smtp.example.com
   MAIL_PORT=587
   MAIL_USERNAME=me@example.com
   MAIL_PASSWORD=your_app_password
   MAIL_USE_TLS=1
   MAIL_USE_SSL=0
   MAIL_DEFAULT_SENDER=me@example.com
   MAIL_RECIPIENT=me@example.com

5. Run the site:

   python main.py

Then open http://127.0.0.1:5000.

Notes
- .env is ignored by git and must not contain values meant to be committed.
- .env.example contains placeholders only and is safe to commit.
- Existing system environment variables take priority over .env values.
- If email variables are missing, the contact form stays available but shows a friendly delivery error.
