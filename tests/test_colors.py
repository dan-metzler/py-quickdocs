from main import _tint, _shade, _parse_root_vars


# ── _tint ──────────────────────────────────────────────────────────────────

class TestTint:
    def test_amount_zero_returns_white(self):
        assert _tint("#000000", 0.0) == "#ffffff"

    def test_amount_one_returns_original(self):
        assert _tint("#ff0000", 1.0) == "#ff0000"

    def test_partial_blend(self):
        result = _tint("#000000", 0.5)
        # 50% black + 50% white → #7f7f7f (rounding may give 7f or 80)
        assert result in ("#7f7f7f", "#808080")

    def test_three_digit_hex_expanded(self):
        assert _tint("#f00", 1.0) == _tint("#ff0000", 1.0)

    def test_three_digit_tint_matches_six_digit(self):
        assert _tint("#abc", 0.5) == _tint("#aabbcc", 0.5)

    def test_non_hex_string_returned_as_is(self):
        assert _tint("red", 0.5) == "red"

    def test_invalid_hex_returned_as_is(self):
        assert _tint("#zzzzzz", 0.5) == "#zzzzzz"

    def test_three_digit_expands_and_tints(self):
        # 3-digit hex is valid and gets expanded before tinting
        assert _tint("#123", 0.5) != "#123"
        assert _tint("#123", 0.5) == _tint("#112233", 0.5)

    def test_five_digit_returned_as_is(self):
        assert _tint("#12345", 0.5) == "#12345"

    def test_result_is_six_digit_hex(self):
        result = _tint("#448aff", 0.12)
        assert result.startswith("#")
        assert len(result) == 7

    def test_blue_tint(self):
        result = _tint("#0000ff", 0.5)
        r, g, b = int(result[1:3], 16), int(result[3:5], 16), int(result[5:7], 16)
        assert b > r and b > g  # still blue-dominant


# ── _shade ─────────────────────────────────────────────────────────────────

class TestShade:
    def test_amount_zero_returns_black(self):
        assert _shade("#ffffff", 0.0) == "#000000"

    def test_amount_one_returns_original(self):
        assert _shade("#ff0000", 1.0) == "#ff0000"

    def test_partial_shade(self):
        result = _shade("#ffffff", 0.5)
        assert result in ("#7f7f7f", "#808080")

    def test_three_digit_hex_expanded(self):
        assert _shade("#fff", 0.5) == _shade("#ffffff", 0.5)

    def test_non_hex_returned_as_is(self):
        assert _shade("blue", 0.5) == "blue"

    def test_result_is_six_digit_hex(self):
        result = _shade("#448aff", 0.58)
        assert result.startswith("#")
        assert len(result) == 7

    def test_darkens_color(self):
        original = "#448aff"
        shaded = _shade(original, 0.5)
        orig_avg = (0x44 + 0x8a + 0xff) / 3
        r, g, b = int(shaded[1:3], 16), int(shaded[3:5], 16), int(shaded[5:7], 16)
        assert (r + g + b) / 3 < orig_avg


# ── _parse_root_vars ───────────────────────────────────────────────────────

class TestParseRootVars:
    def test_basic_extraction(self):
        css = ":root { --accent: #003388; --link: #0091DA; }"
        v = _parse_root_vars(css)
        assert v["accent"] == "#003388"
        assert v["link"] == "#0091DA"

    def test_later_block_overrides_earlier(self):
        css = ":root { --accent: #003388; }\n:root { --accent: #00695c; }"
        v = _parse_root_vars(css)
        assert v["accent"] == "#00695c"

    def test_comments_stripped_before_parsing(self):
        css = "/* :root { --accent: #ff0000; } */\n:root { --accent: #003388; }"
        v = _parse_root_vars(css)
        assert v["accent"] == "#003388"

    def test_multiline_root_block(self):
        css = ":root {\n    --accent: #003388;\n    --link: #0091DA;\n}"
        v = _parse_root_vars(css)
        assert v["accent"] == "#003388"
        assert v["link"] == "#0091DA"

    def test_color_mix_value_captured_as_string(self):
        css = ":root { --note-bg: color-mix(in srgb, #448aff 12%, white); }"
        v = _parse_root_vars(css)
        assert "color-mix" in v.get("note-bg", "")

    def test_empty_css_returns_empty_dict(self):
        assert _parse_root_vars("") == {}

    def test_no_root_block_returns_empty(self):
        css = "body { color: red; }"
        assert _parse_root_vars(css) == {}

    def test_var_with_spaces_trimmed(self):
        css = ":root { --page-margin:   2cm  ; }"
        v = _parse_root_vars(css)
        assert v["page-margin"] == "2cm"

    def test_font_variable_captured(self):
        css = ":root { --font-body: Georgia, 'Times New Roman', serif; }"
        v = _parse_root_vars(css)
        assert "Georgia" in v.get("font-body", "")
