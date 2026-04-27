---
author: pymarkdown
title: Feature Showcase
subtitle: Markdown to PDF - banners, themes, admonitions, syntax highlighting, columns, and more
revision: v1.0
stripe: true
---

# Feature Showcase

This document demonstrates the full feature set of **pymarkdown** - a Markdown to PDF converter driven entirely from Markdown and a single CSS file. Everything you see here is generated from plain Markdown.

---

## Cover Banners

The banner at the top of this document is controlled by frontmatter. Fields include `author`, `title`, `subtitle`, `revision`, `date`, `logo`, `color`, and `stripe`. All fields are optional - omit them all to skip the banner entirely. The date defaults to today if not specified.

A banner with only a `title` and `date` renders as a slim horizontal bar. Add `author`, `subtitle`, or `logo` for the full banner with large type.

---

## Admonitions

Five callout types are available. Each has a distinct color, icon, and background tinted automatically from its primary color.

:::note
**Note** - informational callout. Use for context or background that the reader should be aware of.
:::

:::tip
**Tip** - helpful suggestion. Use for shortcuts, best practices, or things that make life easier. Inline code like `pip install pymarkdown` inherits the tip color scheme automatically.
:::

:::warning
**Warning** - something to be careful about. Use when incorrect action could cause problems.
:::

:::danger
**Danger** - critical callout. Use for breaking changes, data loss risks, or anything requiring immediate attention.
:::

:::info
**Info** - reference or supplementary detail. Use for links, related reading, or secondary context.
:::

### Compact Mode

Add `!` after the type for an inline layout - the icon sits beside the text with no title bar. Useful for short callouts that don't need the visual weight of a full box.

:::tip!
Compact admonitions save vertical space and work well for brief notes that would feel oversized as a full callout.
:::

:::warning!
Never commit `.env` files or API keys to version control.
:::

### Custom Titles

Add `: Title text` after the type to override the default title:

:::danger: Breaking Change in v2
The `data.results` field was renamed to `data.items`. Clients on v1.x will receive empty arrays with no error until updated.
:::

### Admonitions Inside Lists

Indent an admonition inside a list item to keep it in context with its step:

1. **Generate an API key** from the dashboard under `Settings > API Keys`
   :::tip
   Use a *Secret* key for backend services. Use *Public* keys only for browser-facing clients.
   :::
2. **Set your environment variable:**
   ```bash
   export API_KEY="your_key_here"
   ```
   :::warning
   Never hardcode credentials in source files. Use environment variables or a secrets manager.
   :::
3. **Verify connectivity** with a health check before writing integration code

---

## Syntax Highlighting

Code blocks are automatically highlighted using Pygments. A language badge appears in the top-right corner of each block.

**Python:**
```python
import requests

def fetch_data(api_key: str, endpoint: str) -> dict:
    response = requests.get(
        f"https://api.example.com/v1/{endpoint}",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
```

**HTTP request:**
```http
GET /api/v1/data HTTP/1.1
Host: api.example.com
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

**JSON response:**
```json
{
  "data": {
    "id": "abc123",
    "status": "active",
    "items": [1, 2, 3]
  },
  "meta": {
    "request_id": "req_9xKp2m",
    "took_ms": 42
  }
}
```

**Bash:**
```bash
# Install dependencies
uv sync

# Convert a single file
uv run main.py docs/example.md

# Convert all files in docs/
uv run convert_all.py
```

---

## Tables

Tables render with alternating row colors and a header background, both controlled by `--surface` and `--surface-alt` in the theme.

| Feature | Frontmatter Key | Default |
|---|---|---|
| Banner color | `color` | `--accent` from theme |
| Page margin | `--page-margin` in CSS | `0.5cm` |
| Logo height | `logo-height` | `48px` |
| Columns | `columns` | off |
| Date | `date` | today (auto) |

---

## Inline Formatting

Text supports the full Markdown inline set: **bold**, *italic*, ~~strikethrough~~, `inline code`, and [hyperlinks](https://example.com). Inline code outside admonitions uses the theme's `--code-bg`, `--code-border`, and `--code-text` variables.

> Blockquotes render with a left border in `--border` color and muted text. Use them for pull quotes, external references, or technical notes that should stand apart from the main flow.

---

## Images

Local images are embedded as base64 data URIs, making the PDF fully self-contained. Remote images are fetched at generation time.

![Remote image - fetched at generation time](https://picsum.photos/seed/pymarkdown/900/220)

---

## Columns Layout

Set `columns: true` in frontmatter for a two-column layout. Content flows left column to right column continuously. Tables and wide code blocks automatically span both columns. Headings flow inline with content so sections don't reset the column context.

Use `columns: 3` for three columns. Best suited for reference documents, release notes, and dense content where vertical space matters.

---

## Themes

Everything visual is controlled by CSS custom properties in the `THEME` block at the top of `styles.css`. Change `--accent` and the related code/admonition colors update throughout the document.

Two alternative themes are included - **Slate** (gray/indigo) and **Teal** (green). Uncomment either `:root` block in `styles.css` to activate it. Admonition background tints and heading rule colors are computed automatically from the primary colors at generation time - no manual hex values required.

---

## Print Readiness

The following are applied to every generated PDF automatically:

- `orphans` and `widows` set to 3 - no isolated lines at page breaks
- `page-break-after: avoid` on all headings
- `page-break-inside: avoid` on images, code blocks, admonitions, and table rows
- Table headers repeat across pages for multi-page tables
- Page numbers in the bottom-right corner of every page
