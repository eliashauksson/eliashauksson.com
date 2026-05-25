# Admin Interface

The admin interface manages the markdown-backed Projects and Logbook sections.
It does not use a database and does not add user roles.

## Enable Admin

Set a stable Flask secret key and an admin password in the environment:

```bash
SECRET_KEY=replace_with_a_stable_random_secret
ADMIN_PASSWORD=replace_with_a_long_random_password
```

Production should set this in `/etc/eliashaukssoncom.env` alongside the other
service settings. `SECRET_KEY` must be stable across restarts so sessions and
CSRF tokens remain valid. `ADMIN_PASSWORD` should be a long random password,
ideally 24+ characters.

If `ADMIN_PASSWORD` is missing, `/admin` is disabled and returns `404`. If
`SECRET_KEY` is missing in production, the app refuses to start with a clear
error.

The admin login stores only this state in the Flask session:

```text
admin_authenticated = true
```

The password is never written to disk by the app.

## Login

Open:

```text
/admin/login
```

After login, the dashboard is available at:

```text
/admin
```

Logout is a POST action from the dashboard.

## Security Assumptions

- Use HTTPS in production.
- Set a stable `SECRET_KEY` in production so sessions and CSRF tokens survive app restarts.
- Set a long random `ADMIN_PASSWORD`, ideally 24+ characters.
- `SESSION_COOKIE_HTTPONLY` and `SESSION_COOKIE_SAMESITE=Lax` are enabled.
- `SESSION_COOKIE_SECURE` is enabled when `FLASK_ENV=production`.
- Every admin POST form requires a session CSRF token.
- `/admin/login` is rate-limited.
- SVG uploads are intentionally disabled because browser-rendered SVG can carry active content.
- Admin markdown editing is limited to English files in:
  - `content/projects/en/`
  - `content/logbook/en/`
- Filenames, slugs, dates, sections, and upload extensions are validated server-side.
- Flask blocks direct local access to `/static/html/*`. Production Nginx should
  also block that path because templates currently live under `static/html`.

## Saved Files

New project files are saved under:

```text
content/projects/en/
```

New logbook files are saved under:

```text
content/logbook/en/
```

Generated filenames use:

```text
YYYY-MM-DD-slug.md
```

Editing an existing entry saves back to the same filename, even if the date or
slug metadata changes.

## Preview

The create/edit form has a Preview action. Preview renders the markdown with the
same renderer as the public site and does not write files.

## Deletes and Trash

Delete actions require confirmation and use POST with CSRF protection.

Deleted files are moved to:

```text
content/.trash/projects/
content/.trash/logbook/
```

Trash filenames are prefixed with a UTC timestamp:

```text
20260525123015999999-original-filename.md
```

Restore a trashed file manually by moving it back into the correct content
folder.

## Media Uploads

The media manager is available at:

```text
/admin/media
```

Allowed extensions:

```text
jpg, jpeg, png, webp, gif
```

Uploads are stored by section and slug:

```text
static/img/projects/<slug>/
static/img/logbook/<slug>/
```

After upload, the admin page shows the path to paste into frontmatter or
markdown:

```text
/static/img/projects/dynamo-buffer/image.jpg
```

The default upload size limit is 5 MB. It can be changed with:

```bash
MAX_UPLOAD_BYTES=5242880
```

## Nginx Template Guard

Add this location before the broader `/static/` location in the production Nginx
site config:

```nginx
location ^~ /static/html/ {
    return 404;
}
```
