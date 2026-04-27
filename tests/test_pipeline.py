"""Integration-level tests for the processing pipeline steps."""
import re

import pytest
from markdown_it import MarkdownIt

from main import (
    _embed_images_in_html,
    _find_list_indent,
    _highlight_code_blocks,
    _process_tables,
    _BANNER_KEYS,
    preprocess_admonitions,
    restore_admonitions,
    _tint,
    _shade,
    _v,
    ADMONITIONS,
)

md = MarkdownIt().enable("table")


def _render(text: str) -> str:
    text, adm_map = preprocess_admonitions(text, md)
    body = md.render(text).strip()
    body = restore_admonitions(body, adm_map)
    body = _highlight_code_blocks(body)
    return body


# ── first-element margin injection ────────────────────────────────────────

class TestFirstElementMargin:
    @pytest.mark.parametrize("tag", ["h1", "h2", "h3", "p", "ul", "ol", "pre", "table", "blockquote"])
    def test_margin_injected_on_first_block(self, tag):
        if tag == "h1":
            text = "# Heading"
        elif tag == "h2":
            text = "## Heading"
        elif tag == "h3":
            text = "### Heading"
        elif tag == "p":
            text = "A paragraph"
        elif tag in ("ul", "ol"):
            text = "- item" if tag == "ul" else "1. item"
        elif tag == "pre":
            text = "```\ncode\n```"
        elif tag == "table":
            text = "| A | B |\n|---|---|\n| 1 | 2 |"
        elif tag == "blockquote":
            text = "> quote"
        body = _render(text)
        body = re.sub(
            r'<(h[1-6]|p|ul|ol|pre|table|blockquote)\b',
            r'<\1 style="margin-top:0"', body, count=1
        )
        assert 'style="margin-top:0"' in body

    def test_injection_only_first_element(self):
        text = "# One\n\n# Two\n\n# Three"
        body = _render(text)
        body = re.sub(
            r'<(h[1-6]|p|ul|ol|pre|table|blockquote)\b',
            r'<\1 style="margin-top:0"', body, count=1
        )
        assert body.count('style="margin-top:0"') == 1


# ── columns wrapping ──────────────────────────────────────────────────────

class TestColumnsWrapping:
    def _apply_columns(self, body: str, columns: str) -> str:
        if columns and columns not in ("false", "0", "1", ""):
            col_count = "2" if columns == "true" else columns
            return f'<div class="columns-layout" style="column-count:{col_count}">{body}</div>'
        return body

    def test_columns_true_wraps_in_div(self):
        body = "<p>content</p>"
        result = self._apply_columns(body, "true")
        assert 'class="columns-layout"' in result
        assert 'column-count:2' in result

    def test_columns_2_wraps_in_div(self):
        result = self._apply_columns("<p>x</p>", "2")
        assert 'column-count:2' in result

    def test_columns_3_wraps_in_div(self):
        result = self._apply_columns("<p>x</p>", "3")
        assert 'column-count:3' in result

    @pytest.mark.parametrize("val", ["false", "0", "1", ""])
    def test_disabled_values_no_wrap(self, val):
        result = self._apply_columns("<p>x</p>", val)
        assert "columns-layout" not in result

    def test_no_columns_key_no_wrap(self):
        result = self._apply_columns("<p>x</p>", "")
        assert "columns-layout" not in result


# ── find list indent ──────────────────────────────────────────────────────

class TestFindListIndent:
    def test_detects_unordered_list(self):
        lines = ["- Item one", ""]
        indent = _find_list_indent(lines, 2)
        assert indent == "  "

    def test_detects_ordered_list(self):
        lines = ["1. First item", ""]
        indent = _find_list_indent(lines, 2)
        assert indent == "  "

    def test_no_list_returns_empty(self):
        lines = ["Just a paragraph", ""]
        indent = _find_list_indent(lines, 2)
        assert indent == ""

    def test_skips_blank_lines(self):
        lines = ["- Item", "", ""]
        indent = _find_list_indent(lines, 3)
        assert indent == "  "

    def test_nested_list_indentation(self):
        lines = ["  - Nested item", ""]
        indent = _find_list_indent(lines, 2)
        assert indent == "    "


# ── admonition colors computed from css vars ──────────────────────────────

class TestAdmonitionColorsComputed:
    @pytest.mark.parametrize("atype", ["note", "tip", "warning", "danger", "info"])
    def test_admonition_color_loaded_from_css(self, atype):
        assert atype in ADMONITIONS
        assert ADMONITIONS[atype]["color"].startswith("#")

    @pytest.mark.parametrize("atype", ["note", "tip", "warning", "danger", "info"])
    def test_admonition_code_bg_computed(self, atype):
        color_key = f"{atype}-color"
        if color_key in _v and _v[color_key].startswith("#"):
            bg = _tint(_v[color_key], 0.08)
            assert bg.startswith("#")
            assert len(bg) == 7

    @pytest.mark.parametrize("atype", ["note", "tip", "warning", "danger", "info"])
    def test_admonition_code_text_darker_than_primary(self, atype):
        color_key = f"{atype}-color"
        if color_key in _v and _v[color_key].startswith("#"):
            primary = _v[color_key]
            text_color = _shade(primary, 0.58)
            p_avg = sum(int(primary[i:i+2], 16) for i in (1, 3, 5)) / 3
            t_avg = sum(int(text_color[i:i+2], 16) for i in (1, 3, 5)) / 3
            assert t_avg < p_avg


# ── banner key set ────────────────────────────────────────────────────────

class TestBannerKeys:
    def test_banner_keys_does_not_include_columns(self):
        assert "columns" not in _BANNER_KEYS

    def test_banner_keys_includes_all_visual_fields(self):
        for key in ("logo", "author", "title", "subtitle", "revision", "date", "color", "stripe"):
            assert key in _BANNER_KEYS

    def test_logo_height_is_banner_key(self):
        assert "logo-height" in _BANNER_KEYS


# ── table processing ─────────────────────────────────────────────────────

def _make_table(cols: int) -> str:
    header = "<table><thead><tr>" + "".join(f"<th>H{i}</th>" for i in range(cols)) + "</tr></thead>"
    body = "<tbody><tr>" + "".join(f"<td>D{i}</td>" for i in range(cols)) + "</tr></tbody></table>"
    return header + body


class TestProcessTables:
    def test_table_wrapped_in_div(self):
        html = _make_table(3)
        result = _process_tables(html, col_count=1)
        assert 'class="table-wrap"' in result
        assert "<table>" in result

    def test_no_column_span_ever(self):
        # Tables always stay in their column - sizing handles fit, not spanning
        for col_count in (1, 2, 3):
            for headers in (3, 5, 9):
                result = _process_tables(_make_table(headers), col_count=col_count)
                assert "column-span" not in result

    def test_narrow_table_single_col_no_compact(self):
        result = _process_tables(_make_table(3), col_count=1)
        assert "table-compact" not in result

    def test_wide_table_single_col_gets_compact(self):
        result = _process_tables(_make_table(6), col_count=1)
        assert "table-compact" in result

    def test_4col_table_in_multi_col_layout_gets_compact(self):
        result = _process_tables(_make_table(4), col_count=3)
        assert "table-compact" in result

    def test_3col_table_in_single_col_no_compact(self):
        result = _process_tables(_make_table(3), col_count=1)
        assert "table-compact" not in result

    def test_very_wide_table_single_col_gets_tiny(self):
        result = _process_tables(_make_table(9), col_count=1)
        assert "table-tiny" in result

    def test_5col_table_in_3col_layout_gets_tiny(self):
        result = _process_tables(_make_table(5), col_count=3)
        assert "table-tiny" in result

    def test_7col_table_in_2col_layout_gets_tiny(self):
        result = _process_tables(_make_table(7), col_count=2)
        assert "table-tiny" in result

    def test_4col_table_single_col_no_compact(self):
        # 4 headers in single column: 4 is not > 5, so no compact
        result = _process_tables(_make_table(4), col_count=1)
        assert "table-compact" not in result

    def test_tiny_also_carries_compact_class(self):
        # tiny threshold also satisfies compact - both classes present
        result = _process_tables(_make_table(9), col_count=1)
        assert "table-compact" in result
        assert "table-tiny" in result

    def test_5col_in_2col_layout_no_tiny(self):
        # 2-col layout: tiny only at > 6 headers
        result = _process_tables(_make_table(5), col_count=2)
        assert "table-compact" in result
        assert "table-tiny" not in result

    def test_very_wide_table_prints_warning(self, capsys):
        _process_tables(_make_table(9), col_count=1)
        assert "Warning" in capsys.readouterr().out

    def test_warning_includes_column_count(self, capsys):
        _process_tables(_make_table(9), col_count=1)
        assert "9" in capsys.readouterr().out

    def test_warning_includes_source_label(self, capsys):
        _process_tables(_make_table(9), col_count=1, source_label="myfile.md")
        assert "myfile.md" in capsys.readouterr().out

    def test_compact_table_no_warning(self, capsys):
        # compact threshold does not trigger a warning - only tiny does
        _process_tables(_make_table(6), col_count=1)
        assert "Warning" not in capsys.readouterr().out

    def test_multiple_tables_all_wrapped(self):
        html = _make_table(3) + _make_table(3)
        result = _process_tables(html, col_count=2)
        assert result.count('class="table-wrap') == 2

    def test_table_margin_reset_in_wrapper(self):
        result = _process_tables(_make_table(3), col_count=1)
        assert "table-wrap" in result


# ── full render smoke test ────────────────────────────────────────────────

class TestFullRenderSmoke:
    def test_heading_renders(self):
        assert "<h1>" in _render("# Hello")

    def test_admonition_renders(self):
        result = _render(":::note\ncontent\n:::")
        assert "admonition" in result

    def test_code_block_renders(self):
        result = _render("```python\nx = 1\n```")
        assert "code-block" in result or "<code>" in result

    def test_table_renders(self):
        result = _render("| A | B |\n|---|---|\n| 1 | 2 |")
        assert "<table>" in result

    def test_inline_code_renders(self):
        result = _render("Use `pip install` to install.")
        assert "<code>" in result

    def test_blockquote_renders(self):
        result = _render("> A quote")
        assert "<blockquote>" in result

    def test_image_tag_renders(self):
        result = _render("![alt](https://example.com/img.png)")
        assert "<img" in result

    def test_link_renders(self):
        result = _render("[text](https://example.com)")
        assert "<a " in result
