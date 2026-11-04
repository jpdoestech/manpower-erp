"""Disposable Windows database and ownership safety checks; no developer DB writes."""

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/windows"))
import database_tools as data  # noqa: E402
import local  # noqa: E402
import runtime  # noqa: E402


@unittest.skipUnless(os.name == "nt", "Real Windows file locks required")
class DatabaseTools(unittest.TestCase):
    def setUp(self) -> None:
        (ROOT / ".local").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(
            prefix="db tools & test-", dir=ROOT / ".local"
        )
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        backend = self.root / "backend"
        backend.mkdir()
        for name in ("app", "alembic"):
            shutil.copytree(
                ROOT / "backend" / name,
                backend / name,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        shutil.copyfile(ROOT / "backend/alembic.ini", backend / "alembic.ini")
        with patch.object(local, "ROOT", self.root):
            local.migrate()
        self.path = data.database(self.root)
        self.user_id, self.event_id = uuid4().hex, uuid4().hex
        with data.connect(self.path, readonly=False) as db:
            db.execute(
                "INSERT INTO auth_users (id,username,password_hash) VALUES (?,?,?)",
                (self.user_id, "synthetic", "synthetic-hash"),
            )
            db.execute(
                "INSERT INTO auth_events (id,user_id,kind,source,request_id) "
                "VALUES (?,?,?,?,?)",
                (self.event_id, self.user_id, "created", "test", uuid4().hex),
            )
            db.execute(
                "INSERT INTO auth_sessions (token_hash,user_id,expires_at) "
                "VALUES (?,?,?)",
                ("a" * 64, self.user_id, "2099-01-01 00:00:00.000000"),
            )
            db.execute(
                "INSERT INTO auth_password_resets (token_hash,user_id,expires_at) "
                "VALUES (?,?,?)",
                ("b" * 64, self.user_id, "2099-01-01 00:00:00.000000"),
            )
            db.commit()

    def rows(self, path: Path | None = None) -> tuple[int, str, str]:
        with data.connect(path or self.path) as db:
            return (
                db.execute("SELECT count(*) FROM auth_users").fetchone()[0],
                db.execute(
                    "SELECT id FROM auth_events WHERE kind='created'"
                ).fetchone()[0],
                db.execute("SELECT user_id FROM auth_sessions").fetchone()[0],
            )

    def replace(self, action: str, name: str = "") -> None:
        with patch("builtins.input", return_value=f"{action.upper()} LOCAL DATA"):
            with patch.object(local, "ROOT", self.root):
                data.replace(self.root, action, local.migrate, name)

    def test_live_backup_restore_preserves_uuid_audit_session_and_guards(self) -> None:
        with data.connect(self.path, readonly=False) as live:
            live.execute("PRAGMA journal_mode=WAL")
            live.execute(
                "INSERT INTO auth_users (id,username,password_hash) VALUES (?,?,?)",
                (uuid4().hex, "later", "hash"),
            )
            # Snapshot must exclude the in-flight write, even with the writer open.
            saved = data.backup(self.root)
            self.assertNotEqual(saved.parent, self.path.parent)
            self.assertFalse(saved.is_relative_to(self.path.parent))
            self.assertEqual(self.rows(saved), (1, self.event_id, self.user_id))
            live.commit()
        self.replace("restore", saved.name)
        self.assertEqual(self.rows(), (1, self.event_id, self.user_id))
        recovery = sorted(data.backups(self.root).glob("*.sqlite3"))
        self.assertTrue(any(self.rows(path)[0] == 2 for path in recovery))
        with data.connect(self.path, readonly=False) as db:
            self.assertIsNotNone(
                db.execute("SELECT revoked_at FROM auth_sessions").fetchone()[0]
            )
            self.assertIsNotNone(
                db.execute("SELECT used_at FROM auth_password_resets").fetchone()[0]
            )
            self.assertEqual(
                db.execute(
                    "SELECT count(*) FROM auth_events "
                    "WHERE kind='local_database_restored'"
                ).fetchone()[0],
                1,
            )
            with self.assertRaisesRegex(sqlite3.IntegrityError, "immutable"):
                db.execute("UPDATE auth_events SET kind='tampered'")
            self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        with patch.object(local, "ROOT", self.root):
            local.migrate()
            local.migrate()
        self.assertEqual(self.rows(), (1, self.event_id, self.user_id))

    def test_reset_is_confirmed_and_automatically_recoverable(self) -> None:
        saved = data.backup(self.root)
        self.replace("reset")
        with data.connect(self.path) as db:
            self.assertEqual(
                db.execute("SELECT count(*) FROM auth_users").fetchone()[0], 0
            )
        self.replace("restore", saved.name)
        self.assertEqual(self.rows(), (1, self.event_id, self.user_id))

    def test_cancel_does_not_modify_or_backup_active_data(self) -> None:
        saved = data.backup(self.root)
        before = self.path.read_bytes()
        names = set(data.backups(self.root).iterdir())
        for action, name in (("reset", ""), ("restore", saved.name)):
            with (
                patch("builtins.input", return_value="no"),
                self.assertRaises(data.Cancelled),
            ):
                data.replace(self.root, action, lambda _: None, name)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(names, set(data.backups(self.root).iterdir()))

    def test_replace_failure_preserves_original_and_recovery_backup(self) -> None:
        saved = data.backup(self.root)
        with patch("database_tools.os.replace", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                self.replace("restore", saved.name)
        self.assertEqual(self.rows(), (1, self.event_id, self.user_id))
        self.assertEqual(len(list(data.backups(self.root).glob("*.sqlite3"))), 2)
        self.assertEqual(list((self.root / ".local").glob("candidate-*")), [])

    def test_failed_reset_migration_keeps_original(self) -> None:
        def fail(path: Path) -> None:
            with closing(sqlite3.connect(path)) as db:
                db.execute("CREATE TABLE incomplete (id INTEGER)")
                db.commit()
            raise RuntimeError("synthetic migration failure")

        with patch("builtins.input", return_value="RESET LOCAL DATA"):
            with self.assertRaisesRegex(RuntimeError, "migration failure"):
                data.replace(self.root, "reset", fail)
        self.assertEqual(self.rows(), (1, self.event_id, self.user_id))
        self.assertEqual(list((self.root / ".local").glob("candidate-*")), [])

    def test_junction_backup_directory_and_hardlinked_database_are_rejected(
        self,
    ) -> None:
        target = self.root / "linked-storage"
        target.mkdir()
        junction = self.root / ".local-backups"
        subprocess.run(
            [
                os.environ["COMSPEC"],
                "/d",
                "/c",
                "mklink",
                "/J",
                str(junction),
                str(target),
            ],
            check=True,
            capture_output=True,
        )
        try:
            with self.assertRaisesRegex(RuntimeError, "real checkout"):
                data.backups(self.root)
        finally:
            junction.rmdir()
        alias = self.root / "alias.db"
        os.link(self.path, alias)
        with self.assertRaisesRegex(RuntimeError, "links"):
            data.database(self.root)
        alias.unlink()

    def test_invalid_backup_paths_corruption_and_revisions_are_rejected(self) -> None:
        for name in (
            "../manpower_erp.db",
            str(self.path),
            "x.sqlite3",
            "..\\outside.sqlite3",
        ):
            with self.assertRaises(RuntimeError):
                data.selected_backup(self.root, name)
        bad = data.backups(self.root) / f"backup-20260101-000000-{uuid4().hex}.sqlite3"
        bad.write_bytes(b"not a SQLite database")
        with self.assertRaises(sqlite3.DatabaseError):
            data.selected_backup(self.root, bad.name)
        bad.unlink()
        with closing(sqlite3.connect(bad)) as db:
            db.execute("CREATE TABLE alembic_version (version_num TEXT)")
            db.execute("INSERT INTO alembic_version VALUES ('unknown')")
            db.commit()
        with self.assertRaisesRegex(RuntimeError, "revision"):
            data.selected_backup(self.root, bad.name)

    def test_bad_foreign_keys_abort_backup_without_partial_snapshot(self) -> None:
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("PRAGMA foreign_keys=OFF")
            db.execute("UPDATE auth_sessions SET user_id=?", (uuid4().hex,))
            db.commit()
        with self.assertRaisesRegex(RuntimeError, "foreign-key"):
            data.backup(self.root)
        self.assertEqual(list(data.backups(self.root).iterdir()), [])

    def test_backup_with_missing_audit_guard_is_refused(self) -> None:
        saved = data.backup(self.root)
        with data.connect(saved, readonly=False) as db:
            db.execute("DROP TRIGGER auth_events_immutable_delete")
        with self.assertRaisesRegex(RuntimeError, "guards"):
            data.selected_backup(self.root, saved.name)
        self.assertEqual(self.rows(), (1, self.event_id, self.user_id))

    def test_offline_operations_refuse_managed_instances_and_unmanaged_ports(
        self,
    ) -> None:
        with runtime.supervisor(self.root):
            with patch.object(local, "ROOT", self.root):
                with self.assertRaises(runtime.Busy), local.offline():
                    self.fail("Must not enter an offline operation")
        with (
            patch.object(local, "ROOT", self.root),
            patch.object(
                local, "require_free_ports", side_effect=RuntimeError("unmanaged port")
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "unmanaged"), local.offline():
                self.fail("Must not enter an offline operation")

    def test_stale_run_state_never_authorizes_process_termination(self) -> None:
        state = runtime.local_file(self.root, "run.json")
        state.write_text('{"pid":1,"instance":"' + "a" * 32 + '"}')
        with patch("local.subprocess.run") as execute:
            runtime.request_stop(self.root)
            runtime.request_stop(self.root)
            execute.assert_not_called()
        self.assertFalse(runtime.running(self.root))

    def test_cooperative_stop_targets_only_the_current_instance(self) -> None:
        ready = threading.Event()
        finished = threading.Event()

        def own() -> None:
            with runtime.supervisor(self.root) as identity:
                ready.set()
                while not runtime.stop_requested(self.root, identity):
                    time.sleep(0.01)
            finished.set()

        owner = threading.Thread(target=own)
        owner.start()
        self.assertTrue(ready.wait(5))
        runtime.request_stop(self.root)
        self.assertTrue(finished.wait(5))
        owner.join(5)
        runtime.request_stop(self.root)


if __name__ == "__main__":
    unittest.main()
