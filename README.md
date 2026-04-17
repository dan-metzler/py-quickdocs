# pymarkdown

Converts markdown files into styled PDFs. Supports cover banners, admonition blocks, tables, code blocks and custom logos via frontmatter. Good for internal docs, user guides, anything you'd otherwise manage as a Word or PDF file manually.

## What you need

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) or just pip
- `weasyprint.exe` placed in the root of this project (already included)

## Getting started

With uv:
```bash
uv sync
uv run main.py docs/yourfile.md
```

With pip:
```bash
pip install -r requirements.txt
python main.py docs/yourfile.md
```

Output goes to the `output/` folder automatically. You can also pass a custom output path:
```bash
uv run main.py docs/yourfile.md some/other/place.pdf
```

## Frontmatter

At the top of any markdown file you can add a frontmatter block to control the cover banner. All fields are optional.

```yaml
---
title: Getting Started with the API
subtitle: A quick guide for new users
company: Acme Corp
logo: ./assets/logo.png
logo-height: 48px
color: #00338D
stripe: true
version: v2.1
date: April 2026
---
```

| Field | What it does |
|---|---|
| `title` | Large heading on the banner |
| `subtitle` | Smaller line below the title |
| `company` | Small label above the title |
| `logo` | Image instead of company text (PNG, JPG, SVG, WEBP) |
| `logo-height` | Height of the logo, defaults to `48px` |
| `color` | Banner background color, any CSS color value |
| `stripe` | Left side stripe, use `true` for default blue, `false` to disable, or a hex code for a custom color |
| `version` | Shows in the bottom of the banner, e.g. `v2.1` |
| `date` | Shows next to version, e.g. `April 2026` |

If both `logo` and `company` are set, logo takes priority.

## Admonitions

Wrap any content in a typed block to get a styled callout box:

```
:::note
This is a note.
:::

:::tip
This is a tip.
:::

:::warning
This is a warning.
:::

:::danger
This is a danger callout.
:::

:::info
This is an info block.
:::
```

You can also give a block a custom title:

```
:::warning "Check this before deploying"
Something important here.
:::
```

Markdown inside admonition blocks works normally, so bold, inline code, links etc. all render correctly.

## Styling

All styles live in `styles.css` next to `main.py`. Edit that file to change fonts, spacing, colors, margins and so on. No need to touch the Python code for visual changes.

To use a custom font, add it to `styles.css` with `@font-face`:

```css
@font-face {
    font-family: 'Inter';
    src: url('C:/fonts/Inter-Regular.ttf');
}

body {
    font-family: 'Inter', sans-serif;
}
```
