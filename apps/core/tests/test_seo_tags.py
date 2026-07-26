"""Tests del filtro safe_html: sanitización y marcado como HTML seguro."""

from django.utils.safestring import SafeString

from apps.core.templatetags.seo_tags import safe_html


class TestSafeHtml:
    def test_allows_whitelisted_tags(self):
        result = safe_html("<p>ok <b>bold</b></p>")
        assert str(result) == "<p>ok <b>bold</b></p>"

    def test_strips_script_tag(self):
        result = safe_html("<script>alert(1)</script>")
        assert "<script" not in str(result)

    def test_strips_event_handler_attributes(self):
        result = safe_html("<img src=x onerror=alert(1)>")
        assert "onerror" not in str(result)

    def test_strips_javascript_url(self):
        result = safe_html('<a href="javascript:alert(1)">x</a>')
        assert "javascript:" not in str(result)

    def test_strips_data_url(self):
        result = safe_html('<a href="data:text/html,evil">x</a>')
        assert "data:" not in str(result)

    def test_returns_safestring(self):
        result = safe_html("<p>ok</p>")
        assert isinstance(result, SafeString)
