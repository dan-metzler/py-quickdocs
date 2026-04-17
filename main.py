import base64
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from markdown_it import MarkdownIt

WEASYPRINT_EXE = Path(__file__).parent / "weasyprint.exe"

def _icon(color: str, path: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" '
        f'viewBox="0 0 24 24" fill="{color}" '
        f'style="vertical-align:middle;margin-right:5px;margin-bottom:2px;">'
        f'<path d="{path}"/></svg>'
    )

ADMONITIONS = {
    "note": {
        "color": "#448aff", "bg": "#e8f4fd",
        # info circle
        "icon": lambda c: _icon(c, "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"),
    },
    "tip": {
        "color": "#00c853", "bg": "#e8f5e9",
        # lightbulb
        "icon": lambda c: _icon(c, "M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z"),
    },
    "warning": {
        "color": "#ff9100", "bg": "#fff8e1",
        # warning triangle
        "icon": lambda c: _icon(c, "M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"),
    },
    "danger": {
        "color": "#ff1744", "bg": "#fce4ec",
        # cancel / error circle
        "icon": lambda c: _icon(c, "M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z"),
    },
    "info": {
        "color": "#00b0ff", "bg": "#e1f5fe",
        # pin / bookmark
        "icon": lambda c: _icon(c, "M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"),
    },
}

_CSS_FILE = Path(__file__).parent / "styles.css"
if not _CSS_FILE.exists():
    print(f"Error: styles.css not found at {_CSS_FILE}")
    sys.exit(1)
CSS = _CSS_FILE.read_text(encoding="utf-8") + "".join(
    f".admonition.{t} {{ background: {s['bg']}; border-left-color: {s['color']}; }}\n"
    f".admonition.{t} .admonition-title {{ color: {s['color']}; }}\n"
    for t, s in ADMONITIONS.items()
)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML-style frontmatter from top of markdown."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().rstrip(",")
    return meta, text[match.end():]


def _embed_image(path: str, source_dir: Path) -> str:
    """Return a base64 data URI for an image so it resolves from any temp path."""
    img = Path(path) if Path(path).is_absolute() else source_dir / path
    if not img.exists():
        print(f"Error: logo not found: {img}")
        sys.exit(1)
    data = base64.b64encode(img.read_bytes()).decode()
    suffix = img.suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "svg": "svg+xml", "webp": "webp"}.get(suffix, "png")
    return f"data:image/{mime};base64,{data}"


def make_banner(meta: dict, source_dir: Path = Path(".")) -> str:
    """Render a cover banner from frontmatter metadata."""
    if not meta:
        return ""
    logo     = meta.get("logo", "")
    company  = meta.get("company", "")
    title    = meta.get("title", "")
    subtitle = meta.get("subtitle", "")
    version  = meta.get("version", "")
    date     = meta.get("date", "")
    color    = meta.get("color", "#1a73e8")
    stripe   = meta.get("stripe", "false")

    if stripe.lower() == "true":
        stripe_color = "#005EB8"
    elif stripe.lower() == "false":
        stripe_color = None
    else:
        stripe_color = stripe

    stripe_style = f"border-left: 10px solid {stripe_color}; padding-left: 26px;" if stripe_color else ""

    meta_parts = " &nbsp;·&nbsp; ".join(filter(None, [version, date]))

    logo_height = meta.get("logo-height", "48px")

    if logo:
        top = f'<img src="{_embed_image(logo, source_dir)}" style="height:{logo_height};margin-bottom:12px;display:block;">'
    elif company:
        top = f'<div class="cover-company">{company}</div>'
    else:
        top = ""

    return f"""
<div class="cover-banner" style="background: {color}; {stripe_style}">
  {top}
  {"" if not title      else f'<div class="cover-title">{title}</div>'}
  {"" if not subtitle   else f'<div class="cover-subtitle">{subtitle}</div>'}
  {"" if not meta_parts else f'<div class="cover-meta">{meta_parts}</div>'}
</div>
"""


def preprocess_admonitions(text: str, md: MarkdownIt) -> str:
    """Convert Docusaurus-style ::: blocks to styled HTML divs."""
    lines = text.split("\n")
    result = []
    i = 0
    while i < len(lines):
        match = re.match(r'^:::([\w]+)(?:\s+"?([^"]*)"?)?$', lines[i].strip())
        if match:
            atype = match.group(1).lower()
            title = match.group(2) or atype.capitalize()
            style = ADMONITIONS.get(atype, {
                "color": "#888", "bg": "#f5f5f5",
                "icon": lambda c: _icon(c, "M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z"),
            })
            i += 1
            inner_lines = []
            while i < len(lines) and lines[i].strip() != ":::":
                inner_lines.append(lines[i])
                i += 1
            if i >= len(lines):
                print(f"Warning: unclosed admonition block ':::{atype}' — closing ':::' missing")

            inner_html = md.render("\n".join(inner_lines))
            result.append(f'<div class="admonition {atype}">')
            result.append(f'<div class="admonition-title">{style["icon"](style["color"])} {title}</div>')
            result.append(inner_html)
            result.append("</div>")
        else:
            result.append(lines[i])
        i += 1
    return "\n".join(result)


def md_to_pdf(input_path: Path, output_path: Path) -> None:
    if not WEASYPRINT_EXE.exists():
        print(f"Error: weasyprint.exe not found at {WEASYPRINT_EXE}")
        sys.exit(1)
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}")
        sys.exit(1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    md = MarkdownIt().enable("table")
    text = input_path.read_text(encoding="utf-8")
    meta, text = parse_frontmatter(text)
    text = preprocess_admonitions(text, md)
    banner = make_banner(meta, input_path.parent)
    body = md.render(text)
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>{CSS}</style>
</head>
<body>{banner}{body}</body>
</html>"""
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        tmp = f.name

    try:
        result = subprocess.run(
            [WEASYPRINT_EXE, tmp, str(output_path)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(result.stderr)
            sys.exit(result.returncode)
    finally:
        Path(tmp).unlink(missing_ok=True)

    print(f"Written: {output_path}")


OUTPUT_DIR = Path(__file__).parent / "output"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run main.py <input.md> [output.pdf]")
        sys.exit(1)
    inp = Path(sys.argv[1])
    if len(sys.argv) > 2:
        out = Path(sys.argv[2])
    else:
        OUTPUT_DIR.mkdir(exist_ok=True)
        out = OUTPUT_DIR / inp.with_suffix(".pdf").name
    md_to_pdf(inp, out)
