import argparse
import getpass
import warnings

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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
    except ValueError as error:
        # Only known, static validation messages are safe to show to the operator.
        message = str(error)
        if message not in {
            "Passwords do not match",
            "Password must contain 15 to 128 characters",
            "Invalid username",
            "User not found",
            "Distinct administrators required",
            "Bootstrap already completed",
        }:
            message = "Invalid account input"
        parser.exit(1, f"Identity operation failed: {message}.\n")
    except (EOFError, getpass.GetPassWarning):
        parser.exit(
            1,
            "Identity operation failed: hidden password input requires an interactive "
            "terminal. Run setup-local.bat directly; do not pipe password input.\n",
        )
    except IntegrityError:
        parser.exit(
            1,
            "Identity operation failed: account data conflicts with an existing "
            "record or database constraint. Existing accounts were not reset.\n",
        )
    except SQLAlchemyError:
        parser.exit(
            1,
            "Identity operation failed: database operation failed. "
            "Check local connectivity and migrations.\n",
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
