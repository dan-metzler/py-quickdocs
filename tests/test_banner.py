from datetime import date
from pathlib import Path

import pytest

from main import make_banner, _BANNER_KEYS


SOURCE = Path(".")


# ── no banner ──────────────────────────────────────────────────────────────

def test_empty_meta_returns_empty():
    assert make_banner({}) == ""


def test_non_banner_keys_only_returns_empty():
    assert make_banner({"columns": "true"}) == ""
    assert make_banner({"columns": "true", "unknownkey": "x"}) == ""


def test_banner_key_set_contains_expected_keys():
    expected = {"logo", "author", "title", "subtitle", "revision", "date", "color", "stripe", "logo-height"}
    assert expected == _BANNER_KEYS


# ── minimal vs full ────────────────────────────────────────────────────────

def test_title_only_produces_minimal_banner():
    result = make_banner({"title": "Hello"})
    assert "cover-banner-minimal" in result
    assert "cover-title" in result
    assert "Hello" in result


def test_title_with_subtitle_is_full_banner():
    result = make_banner({"title": "T", "subtitle": "S"})
    assert "cover-banner-minimal" not in result
    assert "cover-subtitle" in result


def test_title_with_author_is_full_banner():
    result = make_banner({"title": "T", "author": "Alice"})
    assert "cover-banner-minimal" not in result
    assert "cover-author" in result


def test_author_only_is_full_banner():
    result = make_banner({"author": "Acme Corp"})
    assert "cover-banner-minimal" not in result
    assert "Acme Corp" in result


def test_subtitle_only_is_full_banner():
    result = make_banner({"subtitle": "A guide"})
    assert "cover-banner-minimal" not in result


# ── date ──────────────────────────────────────────────────────────────────

def test_auto_date_contains_current_year():
    result = make_banner({"title": "T"})
    assert str(date.today().year) in result


def test_explicit_date_used():
    result = make_banner({"title": "T", "date": "March 2025"})
    assert "March 2025" in result


def test_empty_date_string_triggers_auto():
    result = make_banner({"title": "T", "date": ""})
    assert str(date.today().year) in result


def test_revision_appears_in_meta():
    result = make_banner({"title": "T", "revision": "v2.1"})
    assert "v2.1" in result


def test_revision_and_date_both_appear():
    result = make_banner({"title": "T", "revision": "v1.0", "date": "Jan 2026"})
    assert "v1.0" in result
    assert "Jan 2026" in result


# ── stripe ────────────────────────────────────────────────────────────────

def test_stripe_true_adds_rgba_overlay():
    result = make_banner({"title": "T", "stripe": "true"})
    assert "rgba(255,255,255,0.25)" in result


def test_stripe_false_no_border():
    result = make_banner({"title": "T", "stripe": "false"})
    assert "border-left" not in result


def test_stripe_custom_color():
    result = make_banner({"title": "T", "stripe": "#ff0000"})
    assert "border-left" in result
    assert "#ff0000" in result


# ── color ─────────────────────────────────────────────────────────────────

def test_default_color_uses_accent_var():
    result = make_banner({"title": "T"})
    assert "var(--accent)" in result


def test_custom_color_overrides_default():
    result = make_banner({"title": "T", "color": "#1b3a5c"})
    assert "#1b3a5c" in result
    assert "var(--accent)" not in result


# ── content elements ──────────────────────────────────────────────────────

def test_title_in_cover_title_div():
    result = make_banner({"title": "My Document"})
    assert '<div class="cover-title">My Document</div>' in result


def test_subtitle_in_cover_subtitle_div():
    result = make_banner({"subtitle": "A guide"})
    assert "cover-subtitle" in result
    assert "A guide" in result


def test_author_in_cover_author_div():
    result = make_banner({"author": "Acme Corp"})
    assert "cover-author" in result
    assert "Acme Corp" in result


def test_no_logo_no_author_no_top_element():
    result = make_banner({"title": "T"})
    assert "cover-author" not in result
    assert "<img" not in result


def test_logo_replaces_author(tmp_path):
    img = tmp_path / "logo.png"
    img.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 20)
    result = make_banner({"logo": str(img), "author": "Acme"}, source_dir=tmp_path)
    assert "<img" in result
    assert "cover-author" not in result


def test_logo_height_applied(tmp_path):
    img = tmp_path / "logo.png"
    img.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 20)
    result = make_banner({"logo": str(img), "logo-height": "64px"}, source_dir=tmp_path)
    assert "height:64px" in result


def test_banner_contains_div():
    result = make_banner({"title": "T"})
    assert "<div" in result
    assert "</div>" in result


# ── html escaping ─────────────────────────────────────────────────────────

def test_title_html_escaped():
    result = make_banner({"title": "<script>alert(1)</script>"})
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_author_html_escaped():
    result = make_banner({"author": "<b>Acme</b>"})
    assert "<b>" not in result
    assert "&lt;b&gt;" in result


def test_subtitle_html_escaped():
    result = make_banner({"subtitle": 'A & B "Guide"'})
    assert "&amp;" in result
    assert "&quot;" in result


def test_revision_html_escaped():
    result = make_banner({"title": "T", "revision": "<v1>"})
    assert "<v1>" not in result
    assert "&lt;v1&gt;" in result
