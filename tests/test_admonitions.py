import pytest
from markdown_it import MarkdownIt

from main import preprocess_admonitions, restore_admonitions

md = MarkdownIt().enable("table")


def _adm_html(text: str) -> str:
    """Preprocess and return the first admonition's HTML."""
    _, admonitions = preprocess_admonitions(text, md)
    assert admonitions, "No admonitions found"
    return next(iter(admonitions.values()))


# ── basic types ───────────────────────────────────────────────────────────

class TestBasicTypes:
    @pytest.mark.parametrize("atype", ["note", "tip", "warning", "danger", "info"])
    def test_all_known_types_render(self, atype):
        html = _adm_html(f":::{atype}\ncontent\n:::")
        assert f'class="admonition {atype}"' in html

    @pytest.mark.parametrize("atype", ["note", "tip", "warning", "danger", "info"])
    def test_title_shows_type_name(self, atype):
        html = _adm_html(f":::{atype}\ncontent\n:::")
        assert atype.capitalize() in html or atype in html

    def test_content_rendered_in_html(self):
        html = _adm_html(":::note\nHello **world**\n:::")
        assert "Hello" in html
        assert "<strong>world</strong>" in html

    def test_unknown_type_uses_fallback_class(self):
        html = _adm_html(":::custom\ncontent\n:::")
        assert 'class="admonition custom"' in html

    def test_unknown_type_renders_content(self):
        html = _adm_html(":::custom\nsome text\n:::")
        assert "some text" in html


# ── compact mode ──────────────────────────────────────────────────────────

class TestCompactMode:
    def test_bang_triggers_compact(self):
        html = _adm_html(":::note!\nHello\n:::")
        assert "admonition-compact" in html

    def test_compact_has_no_title_div(self):
        html = _adm_html(":::note!\nHello\n:::")
        assert "admonition-title" not in html

    def test_compact_has_icon_span(self):
        html = _adm_html(":::note!\nHello\n:::")
        assert "admonition-compact-icon" in html

    def test_compact_has_body_div(self):
        html = _adm_html(":::note!\nHello\n:::")
        assert "admonition-compact-body" in html

    def test_all_types_support_compact(self):
        for t in ["note", "tip", "warning", "danger", "info"]:
            html = _adm_html(f":::{t}!\ncontent\n:::")
            assert "admonition-compact" in html


# ── custom title ──────────────────────────────────────────────────────────

class TestCustomTitle:
    def test_custom_title_rendered(self):
        html = _adm_html(":::note: My Custom Title\ncontent\n:::")
        assert "My Custom Title" in html

    def test_custom_title_replaces_default(self):
        html = _adm_html(":::warning: Pay Attention\ncontent\n:::")
        assert "Pay Attention" in html
        assert "Warning" not in html

    def test_custom_title_with_spaces(self):
        html = _adm_html(":::tip: Pro Tip Here\ncontent\n:::")
        assert "Pro Tip Here" in html


# ── placeholder mechanics ─────────────────────────────────────────────────

class TestPlaceholders:
    def test_placeholder_in_result_text(self):
        result, admonitions = preprocess_admonitions(":::note\ntest\n:::", md)
        assert len(admonitions) == 1
        assert "ADMONITION_PLACEHOLDER_0" in result

    def test_closing_marker_consumed(self):
        result, _ = preprocess_admonitions(":::tip\nHello\n:::\n\nMore text", md)
        assert ":::" not in result

    def test_multiple_admonitions(self):
        text = ":::note\nfirst\n:::\n\n:::tip\nsecond\n:::"
        result, admonitions = preprocess_admonitions(text, md)
        assert len(admonitions) == 2
        assert "ADMONITION_PLACEHOLDER_0" in result
        assert "ADMONITION_PLACEHOLDER_1" in result

    def test_unclosed_admonition_no_crash(self, capsys):
        text = ":::note\nunclosed content"
        result, admonitions = preprocess_admonitions(text, md)
        assert len(admonitions) == 1
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_unclosed_admonition_content_rendered(self, capsys):
        text = ":::note\nHello world"
        _, admonitions = preprocess_admonitions(text, md)
        html = next(iter(admonitions.values()))
        assert "Hello world" in html

    def test_empty_admonition_block(self):
        text = ":::note\n:::"
        _, admonitions = preprocess_admonitions(text, md)
        assert len(admonitions) == 1
        html = next(iter(admonitions.values()))
        assert 'class="admonition note"' in html

    def test_counter_increments_per_admonition(self):
        text = ":::note\na\n:::\n:::tip\nb\n:::\n:::warning\nc\n:::"
        _, admonitions = preprocess_admonitions(text, md)
        keys = list(admonitions.keys())
        assert "ADMONITION_PLACEHOLDER_0" in keys
        assert "ADMONITION_PLACEHOLDER_1" in keys
        assert "ADMONITION_PLACEHOLDER_2" in keys


# ── list indentation ──────────────────────────────────────────────────────

class TestListIndentation:
    def test_admonition_inside_ordered_list(self):
        text = "1. First\n   :::tip\n   A tip\n   :::\n2. Second"
        result, admonitions = preprocess_admonitions(text, md)
        assert len(admonitions) == 1
        placeholder_line = next(l for l in result.split("\n") if "PLACEHOLDER" in l)
        assert placeholder_line.startswith(" ")

    def test_admonition_inside_unordered_list(self):
        text = "- Item\n   :::note\n   A note\n   :::\n- Other"
        result, admonitions = preprocess_admonitions(text, md)
        assert len(admonitions) == 1

    def test_own_indent_used_when_present(self):
        text = "   :::warning\n   Watch out\n   :::"
        result, admonitions = preprocess_admonitions(text, md)
        placeholder_line = next(l for l in result.split("\n") if "PLACEHOLDER" in l)
        assert placeholder_line.startswith("   ")


# ── restore ───────────────────────────────────────────────────────────────

class TestRestoreAdmonitions:
    def test_single_placeholder_replaced(self):
        admonitions = {"ADMONITION_PLACEHOLDER_0": "<div>test</div>"}
        html = "<p>ADMONITION_PLACEHOLDER_0</p>"
        result = restore_admonitions(html, admonitions)
        assert "<div>test</div>" in result
        assert "ADMONITION_PLACEHOLDER_0" not in result

    def test_raw_placeholder_also_replaced(self):
        admonitions = {"ADMONITION_PLACEHOLDER_0": "<div>test</div>"}
        html = "ADMONITION_PLACEHOLDER_0"
        result = restore_admonitions(html, admonitions)
        assert "<div>test</div>" in result

    def test_multiple_placeholders_all_replaced(self):
        admonitions = {
            "ADMONITION_PLACEHOLDER_0": "<div>first</div>",
            "ADMONITION_PLACEHOLDER_1": "<div>second</div>",
        }
        html = "<p>ADMONITION_PLACEHOLDER_0</p><p>ADMONITION_PLACEHOLDER_1</p>"
        result = restore_admonitions(html, admonitions)
        assert "<div>first</div>" in result
        assert "<div>second</div>" in result
        assert "PLACEHOLDER" not in result

    def test_no_placeholders_returns_unchanged(self):
        html = "<p>No placeholders here</p>"
        result = restore_admonitions(html, {})
        assert result == html

    def test_longer_placeholders_replaced_first(self):
        admonitions = {
            "ADMONITION_PLACEHOLDER_1": "<div>one</div>",
            "ADMONITION_PLACEHOLDER_10": "<div>ten</div>",
        }
        html = "<p>ADMONITION_PLACEHOLDER_10</p><p>ADMONITION_PLACEHOLDER_1</p>"
        result = restore_admonitions(html, admonitions)
        assert "<div>ten</div>" in result
        assert "<div>one</div>" in result
        assert "PLACEHOLDER" not in result
