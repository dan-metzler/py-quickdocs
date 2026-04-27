from main import parse_frontmatter


def test_no_frontmatter_returns_empty_dict():
    text = "# Hello\nWorld"
    meta, body = parse_frontmatter(text)
    assert meta == {}
    assert body == text


def test_basic_key_value_pairs():
    text = "---\ntitle: My Doc\nauthor: Alice\n---\n# Content"
    meta, body = parse_frontmatter(text)
    assert meta["title"] == "My Doc"
    assert meta["author"] == "Alice"


def test_body_excludes_frontmatter():
    text = "---\ntitle: Test\n---\n# Content\nParagraph"
    _, body = parse_frontmatter(text)
    assert "---" not in body
    assert "title" not in body
    assert "# Content" in body


def test_color_hash_preserved():
    text = "---\ncolor: #003388\n---\n"
    meta, _ = parse_frontmatter(text)
    assert meta["color"] == "#003388"


def test_boolean_like_values():
    text = "---\nstripe: true\ncolumns: false\n---\n"
    meta, _ = parse_frontmatter(text)
    assert meta["stripe"] == "true"
    assert meta["columns"] == "false"


def test_bom_stripped():
    text = "﻿---\ntitle: Test\n---\n"
    meta, _ = parse_frontmatter(text)
    assert meta["title"] == "Test"


def test_crlf_normalized():
    text = "---\r\ntitle: Test\r\nauthor: Bob\r\n---\r\n# Content"
    meta, body = parse_frontmatter(text)
    assert meta["title"] == "Test"
    assert meta["author"] == "Bob"
    assert "# Content" in body


def test_missing_closing_fence_returns_empty():
    text = "---\ntitle: Test\n# No closing fence"
    meta, body = parse_frontmatter(text)
    assert meta == {}
    assert body == text


def test_empty_frontmatter_block():
    text = "---\n---\n# Content"
    meta, body = parse_frontmatter(text)
    assert meta == {}
    assert "# Content" in body


def test_value_with_colon():
    text = "---\nsubtitle: A guide: part one\n---\n"
    meta, _ = parse_frontmatter(text)
    assert meta["subtitle"] == "A guide: part one"


def test_version_string():
    text = "---\nrevision: v2.1\n---\n"
    meta, _ = parse_frontmatter(text)
    assert meta["revision"] == "v2.1"


def test_multiple_fields():
    text = "---\ntitle: T\nauthor: A\nsubtitle: S\nrevision: v1\ndate: Jan 2026\nstripe: true\n---\n"
    meta, _ = parse_frontmatter(text)
    assert len(meta) == 6
    assert meta["date"] == "Jan 2026"


def test_whitespace_around_values_stripped():
    text = "---\ntitle:   My Title   \n---\n"
    meta, _ = parse_frontmatter(text)
    assert meta["title"] == "My Title"


def test_mixed_line_endings_in_frontmatter():
    # CRLF frontmatter followed by LF body
    text = "---\r\ntitle: Mixed\r\n---\n# Content"
    meta, body = parse_frontmatter(text)
    assert meta["title"] == "Mixed"
    assert "# Content" in body


def test_frontmatter_value_with_angle_brackets():
    # Angle brackets in values are stored raw (escaping happens at render time)
    text = "---\ntitle: <My Title>\n---\n"
    meta, _ = parse_frontmatter(text)
    assert meta["title"] == "<My Title>"
