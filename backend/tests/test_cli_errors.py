import getpass
import sys
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.identity import cli


@pytest.mark.parametrize(
    "error,expected",
    [
        (ValueError("Passwords do not match"), "Passwords do not match"),
        (ValueError("Password must contain 15 to 128 characters"), "15 to 128"),
        (ValueError("Invalid username"), "Invalid username"),
        (ValueError("private-value-must-not-leak"), "Invalid account input"),
        (EOFError("private-value-must-not-leak"), "interactive terminal"),
        (getpass.GetPassWarning("private-value-must-not-leak"), "interactive terminal"),
        (IntegrityError("private-value-must-not-leak", {}, Exception()), "constraint"),
        (SQLAlchemyError("private-value-must-not-leak"), "database operation failed"),
    ],
)
def test_cli_errors_are_actionable_and_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: Exception,
    expected: str,
) -> None:
    engine = MagicMock()
    monkeypatch.setattr(cli, "create_database_engine", lambda: engine)
    monkeypatch.setattr(sys, "argv", ["identity", "create-user", "example"])

    def fail_prompt(_: str) -> str:
        raise error

    monkeypatch.setattr(cli, "confirmed_password", fail_prompt)
    with pytest.raises(SystemExit) as caught:
        cli.main()
    assert caught.value.code == 1
    output = capsys.readouterr()
    assert expected in output.err
    assert "private-value-must-not-leak" not in output.err + output.out
    engine.dispose.assert_called_once()
