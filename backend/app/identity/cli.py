import argparse
import getpass
import warnings

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import create_database_engine
from app.identity.administration import bootstrap
from app.identity.service import manage_user, provision_user


def confirmed_password(label: str) -> str:
    with warnings.catch_warnings(action="error", category=getpass.GetPassWarning):
        password = getpass.getpass(f"{label} password (15–128 characters): ")
        if password != getpass.getpass("Confirm password: "):
            raise ValueError("Passwords do not match")
    return password


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Operator-only identity management; no company grants"
    )
    parser.add_argument(
        "command",
        choices=[
            "create-user",
            "reset-password",
            "deactivate-user",
            "bootstrap-admins",
        ],
    )
    parser.add_argument("username")
    parser.add_argument("second_username", nargs="?")
    args = parser.parse_args()
    if (args.command == "bootstrap-admins") != (args.second_username is not None):
        parser.error("Only bootstrap-admins requires two usernames")
    engine = create_database_engine()
    try:
        password: str | None = None
        if args.command != "deactivate-user":
            password = confirmed_password("First account")
        with Session(engine) as db:
            if args.command == "bootstrap-admins":
                assert password is not None
                bootstrap(
                    db,
                    args.username,
                    password,
                    args.second_username,
                    confirmed_password("Second account"),
                )
            elif args.command == "create-user":
                assert password is not None
                provision_user(db, args.username, password)
            else:
                manage_user(db, args.username, password)
        print("Identity operation completed; no company permissions granted.")
    except (ValueError, EOFError, getpass.GetPassWarning, SQLAlchemyError):
        parser.exit(1, "Identity operation failed; verify input and local database.\n")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
