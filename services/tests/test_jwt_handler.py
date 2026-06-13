import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch

from shared.config import Config
from services.auth_service.jwt_handler import create_access_token, decode_access_token


def test_create_access_token():
    token = create_access_token(1, "test@example.com")
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token_valid():
    token = create_access_token(42, "user@test.com")
    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["email"] == "user@test.com"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_default_user_id():
    token = create_access_token(1, "a@b.com")
    payload = decode_access_token(token)
    assert payload["sub"] == "1"


def test_token_contains_exp():
    token = create_access_token(1, "a@b.com")
    payload = decode_access_token(token)
    now = datetime.utcnow().timestamp()
    assert payload["exp"] > now


def test_decode_expired_token():
    with patch("services.auth_service.jwt_handler.datetime") as mock_dt:
        from datetime import datetime, timedelta

        # Create token with iat = long ago (so exp is also long ago)
        old_time = datetime(2020, 1, 1, 12, 0, 0)
        mock_dt.utcnow.return_value = old_time
        # Also need to handle timedelta — make it real
        mock_dt.side_effect = None

        token = create_access_token(1, "a@b.com")

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_decode_invalid_token_raises():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not.a.real.token")


def test_decode_tampered_token_raises():
    token = create_access_token(1, "a@b.com")
    # Tamper with the payload
    parts = token.split(".")
    tampered = parts[0] + "." + parts[1] + "a" + ".invalid_sig"
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered)


def test_decode_empty_token_raises():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("")


def test_decode_wrong_secret():
    token = create_access_token(1, "a@b.com")
    with pytest.raises(jwt.InvalidTokenError):
        jwt.decode(token, "wrong-secret", algorithms=[Config.JWT_ALGORITHM])
