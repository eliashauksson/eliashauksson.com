import html
import re
from urllib.parse import urlparse


ALLOWED_LINK_SCHEMES = {"", "http", "https", "mailto"}
ALLOWED_IMAGE_SCHEMES = {"", "http", "https"}


def render_markdown(md: str) -> str:
    """
    Very small markdown-to-HTML renderer to avoid external deps.
    Supports:
      - Headings: #, ##, ### → h1..h3
      - Unordered lists: lines starting with -, *
      - Images: ![alt](url)
      - Fenced code blocks: ``` or ```language
      - Paragraphs: separated by blank lines
      - Inline: **bold**, *italic*, [text](url)
      - Line breaks: two spaces at EOL → <br>
    This is intentionally minimal — good for simple content blocks.
    """
    # Normalize line endings
    md = md.replace("\r\n", "\n").replace("\r", "\n")

    html_lines = []
    in_list = False
    in_code = False
    code_language = ""
    code_lines = []

    def close_list():
        nonlocal in_list
        if in_list:
            html_lines.append("</ul>")
            in_list = False

    def close_code():
        nonlocal in_code, code_language, code_lines
        if not in_code:
            return
        class_attr = f' class="language-{code_language}"' if code_language else ""
        code = html.escape("\n".join(code_lines))
        html_lines.append(f"<pre><code{class_attr}>{code}</code></pre>")
        in_code = False
        code_language = ""
        code_lines = []

    # Inline replacements
    def inline(txt: str) -> str:
        txt = html.escape(txt)

        def image(match):
            alt = match.group(1)
            url = html.unescape(match.group(2)).strip()
            parsed = urlparse(url)
            if parsed.scheme.lower() not in ALLOWED_IMAGE_SCHEMES:
                return alt
            return (
                f'<img src="{html.escape(url, quote=True)}" '
                f'alt="{html.escape(alt, quote=True)}" loading="lazy">'
            )

        def link(match):
            label = match.group(1)
            url = html.unescape(match.group(2)).strip()
            parsed = urlparse(url)
            if parsed.scheme.lower() not in ALLOWED_LINK_SCHEMES:
                return label
            return f'<a href="{html.escape(url, quote=True)}">{label}</a>'

        txt = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", image, txt)
        txt = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, txt)
        # Bold **text**
        txt = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", txt)
        # Italic *text*
        txt = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", txt)
        # Line break on two spaces before newline handled later
        return txt

    current_para = []

    def flush_paragraph():
        nonlocal current_para
        if current_para:
            # Join lines with space; keep hard line breaks when two spaces at EOL
            joined = []
            for i, ln in enumerate(current_para):
                if ln.endswith("  "):
                    joined.append(inline(ln.rstrip()) + "<br>")
                else:
                    joined.append(inline(ln))
            html_lines.append(f"<p>{' '.join(joined)}</p>")
            current_para = []

    lines = md.split("\n")
    for raw in lines:
        line = raw.rstrip("\n")

        if in_code:
            if line.strip().startswith("```"):
                close_code()
            else:
                code_lines.append(line)
            continue

        if line.strip().startswith("```"):
            flush_paragraph()
            close_list()
            in_code = True
            language = line.strip()[3:].strip().split(" ", 1)[0]
            code_language = re.sub(r"[^a-zA-Z0-9_-]", "", language)
            code_lines = []
            continue

        if not line.strip():
            # blank line ends paragraph or list
            flush_paragraph()
            close_list()
            continue

        # Headings
        if line.startswith("### "):
            flush_paragraph(); close_list()
            html_lines.append(f"<h3>{inline(line[4:])}</h3>")
            continue
        if line.startswith("## "):
            flush_paragraph(); close_list()
            html_lines.append(f"<h2>{inline(line[3:])}</h2>")
            continue
        if line.startswith("# "):
            flush_paragraph(); close_list()
            html_lines.append(f"<h1>{inline(line[2:])}</h1>")
            continue

        # Unordered list
        if line.lstrip().startswith(("- ", "* ")):
            flush_paragraph()
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item = line.lstrip()[2:]
            html_lines.append(f"<li>{inline(item)}</li>")
            continue

        # Otherwise, part of a paragraph
        current_para.append(line)

    # Close any open structures
    flush_paragraph()
    close_list()
    close_code()

    return "\n".join(html_lines)
