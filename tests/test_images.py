import base64
from pathlib import Path

from main import _embed_images_in_html

_MINIMAL_PNG = (
    b'\x89PNG\r\n\x1a\n'
    b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx'
    b'\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N'
    b'\x00\x00\x00\x00IEND\xaeB`\x82'
)


# ── local images ──────────────────────────────────────────────────────────

class TestLocalImages:
    def test_png_embedded_as_data_uri(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(_MINIMAL_PNG)
        html = '<img src="test.png">'
        result = _embed_images_in_html(html, tmp_path)
        assert "data:image/png;base64," in result
        assert "test.png" not in result

    def test_jpg_mime_type(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b'\xff\xd8\xff' + b'\x00' * 10)
        html = '<img src="photo.jpg">'
        result = _embed_images_in_html(html, tmp_path)
        assert "data:image/jpeg;base64," in result

    def test_jpeg_extension_mime_type(self, tmp_path):
        img = tmp_path / "photo.jpeg"
        img.write_bytes(b'\xff\xd8\xff' + b'\x00' * 10)
        result = _embed_images_in_html('<img src="photo.jpeg">', tmp_path)
        assert "data:image/jpeg;base64," in result

    def test_svg_mime_type(self, tmp_path):
        img = tmp_path / "icon.svg"
        img.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"/>')
        result = _embed_images_in_html('<img src="icon.svg">', tmp_path)
        assert "data:image/svg+xml;base64," in result

    def test_webp_mime_type(self, tmp_path):
        img = tmp_path / "img.webp"
        img.write_bytes(b'RIFF' + b'\x00' * 10)
        result = _embed_images_in_html('<img src="img.webp">', tmp_path)
        assert "data:image/webp;base64," in result

    def test_embedded_content_is_valid_base64(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(_MINIMAL_PNG)
        result = _embed_images_in_html('<img src="test.png">', tmp_path)
        b64 = result.split("base64,")[1].split('"')[0]
        decoded = base64.b64decode(b64)
        assert decoded == _MINIMAL_PNG

    def test_multiple_images_all_embedded(self, tmp_path):
        for name in ("a.png", "b.png"):
            (tmp_path / name).write_bytes(_MINIMAL_PNG)
        html = '<img src="a.png"><img src="b.png">'
        result = _embed_images_in_html(html, tmp_path)
        assert result.count("data:image/png;base64,") == 2


# ── remote and data urls ──────────────────────────────────────────────────

class TestRemoteAndDataUrls:
    def test_https_url_left_unchanged(self):
        html = '<img src="https://example.com/img.png">'
        result = _embed_images_in_html(html, Path("."))
        assert 'src="https://example.com/img.png"' in result

    def test_http_url_left_unchanged(self):
        html = '<img src="http://example.com/img.png">'
        result = _embed_images_in_html(html, Path("."))
        assert 'src="http://example.com/img.png"' in result

    def test_data_uri_left_unchanged(self):
        uri = "data:image/png;base64,abc123"
        html = f'<img src="{uri}">'
        result = _embed_images_in_html(html, Path("."))
        assert uri in result


# ── missing images ────────────────────────────────────────────────────────

class TestMissingImages:
    def test_missing_image_src_unchanged(self, tmp_path, capsys):
        html = '<img src="nonexistent.png">'
        result = _embed_images_in_html(html, tmp_path)
        assert "nonexistent.png" in result
        assert "data:" not in result

    def test_missing_image_prints_warning(self, tmp_path, capsys):
        _embed_images_in_html('<img src="missing.png">', tmp_path)
        captured = capsys.readouterr()
        assert "Warning" in captured.out or "warning" in captured.out.lower()

    def test_missing_image_does_not_crash(self, tmp_path):
        html = '<img src="no_such_file.png">'
        result = _embed_images_in_html(html, tmp_path)
        assert isinstance(result, str)


# ── absolute paths ────────────────────────────────────────────────────────

class TestAbsolutePaths:
    def test_absolute_src_path_embedded(self, tmp_path):
        img = tmp_path / "abs.png"
        img.write_bytes(_MINIMAL_PNG)
        html = f'<img src="{img.as_posix()}">'
        result = _embed_images_in_html(html, Path("."))
        assert "data:image/png;base64," in result

    def test_root_relative_path_attempted(self, tmp_path):
        # /images/x.png - src starts with /, treated as project-root relative
        # If not found it warns and leaves src unchanged
        html = '<img src="/images/nonexistent_absolute.png">'
        result = _embed_images_in_html(html, tmp_path)
        assert isinstance(result, str)
