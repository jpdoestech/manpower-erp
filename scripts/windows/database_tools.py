"""Validated local snapshots and confirmed replacement, independent of cloud URLs."""

import os
import re
import sqlite3
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import runtime
from alembic.config import Config
from alembic.script import ScriptDirectory


class Cancelled(RuntimeError):
    pass


def database(root: Path) -> Path:
    path = runtime.local_file(root, "manpower_erp.db")
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = path.with_name(path.name + suffix)
        if sidecar.resolve() != sidecar:
            raise RuntimeError("Database sidecars must not be links.")
    return path


def backups(root: Path) -> Path:
    return runtime.directory(root, ".local-backups")


@contextmanager
def connect(path: Path, *, readonly: bool = True) -> Iterator[sqlite3.Connection]:
    # Runtime pin/fix gate matches app.database, without opening an app transaction.
    version = sqlite3.sqlite_version_info
    if not (
        version >= (3, 51, 3)
        or (3, 50, 7) <= version < (3, 51, 0)
        or (3, 44, 6) <= version < (3, 45, 0)
    ):
        raise RuntimeError("SQLite runtime requires the WAL-reset fix; rerun setup.")
    mode = "ro" if readonly else "rw"
    db = sqlite3.connect(path.as_uri() + f"?mode={mode}", uri=True, timeout=10)
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA trusted_schema=OFF")
        db.execute("PRAGMA busy_timeout=10000")
        if db.execute("PRAGMA foreign_keys").fetchone() != (1,):
            raise RuntimeError("SQLite foreign-key enforcement is required.")
        yield db
    finally:
        db.close()


def validate(root: Path, path: Path) -> None:
    if not path.is_file() or path.is_symlink() or path.stat().st_nlink != 1:
        raise RuntimeError("A regular local SQLite database file is required.")
    with connect(path) as db:
        deadline = time.monotonic() + 30
        db.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise RuntimeError(
                "SQLite integrity validation failed; no replacement made."
            )
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError(
                "SQLite foreign-key validation failed; no replacement made."
            )
        head = ScriptDirectory.from_config(
            Config(str(root / "backend/alembic.ini"))
        ).get_current_head()
        if db.execute("SELECT version_num FROM alembic_version").fetchall() != [
            (head,)
        ]:
            raise RuntimeError(
                "Backup/database revision must match the current application head."
            )
        tables = {
            row[0]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if not {
            "auth_users",
            "auth_sessions",
            "auth_events",
            "auth_login_limits",
            "auth_account_changes",
            "auth_password_resets",
        }.issubset(tables):
            raise RuntimeError("Required identity schema is missing.")
        guards = {
            row[0]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        }
        expected = {"auth_events_immutable_update", "auth_events_immutable_delete"}
        for table in (
            "auth_users",
            "auth_sessions",
            "auth_events",
            "auth_login_limits",
            "auth_account_changes",
            "auth_password_resets",
        ):
            expected.update(
                f"{table}_limits_{operation}" for operation in ("insert", "update")
            )
        if not expected.issubset(guards):
            raise RuntimeError("Required identity/audit guards are missing.")


def snapshot(root: Path, source: Path, destination: Path) -> None:
    validate(root, source)
    # Destination is an exclusively created, invocation-owned candidate file.
    deadline = time.monotonic() + 30

    def progress(_: int, remaining: int, total: int) -> None:
        if time.monotonic() > deadline:
            raise RuntimeError("SQLite backup timed out; original data retained.")

    with connect(source) as original:
        with closing(sqlite3.connect(destination)) as copy:
            original.backup(copy, pages=128, progress=progress, sleep=0.05)
            copy.execute("PRAGMA journal_mode=DELETE")
    validate(root, destination)


def backup(root: Path) -> Path:
    folder = backups(root)
    name = f"backup-{datetime.now(UTC):%Y%m%d-%H%M%S}-{uuid4().hex}.sqlite3"
    target = folder / name
    # Exclusive reservation prevents overwriting even an existing backup.
    with target.open("xb"):
        pass
    try:
        snapshot(root, database(root), target)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    print(f"Validated SQLite backup: {target}")
    return target


def selected_backup(root: Path, name: str) -> Path:
    if not re.fullmatch(r"backup-\d{8}-\d{6}-[a-f0-9]{32}\.sqlite3", name):
        raise RuntimeError(
            "Select a backup filename from .local-backups; paths are not accepted."
        )
    path = backups(root) / name
    if path.resolve() != path:
        raise RuntimeError("Backup links or redirected paths are not accepted.")
    validate(root, path)
    return path


def confirmation(action: str) -> None:
    phrase = f"{action.upper()} LOCAL DATA"
    if input(f"This replaces local SQLite data. Type {phrase} to continue: ") != phrase:
        raise Cancelled("Cancelled; database unchanged.")


def checkpoint(path: Path) -> None:
    with connect(path, readonly=False) as db:
        if db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] != 0:
            raise RuntimeError("Database is busy; stop all SQLite connections first.")
        if db.execute("PRAGMA journal_mode=DELETE").fetchone() != ("delete",):
            raise RuntimeError("Database is busy; no replacement made.")
    if any(
        path.with_name(path.name + suffix).exists()
        for suffix in ("-wal", "-shm", "-journal")
    ):
        raise RuntimeError(
            "Database sidecars remain; close other connections before replacement."
        )


def revoke_restored_capabilities(path: Path) -> None:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f")
    with connect(path, readonly=False) as db:
        db.execute(
            "UPDATE auth_sessions SET revoked_at=? WHERE revoked_at IS NULL", (now,)
        )
        db.execute(
            "UPDATE auth_password_resets SET used_at=? WHERE used_at IS NULL", (now,)
        )
        db.execute(
            "UPDATE auth_account_changes SET expires_at=? "
            "WHERE approved_by IS NULL AND expires_at > ?",
            (now, now),
        )
        db.execute(
            "INSERT INTO auth_events (id,kind,source,request_id) VALUES (?,?,?,?)",
            (uuid4().hex, "local_database_restored", "local_tools", uuid4().hex),
        )
        db.commit()


def replace(
    root: Path, action: str, initialize: Callable[[Path], None], source: str = ""
) -> None:
    target = database(root)
    selected = selected_backup(root, source) if action == "restore" else None
    print(f"Local target: {target}")
    if selected:
        print(f"Selected backup: {selected.name}")
    confirmation(action)
    if target.exists():
        backup(root)
    with candidate(root) as prepared:
        if selected:
            snapshot(root, selected, prepared)
        initialize(prepared)
        if selected:
            revoke_restored_capabilities(prepared)
        validate(root, prepared)
        checkpoint(prepared)
        if target.exists():
            checkpoint(target)
        os.replace(prepared, target)
    print(f"Local {action} verified. Recovery backup retained; no cloud DB contacted.")


@contextmanager
def candidate(root: Path) -> Iterator[Path]:
    fd, filename = tempfile.mkstemp(
        prefix="candidate-", suffix=".sqlite3", dir=runtime.directory(root)
    )
    os.close(fd)
    path = Path(filename)
    try:
        yield path
    finally:
        # Only this operation's new candidate; never sweep active DB/backup files.
        for suffix in ("", "-wal", "-shm", "-journal"):
            path.with_name(path.name + suffix).unlink(missing_ok=True)
