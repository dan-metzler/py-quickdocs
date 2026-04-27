import pytest

from main import _highlight_code_blocks, _PYGMENTS

pytestmark = pytest.mark.skipif(not _PYGMENTS, reason="Pygments not installed")


def _hl(lang: str, code: str) -> str:
    if lang:
        return f'<pre><code class="language-{lang}">{code}\n</code></pre>'
    return f"<pre><code>{code}\n</code></pre>"


# ── wrapping ───────────────────────────────────────────────────────────────

class TestWrapping:
    def test_code_block_wrapped_in_code_block_div(self):
        result = _highlight_code_blocks(_hl("", "x = 1"))
        assert 'class="code-block"' in result

    def test_multiple_blocks_all_wrapped(self):
        html = _hl("python", "x = 1") + "\n" + _hl("json", '{"a": 1}')
        result = _highlight_code_blocks(html)
        assert result.count('class="code-block"') == 2

    def test_passthrough_when_pygments_unavailable(self, monkeypatch):
        import main
        monkeypatch.setattr(main, "_PYGMENTS", False)
        html = _hl("python", "x = 1")
        result = main._highlight_code_blocks(html)
        assert result == html


# ── language badge ────────────────────────────────────────────────────────

class TestLanguageBadge:
    def test_badge_present_for_known_language(self):
        result = _highlight_code_blocks(_hl("python", "x = 1"))
        assert 'class="code-lang"' in result

    def test_badge_shows_lexer_name(self):
        result = _highlight_code_blocks(_hl("python", "x = 1"))
        assert "Python" in result

    def test_badge_for_json(self):
        result = _highlight_code_blocks(_hl("json", '{"key": "value"}'))
        assert 'class="code-lang"' in result

    def test_badge_for_bash(self):
        result = _highlight_code_blocks(_hl("bash", "echo hello"))
        assert 'class="code-lang"' in result

    def test_no_badge_for_unlabelled_block(self):
        result = _highlight_code_blocks(_hl("", "some code"))
        assert 'class="code-lang"' not in result

    def test_no_badge_for_unknown_language(self):
        result = _highlight_code_blocks(_hl("xyzunknown999", "code"))
        assert 'class="code-lang"' not in result

    def test_badge_inside_pre_element(self):
        result = _highlight_code_blocks(_hl("python", "x = 1"))
        pre_idx = result.index("<pre>")
        badge_idx = result.index('class="code-lang"')
        assert badge_idx > pre_idx


# ── highlighting output ───────────────────────────────────────────────────

class TestHighlightingOutput:
    def test_python_produces_colored_spans(self):
        result = _highlight_code_blocks(_hl("python", "import requests"))
        assert "<span" in result

    def test_html_entities_unescaped_before_highlight(self):
        result = _highlight_code_blocks(_hl("python", "x &lt; y"))
        # Raw entity sequence should be gone - Pygments received the real < char
        assert "x &lt; y" not in result
        assert "<span" in result  # highlighting was applied

    def test_multiline_code_preserves_newlines(self):
        code = "x = 1\ny = 2\nz = 3"
        result = _highlight_code_blocks(_hl("python", code))
        assert "x" in result and "y" in result and "z" in result

    def test_unlabelled_block_has_code_block_wrapper(self):
        result = _highlight_code_blocks(_hl("", "line1\nline2"))
        assert 'class="code-block"' in result

    def test_http_label_highlighted(self):
        result = _highlight_code_blocks(_hl("http", "GET /api HTTP/1.1"))
        assert "<span" in result


# ── entity handling ───────────────────────────────────────────────────────

class TestEntityHandling:
    def test_amp_entity_handled(self):
        result = _highlight_code_blocks(_hl("python", "a &amp; b"))
        assert "a &amp; b" not in result

    def test_lt_gt_handled(self):
        result = _highlight_code_blocks(_hl("python", "a &lt; b &gt; c"))
        assert "a &lt; b &gt; c" not in result
