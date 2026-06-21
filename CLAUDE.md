# eliashauksson.com — project guide for Claude Code

Personal website for Elías Hauksson, electrical engineering student. Flask app, no frontend framework, no build step. Running at eliashauksson.com on Ubuntu + Gunicorn + Nginx.

---

## Stack

| Layer | Detail |
|---|---|
| Runtime | Python / Flask 2.x via `main.py` → `app/create_app()` |
| Templates | Jinja2, files live in `static/html/` (not `templates/`) |
| Styles | Single file `static/css/style.css` — no preprocessor, no bundler |
| Markdown | Custom renderer in `app/markdown_utils.py` (no external dep) |
| Content | Markdown files with YAML frontmatter in `content/` |
| Rate limiting | Flask-Limiter (`app/extensions.py`) |
| WSGI | Gunicorn on `127.0.0.1:8000`, reverse-proxied by Nginx |
| Service | systemd unit named `eliashaukssoncom` |

---

## URL structure and routing (`app/routes.py`)

- Default language is `en`; German adds `/de/` prefix to every URL.
- `/ → /home`, `/de → /de/home`
- Routes: `/home`, `/about`, `/contact`, `/projects`, `/projects/<slug>`, `/logbook`, `/logbook/<slug>`
- Admin blueprint at `/admin` (disabled unless `ADMIN_PASSWORD` env var is set)
- `current_page()` returns the logical page name (`projects` for both index and detail, same for `logbook`); this drives `.active` nav highlighting.
- Every template receives via `@app.context_processor`: `lang`, `text` (translations dict), `current_page`, `localized_url`, `language_switch_url`, `has_projects`, `has_logbook`.

---

## Content system (`app/content_loader.py`)

Content lives in `content/<section>/<lang>/*.md` where `<section>` is `projects` or `logbook`.

**Frontmatter fields:**

| Field | Type | Notes |
|---|---|---|
| `title` | string | required |
| `slug` | string | required for projects; optional for logbook (falls back to filename stem) |
| `date` | `YYYY-MM-DD` | used for sorting (newest first) |
| `status` | string | projects only (e.g. `in-progress`) |
| `summary` | string | short description shown in index and detail header |
| `tags` | comma-separated | e.g. `electronics, bikepacking` |
| `cover_image` | path | must start with `/static/img/` |
| `related_project` | slug | logbook only; links back to a project |
| `draft` | `true`/`false` | hides from public views |

Entries with `draft: true` are invisible to public routes but visible in admin.

Language fallback: if no DE entries exist for a section, the EN entries are shown.

---

## Templates (`static/html/`)

All templates extend `base.html`. The template folder is `static/html/` (set in `create_app()`).

| File | Page |
|---|---|
| `base.html` | Navbar, `<head>`, script tags, `{% block content %}` |
| `home.html` | Full-viewport hero with mountain photo |
| `about.html` | `about_content` (rendered from `content/<lang>/about.md`) injected as `about_content|safe` |
| `projects.html` | List of projects passed as `projects` |
| `project_detail.html` | Single project as `project` dict |
| `logbook.html` | List of entries as `entries` |
| `logbook_detail.html` | Single entry as `entry` dict; `related_project` dict or None |
| `contact.html` | Form with `status`, `error`, `form` (dict with name/email/message) |
| `admin/*.html` | Admin UI — password-protected, English only |
| `403.html`, `404.html`, `500.html` | Error pages |

The navbar is in `base.html`. The mobile hamburger button (`.nav-toggle`) is toggled by `static/js/nav.js`.

`body.home-page` class is added when `current_page == 'home'`, which makes the navbar transparent/absolute over the hero.

---

## Translations (`translations/`)

`translations/en.json` and `translations/de.json` — loaded by `app/translations.py` using `@lru_cache`.

All UI strings go through the `text` context variable (`text.key_name`). The `about_intro` value in `en.json` contains inline HTML (`<br />`), rendered with `|safe` in the template.

---

## Static assets

- `static/css/style.css` — the one and only stylesheet
- `static/js/nav.js` — mobile nav toggle only
- `static/img/mountain_in_the_morning.jpg` — hero photo
- `static/img/projects/<slug>/` — per-project media
- `static/img/logbook/<slug>/` — per-logbook-entry media

Media uploaded via admin goes to `static/img/<section>/<slug>/`. Deleted media is moved to `static/img/.trash/`. Deleted content is moved to `content/.trash/`.

Nginx serves `/static/` directly (bypasses Flask) with 30-day cache headers. Nginx blocks `/static/html/` (prevents direct template access), and Flask also blocks it with `abort(404)` in `before_request`.

---

## Contact form (`app/routes.py` + `app/mail_utils.py`)

Spam defenses (in order):
1. Honeypot hidden fields: `company`, `website`, `contact_confirm`
2. Minimum submission time (3s — session timer set on GET)
3. Structural checks: name length 2–100, email max 254, message 10–5000 chars, no repeated chars, Shannon entropy check (rejects very low-entropy messages ≥80 chars)
4. Disposable email check (`app/disposable_domains.py`)
5. Rate limiting: 5/hour and 2/minute per IP (POST only)

Email sent via SMTP. Required env vars: `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS`, `MAIL_DEFAULT_SENDER`, `MAIL_RECIPIENT`.

---

## Admin (`app/admin.py`)

Route prefix `/admin`. Disabled (404) unless `ADMIN_PASSWORD` env var is set. Session-based auth. CSRF protection on all POSTs.

Features:
- Dashboard: counts + 6 most recent entries
- List, create, edit, delete for `projects` and `logbook` (EN only)
- Markdown editor with live preview
- Media manager: upload, rename, delete (moves to trash), search by section/slug
- Allowed image types: jpg, jpeg, png, webp, gif; max 5 MB

Content files generated as `<date>-<slug>.md` in `content/<section>/en/`.

---

## Environment variables

Loaded from `.env` at project root in development (via `app/env.py`). In production, set in `/etc/eliashaukssoncom.env` (owned root, chmod 600).

| Var | Required | Purpose |
|---|---|---|
| `SECRET_KEY` | Yes (prod) | Flask session signing |
| `FLASK_ENV` or `APP_ENV` | Yes (prod) | Set to `production` to enable HSTS and require SECRET_KEY |
| `ADMIN_PASSWORD` | Optional | Enables `/admin` |
| `MAIL_SERVER` | Optional | SMTP host for contact form |
| `MAIL_PORT` | Optional | SMTP port |
| `MAIL_USERNAME` | Optional | SMTP login |
| `MAIL_PASSWORD` | Optional | SMTP login |
| `MAIL_USE_TLS` | Optional | Default `1` |
| `MAIL_USE_SSL` | Optional | Default `0` |
| `MAIL_DEFAULT_SENDER` | Optional | From address |
| `MAIL_RECIPIENT` | Optional | Delivery address |

---

## Deployment

**First-time setup:** `sudo bash deploy/setup.sh --domain eliashauksson.com`
- Installs Python venv, requirements, systemd service, Nginx config
- Creates `/etc/eliashaukssoncom.env` template if not present

**Live update (on the server):** `bash deploy/update_live.sh`
- Verifies we're on `master`, refuses dirty code/config/template files
- Allows dirty `content/` and `static/img/` (live admin-created content is preserved through pulls)
- `git pull --ff-only origin master`
- Reinstalls pip deps, compiles Python, validates JSON translations
- `sudo systemctl restart eliashaukssoncom`

---

## Pending work: Swiss Technical redesign (HANDOFF.md)

**Status as of 2026-06-21: NOT YET APPLIED.** `style.css` and all templates are still on the old design.

`HANDOFF.md` contains a complete, high-fidelity spec for a visual redesign ("Swiss Technical" — Helvetica on white, monospace metadata, sharp corners, hairline rules, numbered list entries, coordinate strip on hero).

Key changes described:
- New `:root` CSS design tokens (`--ink`, `--prose`, `--muted`, `--faint`, `--hairline`, `--mono`, etc.)
- Navbar: logo wordmark → "Hauksson" + `<span class="logo__tag">EE · CH</span>`; mono nav links; `border-bottom: 1px solid var(--ink)`
- Hero: coordinate strip top, eyebrow text, caption bottom-right (no background box), content anchored to bottom
- Index pages: numbered hairline-ruled list (`.entry` with `.entry__num`) replacing `.entry-card` boxes
- Detail pages: mono back-link, mono meta row, counter-based section markers on h2/h3, cover image in 16:9 hairline frame
- Contact: two-column grid, mono labels, hairline social list on right
- About: Profile-rail two-column grid
- Footer: new simple mono footer on all pages except home

All values in `HANDOFF.md` are **literal** — match exactly. A design reference HTML prototype exists as `Eliashauksson Site.dc.html` (not in repo, was provided separately).

Files to edit for redesign: `static/css/style.css`, `static/html/base.html`, `static/html/home.html`, `static/html/projects.html`, `static/html/logbook.html`, `static/html/project_detail.html`, `static/html/logbook_detail.html`, `static/html/contact.html`, `static/html/about.html`.

---

## Running locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Create .env with SECRET_KEY and optional ADMIN_PASSWORD, MAIL_* vars
flask --app main run --debug
```

Site at `http://localhost:5000`. Admin at `/admin` if `ADMIN_PASSWORD` is set in `.env`.

---

## Security notes

- CSP set in `app/__init__.py` `add_security_headers()` — `style-src 'unsafe-inline'` is allowed (no nonces needed for current inline-free stylesheet, but the policy permits it)
- `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`
- `Strict-Transport-Security` only in production
- Admin routes abort 404 if `ADMIN_PASSWORD` not set (no 403 disclosure)
- CSRF via `hmac.compare_digest` on session token
- Media path validation: `safe_join` + `Path.resolve()` to prevent traversal
- Markdown renderer (`app/markdown_utils.py`) does `html.escape()` before processing — XSS-safe

---

## Coding principles

### Readability and clarity

- Code is read far more than it's written — optimize for the reader.
- Follow PEP 8. Use a formatter (Black or `ruff format`) so style is never debated.
- Names should reveal intent. `elapsed_seconds` beats `t`. A good name removes the need for a comment.
- Comment the *why*, not the *what*. The code already shows what it does — explain reasoning, constraints, or non-obvious tradeoffs.
- Prefer explicit over implicit (Zen of Python). This is the best tiebreaker for style disputes.

### Structure and design

- **Single responsibility**: a function does one thing. If you can't name it without "and," split it.
- Keep functions small and side-effect-light. Pure functions (input → output, no hidden state) are easiest to test and compose.
- **DRY, but don't over-abstract.** Tolerate duplication until the third occurrence, then extract.
- **YAGNI** — don't build for hypothetical futures. Solve the problem in front of you.
- Composition over inheritance. Duck typing and `typing.Protocol` usually make deep class hierarchies unnecessary.
- Fail fast and loudly. Validate inputs early, raise specific exceptions, never use a bare `except:`.

### Python idioms

- Write idiomatic Python: use comprehensions, `enumerate`, `zip`, unpacking, context managers, generators.
- Reach for the standard library before a dependency: `itertools`, `functools`, `collections`, `pathlib`, `dataclasses`.
- Manage resources with `with`. Context managers guarantee cleanup even on exceptions.
- Prefer generators (`yield`) for large or streaming data — keeps memory flat, composes lazily.
- Use type hints. They document intent, catch bugs via mypy/pyright, and make refactors safer.
- Prefer EAFP over LBYL where natural — try the operation and handle the exception rather than pre-checking.

### Correctness and maintenance

- Test behavior, not implementation, so tests survive refactors. `pytest` with plain `assert`.
- Make illegal states unrepresentable. Use `dataclasses` / `enum` / types so invalid data can't exist.
- Pin and isolate dependencies. A lockfile and virtual environment make builds reproducible.
- Automate the boring checks: Ruff (lint + format), mypy, and pre-commit hooks catch issues before review.
- Optimize only with evidence. Profile first — clarity first unless a real, measured problem says otherwise.

### Meta-principle

Consistency beats personal preference. A uniformly "fine" codebase beats one that's locally optimal but globally inconsistent. Match the surrounding code.

---

## Claude behavior defaults

**After every codebase change, update all project documentation files** to reflect what changed. This includes `CLAUDE.md`, `HANDOFF.md`, and any other `*.md` files at the project root (e.g. `README.md`, `DEPLOY.md`). Keep only the sections that are affected — don't rewrite everything, just keep the docs accurate.
