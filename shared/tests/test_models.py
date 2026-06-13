import pytest
from datetime import datetime
from pydantic import ValidationError

from shared.models import (
    ShortenRequest,
    ShortenResponse,
    PasswordVerifyRequest,
    AliasLookupResponse,
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UrlHistoryItem,
    UrlHistoryResponse,
)


class TestShortenRequest:
    def test_valid_url_passes(self):
        req = ShortenRequest(long_url="https://example.com/path")
        assert str(req.long_url) == "https://example.com/path"

    def test_invalid_url_raises(self):
        with pytest.raises(ValidationError):
            ShortenRequest(long_url="not-a-url")

    def test_custom_alias_none(self):
        req = ShortenRequest(long_url="https://a.com", custom_alias=None)
        assert req.custom_alias is None

    def test_custom_alias_valid(self):
        req = ShortenRequest(long_url="https://a.com", custom_alias="my-link")
        assert req.custom_alias == "my-link"

    def test_custom_alias_lowercased(self):
        req = ShortenRequest(long_url="https://a.com", custom_alias="MY-LINK")
        assert req.custom_alias == "my-link"

    def test_custom_alias_numbers_and_underscore(self):
        req = ShortenRequest(long_url="https://a.com", custom_alias="hello_123")
        assert req.custom_alias == "hello_123"

    def test_custom_alias_too_short_raises(self):
        with pytest.raises(ValidationError):
            ShortenRequest(long_url="https://a.com", custom_alias="abc")

    def test_custom_alias_too_long_raises(self):
        with pytest.raises(ValidationError):
            ShortenRequest(long_url="https://a.com", custom_alias="a" * 21)

    def test_custom_alias_special_chars_raises(self):
        with pytest.raises(ValidationError):
            ShortenRequest(long_url="https://a.com", custom_alias="my link")

    def test_custom_alias_exclamation_raises(self):
        with pytest.raises(ValidationError):
            ShortenRequest(long_url="https://a.com", custom_alias="hello!")

    def test_expires_in_days_none(self):
        req = ShortenRequest(long_url="https://a.com", expires_in_days=None)
        assert req.expires_in_days is None

    def test_expires_in_days_valid(self):
        req = ShortenRequest(long_url="https://a.com", expires_in_days=30)
        assert req.expires_in_days == 30

    def test_expires_in_days_min(self):
        req = ShortenRequest(long_url="https://a.com", expires_in_days=1)
        assert req.expires_in_days == 1

    def test_expires_in_days_max(self):
        req = ShortenRequest(long_url="https://a.com", expires_in_days=365)
        assert req.expires_in_days == 365

    def test_expires_in_days_zero_raises(self):
        with pytest.raises(ValidationError):
            ShortenRequest(long_url="https://a.com", expires_in_days=0)

    def test_expires_in_days_negative_raises(self):
        with pytest.raises(ValidationError):
            ShortenRequest(long_url="https://a.com", expires_in_days=-1)

    def test_expires_in_days_over_max_raises(self):
        with pytest.raises(ValidationError):
            ShortenRequest(long_url="https://a.com", expires_in_days=366)

    def test_password_none(self):
        req = ShortenRequest(long_url="https://a.com", password=None)
        assert req.password is None

    def test_password_valid(self):
        req = ShortenRequest(long_url="https://a.com", password="secret")
        assert req.password == "secret"

    def test_password_too_short_raises(self):
        with pytest.raises(ValidationError):
            ShortenRequest(long_url="https://a.com", password="abc")

    def test_all_fields_populated(self):
        req = ShortenRequest(
            long_url="https://example.com",
            custom_alias="my-link",
            expires_in_days=7,
            password="test123",
        )
        assert str(req.long_url) == "https://example.com/"
        assert req.custom_alias == "my-link"
        assert req.expires_in_days == 7
        assert req.password == "test123"


class TestShortenResponse:
    def test_fields(self):
        resp = ShortenResponse(
            short_url="http://localhost:8000/abc123",
            long_url="https://example.com",
            alias="abc123",
            is_custom=False,
        )
        assert resp.short_url == "http://localhost:8000/abc123"
        assert resp.long_url == "https://example.com"
        assert resp.alias == "abc123"
        assert resp.is_custom is False
        assert resp.has_password is False
        assert resp.expires_at is None

    def test_with_expiry(self):
        dt = datetime(2026, 6, 30)
        resp = ShortenResponse(
            short_url="http://localhost:8000/abc",
            long_url="https://example.com",
            alias="abc",
            is_custom=True,
            expires_at=dt,
        )
        assert resp.expires_at == dt

    def test_has_password_true(self):
        resp = ShortenResponse(
            short_url="http://localhost:8000/abc",
            long_url="https://example.com",
            alias="abc",
            is_custom=False,
            has_password=True,
        )
        assert resp.has_password is True


class TestPasswordVerifyRequest:
    def test_password_field(self):
        req = PasswordVerifyRequest(password="secret")
        assert req.password == "secret"


class TestAliasLookupResponse:
    def test_defaults(self):
        resp = AliasLookupResponse(alias="abc123")
        assert resp.alias == "abc123"
        assert resp.needs_password is False

    def test_needs_password(self):
        resp = AliasLookupResponse(alias="abc123", needs_password=True)
        assert resp.needs_password is True


class TestRegisterRequest:
    def test_valid_email_and_password(self):
        req = RegisterRequest(email="User@Example.Com", password="password123")
        assert req.email == "user@example.com"
        assert req.password == "password123"

    def test_email_lowercased(self):
        req = RegisterRequest(email="TEST@EXAMPLE.COM", password="password123")
        assert req.email == "test@example.com"

    def test_invalid_email_no_at_raises(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="notanemail", password="password123")

    def test_invalid_email_no_domain_raises(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@missingdot", password="password123")

    def test_password_too_short_raises(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", password="short")

    def test_password_exactly_8_chars(self):
        req = RegisterRequest(email="a@b.com", password="12345678")
        assert req.password == "12345678"

    def test_password_longer_than_8(self):
        req = RegisterRequest(email="a@b.com", password="123456789")
        assert req.password == "123456789"


class TestLoginRequest:
    def test_fields(self):
        req = LoginRequest(email="a@b.com", password="secret")
        assert req.email == "a@b.com"
        assert req.password == "secret"


class TestTokenResponse:
    def test_fields(self):
        resp = TokenResponse(access_token="abc.def.ghi", email="a@b.com")
        assert resp.access_token == "abc.def.ghi"
        assert resp.token_type == "bearer"
        assert resp.email == "a@b.com"

    def test_custom_token_type(self):
        resp = TokenResponse(access_token="x", email="a@b.com", token_type="jwt")
        assert resp.token_type == "jwt"


class TestUrlHistoryItem:
    def test_fields(self):
        item = UrlHistoryItem(
            alias="abc",
            long_url="https://example.com",
            short_url="http://localhost:8000/abc",
            is_custom=False,
        )
        assert item.alias == "abc"
        assert item.long_url == "https://example.com"
        assert item.short_url == "http://localhost:8000/abc"
        assert item.is_custom is False
        assert item.has_password is False
        assert item.expires_at is None
        assert item.created_at is None

    def test_all_fields(self):
        dt = datetime(2026, 6, 1)
        item = UrlHistoryItem(
            alias="abc",
            long_url="https://example.com",
            short_url="http://localhost:8000/abc",
            is_custom=True,
            has_password=True,
            expires_at=dt,
            created_at=dt,
        )
        assert item.is_custom is True
        assert item.has_password is True
        assert item.expires_at == dt
        assert item.created_at == dt


class TestUrlHistoryResponse:
    def test_empty_list(self):
        resp = UrlHistoryResponse(urls=[])
        assert resp.urls == []

    def test_with_items(self):
        items = [
            UrlHistoryItem(
                alias="abc", long_url="https://a.com",
                short_url="http://s/abc", is_custom=False,
            ),
        ]
        resp = UrlHistoryResponse(urls=items)
        assert len(resp.urls) == 1
        assert resp.urls[0].alias == "abc"
