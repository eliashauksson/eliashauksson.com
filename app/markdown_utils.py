import re


def render_markdown(md: str) -> str:
    """
    Very small markdown-to-HTML renderer to avoid external deps.
    Supports:
      - Headings: #, ##, ### → h1..h3
      - Unordered lists: lines starting with -, *
      - Paragraphs: separated by blank lines
      - Inline: **bold**, *italic*, [text](url)
      - Line breaks: two spaces at EOL → <br>
    This is intentionally minimal — good for simple content blocks.
    """
    # Normalize line endings
    md = md.replace("\r\n", "\n").replace("\r", "\n")

    html_lines = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            html_lines.append("</ul>")
            in_list = False

    # Inline replacements
    def inline(txt: str) -> str:
        # Escape minimal HTML
        txt = (txt
               .replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;"))
        # Links [text](url)
        txt = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', txt)
        # Bold **text**
        txt = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", txt)
        # Italic *text*
        txt = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", txt)
        # Line break on two spaces before newline handled later
        return txt

    paragraphs = []
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
            paragraphs.append(" ".join(joined))
            current_para = []

    lines = md.split("\n")
    for raw in lines:
        line = raw.rstrip("\n")
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

    # Wrap paragraphs
    for p in paragraphs:
        html_lines.append(f"<p>{p}</p>")

    return "\n".join(html_lines)
