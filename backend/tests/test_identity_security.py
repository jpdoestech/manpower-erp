import getpass
import sys
import warnings
from unittest.mock import MagicMock

import pytest

from app.identity import cli
from app.identity.security import (
    auth_settings,
    csrf_token,
    hash_password,
    normalize_username,
    token_hash,
    verify_password,
)


def test_argon2id_verification_and_token_derivation() -> None:
    password = "long synthetic passphrase"
    encoded = hash_password(password)
    assert encoded.startswith("$argon2id$")
    assert password not in encoded
    assert verify_password(password, encoded)
    assert not verify_password("wrong", encoded)
    assert not verify_password(password, None)
    assert not verify_password(password, "corrupt-hash")
    assert hash_password(password) != encoded
    assert token_hash("token") != "token"
    assert csrf_token("token-one") != csrf_token("token-two")


@pytest.mark.parametrize("value", ["short", "x" * 129])
def test_password_limits(value: str) -> None:
    with pytest.raises(ValueError):
        hash_password(value)


@pytest.mark.parametrize("value", ["ab", "user@x", "x" * 65, "a\nname", "😀user"])
def test_invalid_names(value: str) -> None:
    with pytest.raises(ValueError):
        normalize_username(value)


def test_normalized_names_and_unmodified_passphrases() -> None:
    assert normalize_username("  SOME.User  ") == "some.user"
    password = "  spaces preserved  "
    assert verify_password(password, hash_password(password))
    assert not verify_password(password.strip(), hash_password(password))


@pytest.mark.parametrize(
    "origin,secure",
    [
        ("http://remote.example", "false"),
        ("https://remote.example", "false"),
        ("http://remote.example", "true"),
        ("https://host/path", "true"),
        ("https://user:secret@host", "true"),
        ("*", "true"),
        ("https://host", "invalid"),
    ],
)
def test_cookie_configuration_rejects_unsafe_values(
    monkeypatch: pytest.MonkeyPatch, origin: str, secure: str
) -> None:
    monkeypatch.setenv("AUTH_ORIGIN", origin)
    monkeypatch.setenv("AUTH_COOKIE_SECURE", secure)
    with pytest.raises(RuntimeError, match="authentication origin/cookie"):
        auth_settings()


def test_default_secure_and_loopback_opt_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTH_COOKIE_SECURE", raising=False)
    assert auth_settings().cookie_secure
    monkeypatch.setenv("AUTH_ORIGIN", "http://127.0.0.1:5173")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    assert not auth_settings().cookie_secure


def test_cli_refuses_echoing_password_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = MagicMock()
    monkeypatch.setattr(cli, "create_database_engine", lambda: engine)
    monkeypatch.setattr(sys, "argv", ["identity", "create-user", "alice"])

    def insecure_prompt(prompt: str) -> str:
        warnings.warn("Echo would be enabled", getpass.GetPassWarning, stacklevel=2)
        raise AssertionError("Echoing fallback must not run")

    monkeypatch.setattr("getpass.getpass", insecure_prompt)
    with pytest.raises(SystemExit) as caught:
        cli.main()
    assert caught.value.code == 1
    engine.dispose.assert_called_once()
