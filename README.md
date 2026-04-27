# pymarkdown

[![Build](https://github.com/dan-metzler/pymarkdown/actions/workflows/test.yml/badge.svg)](https://github.com/dan-metzler/pymarkdown/actions/workflows/test.yml) [![Tests](https://img.shields.io/badge/tests-188%20passing-brightgreen)](#)

Converts Markdown files to styled PDFs. Supports cover banners, themes, admonition blocks, syntax-highlighted code, columns layout, images, and custom logos - all driven from Markdown and a single CSS file.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) or pip
- `weasyprint.exe` in the project root (included)

## Getting started

```bash
# Single file - output goes to output/yourfile.pdf
uv run main.py docs/yourfile.md

# Custom output path
uv run main.py docs/yourfile.md path/to/output.pdf

# Convert all files in docs/ at once
uv run convert_all.py
```

With pip instead of uv, replace `uv run` with `python`.

---

## Frontmatter

Add a frontmatter block at the top of any Markdown file to control the cover banner. All fields are optional. Omitting all banner fields skips the banner entirely.

```yaml
---
author: Acme Corp
title: Getting Started with the API
subtitle: A quick guide for new users
revision: v2.1
date: April 26, 2026
logo: images/logo.png
logo-height: 48px
color: #00338D
stripe: true
columns: true
---
```

| Field | Description |
|---|---|
| `author` | Small label above the title - person, team, org, or company name |
| `title` | Large heading on the banner |
| `subtitle` | Smaller line below the title |
| `revision` | Shown in the banner footer - version, edition, draft label, etc. |
| `date` | Shown next to revision. Omit to use today's date automatically. |
| `logo` | Path to an image (PNG, JPG, SVG, WEBP) - replaces the author label |
| `logo-height` | Height of the logo image, defaults to `48px` |
| `color` | Banner background color - any CSS color. Defaults to `--accent` from the active theme |
| `stripe` | Left border on the banner. `true` for a white overlay, `false` to disable, or any CSS color |
| `columns` | `true` or a number (e.g. `2`, `3`) for multi-column layout. Omit for single column |

**Banner variants:** a banner with only `title` and `date` renders as a slim horizontal bar. Add `author`, `subtitle`, or `logo` for the full banner with larger type.

---

## Admonitions

Wrap content in a typed block to get a styled callout box. Five types: `note`, `tip`, `warning`, `danger`, `info`.

```
:::note
Informational callout.
:::

:::tip
Helpful suggestion.
:::

:::warning
Something to be careful about.
:::

:::danger
Critical - action required.
:::

:::info
Reference or supplementary detail.
:::
```

**Custom title** - add `: Title text` after the type:

```
:::warning: Check before deploying
Something important here.
:::
```

**Compact mode** - add `!` after the type to render the icon inline with the text, no title bar:

```
:::note!
Compact callout - icon sits inline with the text. Saves vertical space.
:::
```

**Inside lists** - indent admonitions to keep them inside a list item:

```markdown
1. First step
   :::tip
   Use a virtual environment.
   :::
2. Second step
```

All Markdown inside an admonition renders normally - bold, inline code, links, and nested lists all work. Inline code inside an admonition automatically inherits a tinted color scheme matching the admonition type.

---

## Syntax highlighting

Code blocks are automatically syntax-highlighted using Pygments. Specify the language after the opening fence:

````markdown
```python
import requests
response = requests.get(url, headers=headers)
```
````

A language badge appears in the top-right corner of the code block when a language is specified. Supported languages include `python`, `javascript`, `json`, `bash`, `http`, `sql`, `yaml`, and [any other Pygments lexer](https://pygments.org/languages/). Unlabelled blocks render without highlighting or badge.

---

## Columns

Set `columns: true` in frontmatter for a two-column layout. Use a number for more columns:

```yaml
columns: true   # two columns
columns: 3      # three columns
```

Tables and wide code blocks automatically span both columns. Headings flow inline with content so text fills columns continuously before moving to the next.

---

## Themes

All colors, fonts, spacing, and margins are controlled by CSS custom properties at the top of `styles.css`. Change the variables once and everything updates.

```css
:root {
    --font-body:    Georgia, 'Times New Roman', serif;
    --font-heading: Arial, Helvetica, sans-serif;

    --accent:      #003388;   /* headings and default banner color */
    --link:        #0091DA;
    --code-bg:     #edf1fb;
    --code-border: #c9d4ef;
    --code-text:   #1a2e6b;

    --note-color:    #448aff;
    --tip-color:     #00c853;
    --warning-color: #ff9100;
    --danger-color:  #ff1744;
    --info-color:    #00b0ff;

    --text:        #1a1a1a;
    --border:      #dde3ec;
    --surface:     #f6f8fa;
    --page-margin: 0.5cm;
}
```

Two alternative themes are included as commented blocks in `styles.css` - **Slate** (gray/indigo) and **Teal** (green). Uncomment one to activate it. Because CSS cascades, later `:root` blocks override earlier ones - you only need to list the variables you want to change:

```css
:root {
    --accent:      #1b3a5c;
    --link:        #2e7dbe;
    --code-bg:     #eef3f8;
    --code-border: #b8cfe0;
    --code-text:   #1b3a5c;
}
```

Admonition background colors (`--note-bg`, `--danger-bg`, etc.) are computed automatically from their primary color at generation time - you only need to set the primary color. Icon fill colors are also read from CSS variables at generation time, so switching themes updates icons, borders, and backgrounds with no Python edits needed.

**Custom fonts** - add a `@font-face` declaration and override the font variables:

```css
@font-face {
    font-family: 'Inter';
    src: url('C:/fonts/Inter-Regular.ttf');
}

:root {
    --font-body: 'Inter', sans-serif;
}
```

---

## Images

```markdown
![Alt text](images/diagram.png)
![Remote](https://example.com/image.png)
```

**Local images** are embedded as base64 data URIs - the PDF is fully self-contained. Paths resolve relative to the Markdown file's directory.

**Remote images** (`https://`) are fetched by WeasyPrint at generation time. An internet connection is required; the image is not embedded.

---

## Print readiness

The following are applied automatically:

- `orphans` and `widows` set to 3 - no isolated lines at page breaks
- `page-break-after: avoid` on all headings
- `page-break-inside: avoid` on images, code blocks, tables, and admonitions
- Table headers repeat on every page for multi-page tables
- Page numbers in the bottom-right corner of every page (`--page-num` controls the color)
