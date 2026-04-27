import base64
import html as _html
import re
import subprocess
import sys
import tempfile
from datetime import date as _date
from pathlib import Path
from markdown_it import MarkdownIt

try:
    from pygments import highlight as _pyg_highlight
    from pygments.formatters import HtmlFormatter as _HtmlFormatter
    from pygments.lexers import get_lexer_by_name as _get_lexer, TextLexer as _TextLexer
    from pygments.util import ClassNotFound as _ClassNotFound
    _PYGMENTS = True
except ImportError:
    _PYGMENTS = False

WEASYPRINT_EXE = Path(__file__).parent / "weasyprint.exe"


def _icon(color: str, path: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" '
        f'viewBox="0 0 24 24" fill="{color}" '
        f'style="vertical-align:middle;margin-right:5px;margin-bottom:2px;">'
        f'<path d="{path}"/></svg>'
    )


def _parse_root_vars(css: str) -> dict[str, str]:
    """Extract CSS custom properties from all :root blocks (later blocks override earlier)."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    vars: dict[str, str] = {}
    for block in re.findall(r':root\s*\{([^}]*)\}', css):
        for m in re.finditer(r'--([a-zA-Z0-9-]+)\s*:\s*([^;]+)', block):
            vars[m.group(1)] = m.group(2).strip()
    return vars


def _tint(hex_color: str, amount: float) -> str:
    """Blend hex_color toward white. amount=0.15 → 15% color, 85% white."""
    c = hex_color.strip().lstrip('#')
    if len(c) == 3:
        c = c[0]*2 + c[1]*2 + c[2]*2
    if len(c) != 6:
        return hex_color
    try:
        r = round(int(c[0:2], 16) * amount + 255 * (1 - amount))
        g = round(int(c[2:4], 16) * amount + 255 * (1 - amount))
        b = round(int(c[4:6], 16) * amount + 255 * (1 - amount))
        return f'#{r:02x}{g:02x}{b:02x}'
    except ValueError:
        return hex_color


def _shade(hex_color: str, amount: float) -> str:
    """Darken hex_color toward black. amount=0.6 → 60% of original brightness."""
    c = hex_color.strip().lstrip('#')
    if len(c) == 3:
        c = c[0]*2 + c[1]*2 + c[2]*2
    if len(c) != 6:
        return hex_color
    try:
        r = round(int(c[0:2], 16) * amount)
        g = round(int(c[2:4], 16) * amount)
        b = round(int(c[4:6], 16) * amount)
        return f'#{r:02x}{g:02x}{b:02x}'
    except ValueError:
        return hex_color


_TINT_PAIRS = [
    ("accent",        "heading-rule-color", 0.25),
    ("note-color",    "note-bg",            0.12),
    ("tip-color",     "tip-bg",             0.12),
    ("warning-color", "warning-bg",         0.15),
    ("danger-color",  "danger-bg",          0.15),
    ("info-color",    "info-bg",            0.12),
]

_CSS_FILE = Path(__file__).parent / "styles.css"
if not _CSS_FILE.exists():
    print(f"Error: styles.css not found at {_CSS_FILE}")
    sys.exit(1)
CSS = _CSS_FILE.read_text(encoding="utf-8")
_v = _parse_root_vars(CSS)
_tint_overrides = "".join(
    f"    --{bg}: {_tint(_v[color], pct)};\n"
    for color, bg, pct in _TINT_PAIRS
    if color in _v and _v[color].startswith('#')
)
_adm_code: list[str] = []
for _t in ["note", "tip", "warning", "danger", "info"]:
    _c = _v.get(f"{_t}-color", "")
    if _c.startswith('#'):
        _adm_code += [
            f"    --{_t}-code-bg:     {_tint(_c, 0.08)};",
            f"    --{_t}-code-border: {_tint(_c, 0.35)};",
            f"    --{_t}-code-text:   {_shade(_c, 0.58)};",
        ]
_computed = (_tint_overrides + "\n".join(_adm_code) + "\n") if _adm_code else _tint_overrides
if _computed.strip():
    CSS += f"\n:root {{\n{_computed}}}\n"

ADMONITIONS = {
    "note":    {"color": _v.get("note-color",    "#448aff"), "icon": lambda c: _icon(c, "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z")},
    "tip":     {"color": _v.get("tip-color",     "#00c853"), "icon": lambda c: _icon(c, "M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z")},
    "warning": {"color": _v.get("warning-color", "#ff9100"), "icon": lambda c: _icon(c, "M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z")},
    "danger":  {"color": _v.get("danger-color",  "#ff1744"), "icon": lambda c: _icon(c, "M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.59 12 17 15.59z")},
    "info":    {"color": _v.get("info-color",    "#00b0ff"), "icon": lambda c: _icon(c, "M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z")},
}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML-style frontmatter from top of markdown."""
    text = text.lstrip("\ufeff")  # strip UTF-8 BOM if present
    text = text.replace("\r\n", "\n").replace("\r", "\n")
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
    project_root = Path(__file__).parent
    if Path(path).is_absolute():
        img = Path(path)
    else:
        img = source_dir / path
    if not img.exists():
        # fall back to project root (e.g. logo stored at root /images/ but md is in docs/)
        img = project_root / path.lstrip("./")
    if not img.exists():
        print(f"Error: logo not found: {img}")
        sys.exit(1)
    data = base64.b64encode(img.read_bytes()).decode()
    suffix = img.suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "svg": "svg+xml", "webp": "webp"}.get(suffix, "png")
    return f"data:image/{mime};base64,{data}"


_BANNER_KEYS = {"logo", "author", "title", "subtitle", "revision", "date", "color", "stripe", "logo-height"}

def make_banner(meta: dict, source_dir: Path = Path(".")) -> str:
    """Render a cover banner from frontmatter metadata."""
    if not meta or not any(k in _BANNER_KEYS for k in meta):
        return ""
    logo     = meta.get("logo", "")
    author   = _html.escape(meta.get("author", ""))
    title    = _html.escape(meta.get("title", ""))
    subtitle = _html.escape(meta.get("subtitle", ""))
    revision = _html.escape(meta.get("revision", ""))
    _today   = _date.today()
    date     = _html.escape(meta.get("date") or f"{_today.strftime('%B')} {_today.day}, {_today.year}")
    color    = meta.get("color", "var(--accent)")
    stripe   = meta.get("stripe", "false")

    if stripe.lower() == "true":
        stripe_color = "rgba(255,255,255,0.25)"
    elif stripe.lower() == "false":
        stripe_color = None
    else:
        stripe_color = stripe

    stripe_style = f"border-left: 10px solid {stripe_color}; padding-left: 26px;" if stripe_color else ""

    meta_parts = " &nbsp;&nbsp; ".join(filter(None, [revision, date]))

    logo_height = meta.get("logo-height", "48px")

    if logo:
        top = f'<img src="{_embed_image(logo, source_dir)}" style="height:{logo_height};margin-bottom:12px;display:block;">'
    elif author:
        top = f'<div class="cover-author">{author}</div>'
    else:
        top = ""

    minimal = not logo and not author and not subtitle
    banner_class = "cover-banner cover-banner-minimal" if minimal else "cover-banner"

    return f"""
<div class="{banner_class}" style="background: {color}; {stripe_style}">
  {top}
  {"" if not title     else f'<div class="cover-title">{title}</div>'}
  {"" if not subtitle  else f'<div class="cover-subtitle">{subtitle}</div>'}
  {"" if not meta_parts else f'<div class="cover-meta">{meta_parts}</div>'}
</div>
"""


def _find_list_indent(lines: list[str], index: int) -> str:
    """Look backwards from index to detect if we're inside a list; return continuation indent or ''."""
    for j in range(index - 1, -1, -1):
        line = lines[j]
        if line.strip() == "":
            continue
        m = re.match(r'^(\s*)(\d+\.\s+|[-*+]\s+)', line)
        if m:
            # indent to continue inside this list item
            return m.group(1) + "  "
        # indented continuation of a list item - keep looking
        if line.startswith("    ") or line.startswith("\t"):
            continue
        break
    return ""


def preprocess_admonitions(text: str, md: MarkdownIt) -> tuple[str, dict]:
    """Replace ::: blocks with unique placeholders and return (text, map)."""
    lines = text.split("\n")
    result = []
    admonitions: dict = {}
    counter = 0
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        match = re.match(r'^:::(\w+)(!)?(?::\s+([^"]*?))?$', stripped)
        if match:
            own_indent = lines[i][: len(lines[i]) - len(lines[i].lstrip())]
            atype = match.group(1).lower()
            compact = match.group(2) == "!"
            title = match.group(3) or atype.capitalize()
            style = ADMONITIONS.get(atype, {
                "color": "#888888",
                "icon": lambda c: _icon(c, "M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7l5 5v11z"),
            })
            i += 1
            inner_lines = []
            while i < len(lines) and lines[i].strip() != ":::":
                inner_lines.append(lines[i])
                i += 1
            if i >= len(lines):
                print(f"Warning: unclosed admonition block ':::{atype}' - closing ':::' missing")
            else:
                i += 1  # skip the closing :::
            # strip the admonition's own indentation from inner lines
            # so markdown-it doesn't treat indented content as a code block
            if own_indent:
                inner_lines = [
                    l[len(own_indent):] if l.startswith(own_indent) else l
                    for l in inner_lines
                ]
            inner_html = md.render("\n".join(inner_lines))
            if compact:
                admonition_html = (
                    f'<div class="admonition {atype} admonition-compact">'
                    f'<span class="admonition-compact-icon">{style["icon"](style["color"])}</span>'
                    f'<div class="admonition-compact-body">{inner_html}</div>'
                    f'</div>'
                )
            else:
                admonition_html = (
                    f'<div class="admonition {atype}">'
                    f'<div class="admonition-title">{style["icon"](style["color"])} {title}</div>'
                    f'{inner_html}'
                    f'</div>'
                )
            placeholder = f"ADMONITION_PLACEHOLDER_{counter}"
            admonitions[placeholder] = admonition_html
            counter += 1
            # if at root level but inside a list, auto-indent to stay in the list
            indent = own_indent or _find_list_indent(result, len(result))
            result.append(indent + placeholder)
        else:
            result.append(lines[i])
            i += 1
    return "\n".join(result), admonitions


def restore_admonitions(html: str, admonitions: dict) -> str:
    """Swap admonition placeholders back into rendered HTML."""
    # Replace longest placeholders first to avoid partial matches
    # (e.g. PLACEHOLDER_1 matching inside PLACEHOLDER_10)
    for placeholder in sorted(admonitions, key=len, reverse=True):
        admonition_html = admonitions[placeholder]
        html = html.replace(f"<p>{placeholder}</p>", admonition_html)
        html = html.replace(placeholder, admonition_html)
    return html


def _embed_images_in_html(html: str, source_dir: Path) -> str:
    """Replace <img src> paths with base64 data URIs so WeasyPrint resolves them from any temp path."""
    project_root = Path(__file__).parent

    def replacer(m: re.Match) -> str:
        src = m.group(1)
        if src.startswith("data:") or src.startswith("http://") or src.startswith("https://"):
            return m.group(0)
        img = project_root / src.lstrip("/") if src.startswith("/") else source_dir / src
        if not img.exists():
            print(f"Warning: image not found, skipping embed: {img}")
            return m.group(0)
        data = base64.b64encode(img.read_bytes()).decode()
        suffix = img.suffix.lower().lstrip(".")
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "svg": "svg+xml", "webp": "webp"}.get(suffix, "png")
        return f'src="data:image/{mime};base64,{data}"'

    return re.sub(r'src="([^"]+)"', replacer, html)


def _process_tables(html: str, col_count: int, source_label: str = "") -> str:
    """Wrap tables; span all columns only when table is wider than a single column can fit."""
    def replacer(m: re.Match) -> str:
        table = m.group(0)
        headers = len(re.findall(r'<th[\s>]', table))
        # A table needs to span all layout columns when it has more columns
        # than a single layout column can reasonably fit (threshold: 4+)
        compact = headers > 5 or (col_count > 1 and headers > 3)
        tiny    = headers > 8 or (col_count >= 3 and headers > 4) or (col_count == 2 and headers > 6)
        classes = "table-wrap"
        if compact:
            classes += " table-compact"
        if tiny:
            classes += " table-tiny"
            label = f" ({source_label})" if source_label else ""
            print(f"Warning: table with {headers} columns{label} may overflow - applying compact styling")
        return f'<div class="{classes}">{table}</div>'

    return re.sub(r'<table>.*?</table>', replacer, html, flags=re.DOTALL)


def _highlight_code_blocks(html: str) -> str:
    if not _PYGMENTS:
        return html
    formatter = _HtmlFormatter(noclasses=True, nowrap=True, style="friendly")

    def replacer(m: re.Match) -> str:
        lang = (m.group(1) or "").strip().lower()
        code = _html.unescape(m.group(2))
        try:
            lexer = _get_lexer(lang) if lang else _TextLexer()
        except _ClassNotFound:
            lexer = _TextLexer()
        highlighted = _pyg_highlight(code, lexer, formatter)
        has_lang = lang and not isinstance(lexer, _TextLexer)
        if has_lang:
            badge = f'<span class="code-lang">{lexer.name}</span>'
            return f'<div class="code-block"><pre>{badge}<code>{highlighted}</code></pre></div>'
        return f'<div class="code-block"><pre><code>{highlighted}</code></pre></div>'

    return re.sub(
        r'<pre><code(?:\s+class="language-([^"]*)")?>(.*?)</code></pre>',
        replacer,
        html,
        flags=re.DOTALL,
    )


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
    text, admonition_map = preprocess_admonitions(text, md)
    banner = make_banner(meta, input_path.parent).strip()
    body = md.render(text).strip()
    body = restore_admonitions(body, admonition_map)
    body = _highlight_code_blocks(body)
    body = _embed_images_in_html(body, input_path.parent)
    body = re.sub(r'<(h[1-6]|p|ul|ol|pre|table|blockquote)\b',
                  r'<\1 style="margin-top:0"', body, count=1)
    columns = meta.get("columns", "").strip().lower()
    col_count = int("2" if columns == "true" else columns) if columns and columns not in ("false", "0", "1", "") else 1
    body = _process_tables(body, col_count, source_label=input_path.name)
    if col_count > 1:
        body = f'<div class="columns-layout" style="column-count:{col_count}">{body}</div>'
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