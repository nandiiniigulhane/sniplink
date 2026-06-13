from services.url_service.password_page import password_page_html


def test_returns_html_string():
    html = password_page_html("testalias")
    assert isinstance(html, str)
    assert len(html) > 0


def test_contains_alias():
    html = password_page_html("my-custom-alias")
    assert "my-custom-alias" in html


def test_contains_password_protected_text():
    html = password_page_html("abc")
    assert "Password Protected" in html


def test_contains_verify_endpoint():
    html = password_page_html("test123")
    # JavaScript uses concatenation: '/api/verify/' + alias
    assert "/api/verify/" in html
    assert "test123" in html


def test_contains_fetch_call():
    html = password_page_html("abc")
    assert "fetch('/api/verify/" in html


def test_contains_styles():
    html = password_page_html("abc")
    assert "<style>" in html
    assert "font-family" in html


def test_doctype_present():
    html = password_page_html("abc")
    assert "<!DOCTYPE html>" in html
