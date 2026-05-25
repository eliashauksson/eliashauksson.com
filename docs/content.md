# Projects and Logbook Content

Projects and logbook entries are Markdown files with a small frontmatter block.
There is no database and no admin interface: publish by adding a file to the
right folder and deploying the repository.

## Folders

```text
content/
  projects/
    en/
    de/
  logbook/
    en/
    de/

static/
  img/
    projects/
    logbook/
```

German content is optional. If a German folder has no visible entries, the site
falls back to English entries for that section. Detail pages also fall back to
the English file when the requested German slug does not exist.

## Project Entry

Create one Markdown file per project:

```text
content/projects/en/dynamo-buffer.md
```

```markdown
---
title: Dynamo Buffer System
date: 2026-05-25
status: in-progress
summary: A buffer battery and charging system for long-distance bikepacking.
tags: electronics, bikepacking, power
cover_image: /static/img/projects/dynamo-buffer/cover.jpg
draft: false
---

Markdown body here.
```

## Logbook Entry

Create one Markdown file per logbook entry:

```text
content/logbook/en/2026-05-25-dynamo-buffer-v1.md
```

```markdown
---
title: First thoughts on the dynamo buffer
date: 2026-05-25
related_project: dynamo-buffer
summary: Initial architecture ideas for a dynamo-powered charging system.
tags: electronics, bikepacking
cover_image: /static/img/logbook/dynamo-buffer-v1/cover.jpg
draft: false
---

Markdown body here.
```

`related_project` should match the slug of a project. If the matching project
exists, the logbook detail page links to it.

## Metadata

Supported fields:

- `title`: Display title. If missing, the slug is converted to title case.
- `slug`: Optional URL slug. If missing, the filename is used.
- `date`: ISO date in `YYYY-MM-DD` format. Used for newest-first sorting.
- `status`: Optional project status, such as `in-progress` or `complete`.
- `summary`: Short text shown on list pages and detail headers.
- `tags`: Comma-separated tags.
- `cover_image`: Optional static image path.
- `related_project`: Optional logbook field linking to a project slug.
- `draft`: Set to `true` to hide an entry from lists, detail pages, and navbar counts.

## Markdown

The site uses a small built-in Markdown renderer. It supports:

- Headings: `#`, `##`, `###`
- Paragraphs
- Unordered lists with `-` or `*`
- Links: `[label](https://example.com)`
- Images: `![Alt text](/static/img/projects/example/image.jpg)`
- Bold and italic text
- Fenced code blocks:

````markdown
```python
print("hello")
```
````

## Images

Put images under `static/img/projects/` or `static/img/logbook/`, then reference
them with absolute static paths:

```markdown
![Prototype wiring](/static/img/projects/dynamo-buffer/wiring.jpg)
```

Cover images use the same path style in frontmatter:

```yaml
cover_image: /static/img/projects/dynamo-buffer/cover.jpg
```

## Drafts

Draft entries are hidden when `draft: true`:

```yaml
draft: true
```

Removing the field or setting `draft: false` makes the entry visible.
