"""Trusted operator provisioning for company registry access."""

import argparse
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import create_database_engine
from app.organizations.service import provision_company, set_grant, set_hierarchy_grant


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("code")
    create.add_argument("legal_name")
    create.add_argument("username")
    for name in ("grant", "revoke", "grant-hierarchy", "revoke-hierarchy"):
        command = commands.add_parser(name)
        command.add_argument("company_id", type=UUID)
        command.add_argument("username")
    args = parser.parse_args()
    engine = create_database_engine()
    try:
        with Session(engine) as db:
            if args.command == "create":
                company = provision_company(
                    db, args.code, args.legal_name, args.username
                )
                print(f"Company created: {company.id}")
            elif args.command in ("grant-hierarchy", "revoke-hierarchy"):
                set_hierarchy_grant(
                    db,
                    args.company_id,
                    args.username,
                    args.command == "grant-hierarchy",
                )
                print("Company hierarchy access updated.")
            else:
                set_grant(db, args.company_id, args.username, args.command == "grant")
                print("Company registry access updated.")
    except (ValueError, SQLAlchemyError):
        parser.exit(
            1,
            "Company operation failed. Check input, operator permissions "
            "and migrations.\n",
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
