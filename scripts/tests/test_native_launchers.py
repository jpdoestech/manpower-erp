"""Unit checks plus an opt-in real Windows BAT setup/start/stop smoke."""

import http.cookiejar
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/windows"))
import local  # noqa: E402


class NativeHelper(unittest.TestCase):
    def test_tests_do_not_receive_active_database_or_auth_configuration(self) -> None:
        with (
            patch.dict(
                os.environ, DATABASE_URL="production-secret", POSTGRES_HOST="private"
            ),
            patch.object(local, "tools", return_value=("node", "npm")),
            patch.object(local, "run") as run,
        ):
            local.test_local()
            settings = run.call_args_list[0].kwargs["settings"]
            self.assertNotIn("DATABASE_URL", settings)
            self.assertNotIn("DATABASE_MODE", settings)
            self.assertFalse(
                any(key.startswith(("POSTGRES_", "AUTH_")) for key in settings)
            )
            self.assertEqual(settings["ERP_NATIVE_SMOKE"], "0")
            self.assertEqual(os.environ["DATABASE_URL"], "production-secret")

    def test_environment_overrides_cloud_settings_without_modifying_parent(
        self,
    ) -> None:
        with patch.dict(os.environ, DATABASE_URL="production-secret", VERCEL="1"):
            settings = local.environment()
            self.assertEqual(settings["DATABASE_MODE"], "sqlite")
            self.assertEqual(settings["AUTH_PROVIDER"], "local")
            self.assertEqual(settings["VERCEL"], "")
            self.assertNotIn("production-secret", settings["DATABASE_URL"])
            self.assertEqual(os.environ["DATABASE_URL"], "production-secret")

    def test_missing_or_wrong_node_fails_with_guidance(self) -> None:
        with patch("local.shutil.which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "Install Node.js 24"):
                local.tools()
        with (
            patch("local.shutil.which", return_value="node"),
            patch("local.subprocess.check_output", return_value="v22.1.0"),
        ):
            with self.assertRaisesRegex(RuntimeError, "Node.js 24"):
                local.tools()

    def test_port_collision_is_refused(self) -> None:
        with patch("local.socket.socket") as socket_mock:
            socket_mock.return_value.__enter__.return_value.connect_ex.return_value = 0
            with self.assertRaisesRegex(RuntimeError, "Port 8000"):
                local.require_free_ports()

    def test_dead_server_is_not_ready(self) -> None:
        process = MagicMock(spec=subprocess.Popen)
        process.poll.return_value = 1
        with self.assertRaisesRegex(RuntimeError, "server exited"):
            local.wait_ready([process])

    def test_stop_only_targets_owned_live_pid(self) -> None:
        process = MagicMock(spec=subprocess.Popen)
        process.pid = 12345
        process.poll.return_value = None
        with patch("local.subprocess.run") as run:
            local.stop(process)
            self.assertEqual(
                run.call_args.args[0], ["taskkill.exe", "/PID", "12345", "/T", "/F"]
            )
        process.poll.return_value = 0
        with patch("local.subprocess.run") as run:
            local.stop(process)
            run.assert_not_called()

    def test_start_failure_cleans_both_owned_processes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vite = root / "frontend/node_modules/vite/bin/vite.js"
            vite.parent.mkdir(parents=True)
            vite.touch()
            processes = [
                MagicMock(spec=subprocess.Popen),
                MagicMock(spec=subprocess.Popen),
            ]
            with (
                patch.object(local, "ROOT", root),
                patch("local.runtime.supervisor", return_value=nullcontext("test")),
                patch("local.runtime.lock", return_value=nullcontext()),
                patch.object(local, "tools", return_value=("node", "npm")),
                patch.object(local, "require_free_ports"),
                patch.object(local, "migrate"),
                patch("local.subprocess.Popen", side_effect=processes),
                patch.object(local, "wait_ready", side_effect=RuntimeError("failed")),
                patch.object(local, "stop") as stop,
            ):
                with self.assertRaisesRegex(RuntimeError, "failed"):
                    local.start(True)
                self.assertEqual(
                    [call.args[0] for call in stop.call_args_list],
                    list(reversed(processes)),
                )


@unittest.skipUnless(os.name == "nt", "Real Windows cmd required")
class NativeBat(unittest.TestCase):
    def test_missing_uv_fails_with_install_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "setup-local.bat"
            shutil.copyfile(ROOT / target.name, target)
            result = subprocess.run(
                [os.environ["COMSPEC"], "/d", "/c", "call", str(target)],
                cwd=ROOT,
                input="\n",
                text=True,
                capture_output=True,
                timeout=15,
                env={
                    **os.environ,
                    "PATH": str(Path(os.environ["SystemRoot"]) / "System32"),
                },
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Install uv 0.13.7", result.stdout)

    def test_missing_setup_does_not_start_servers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "start-local.bat"
            shutil.copyfile(ROOT / target.name, target)
            result = subprocess.run(
                [os.environ["COMSPEC"], "/d", "/c", "call", str(target)],
                cwd=ROOT,
                input="\n",
                text=True,
                capture_output=True,
                timeout=15,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Run setup-local.bat first", result.stdout)

    @unittest.skipUnless(
        os.environ.get("ERP_NATIVE_SMOKE") == "1", "Opt-in tool/network smoke"
    )
    def test_actual_bats_setup_repeat_start_http_and_stop(self) -> None:
        for port in (8000, 5173):
            with socket.socket() as probe:
                self.assertNotEqual(
                    probe.connect_ex(("127.0.0.1", port)),
                    0,
                    f"Port {port} must be free for smoke",
                )
        directory = ROOT / ".local"
        directory.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="native bat & test-", dir=directory
        ) as name:
            repo = Path(name)
            for filename in (
                "setup-local.bat",
                "start-local.bat",
                "setup.bat",
                "run.bat",
                ".env.example",
                "compose.yaml",
                "stop-local.bat",
                "test-local.bat",
                "backup-local-db.bat",
                "restore-local-db.bat",
                "reset-local-db.bat",
                "migrate-local.bat",
                "check-local.bat",
            ):
                shutil.copyfile(ROOT / filename, repo / filename)
            for folder in ("backend", "frontend", "scripts/windows", "scripts/tests"):
                shutil.copytree(
                    ROOT / folder,
                    repo / folder,
                    ignore=shutil.ignore_patterns(
                        ".venv",
                        "node_modules",
                        "dist",
                        "__pycache__",
                        ".*_cache",
                        ".env*",
                    ),
                )
            uv = shutil.which("uv.exe") or str(ROOT / ".tools/Scripts/uv.exe")
            (repo / ".tools/Scripts").mkdir(parents=True)
            shutil.copyfile(uv, repo / ".tools/Scripts/uv.exe")
            sentinel = repo / ".env"
            sentinel.write_text("DATABASE_URL=do-not-use-or-overwrite\n")
            for iteration in range(2):
                result = subprocess.run(
                    [
                        os.environ["COMSPEC"],
                        "/d",
                        "/c",
                        "call",
                        str(repo / "setup-local.bat"),
                        "--no-account",
                    ],
                    cwd=ROOT,
                    input="\n",
                    text=True,
                    capture_output=True,
                    timeout=300,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                print("Native BAT verified: setup-local.bat", flush=True)
                if iteration == 0:
                    subprocess.run(
                        [
                            str(repo / "backend/.venv/Scripts/python.exe"),
                            "-c",
                            "from sqlalchemy.orm import Session; "
                            "from app.database import create_database_engine; "
                            "from app.identity.service import provision_user; "
                            "engine=create_database_engine(); "
                            "db=Session(engine); "
                            "provision_user(db,'smoke-user',"
                            "'a native synthetic password'); "
                            "db.close(); engine.dispose()",
                        ],
                        cwd=repo / "backend",
                        env={
                            **os.environ,
                            "DATABASE_MODE": "sqlite",
                            "APP_ENV": "test",
                            "DATABASE_URL": "sqlite:///./.local/manpower_erp.db",
                            "VERCEL": "",
                            "PYTHONPATH": "",
                        },
                        check=True,
                        timeout=20,
                    )
            self.assertEqual(
                sentinel.read_text(), "DATABASE_URL=do-not-use-or-overwrite\n"
            )
            self.assertTrue((repo / ".local/manpower_erp.db").is_file())
            with (repo / "smoke.log").open("w+") as output:
                process = subprocess.Popen(
                    [
                        os.environ["COMSPEC"],
                        "/d",
                        "/c",
                        "call",
                        str(repo / "start-local.bat"),
                        "--no-browser",
                    ],
                    cwd=ROOT,
                    stdin=subprocess.PIPE,
                    stdout=output,
                    stderr=output,
                    text=True,
                )
                try:
                    for _ in range(150):
                        output.seek(0)
                        if "System ready:" in output.read():
                            break
                        if process.poll() is not None:
                            self.fail(
                                "Launcher exited: " + (repo / "smoke.log").read_text()
                            )
                        time.sleep(0.2)
                    else:
                        self.fail("No readiness: " + (repo / "smoke.log").read_text())
                    with urlopen("http://127.0.0.1:5173/api/health/ready") as response:
                        self.assertEqual(response.read(), b'{"status":"ready"}')
                    print(
                        "Native BAT verified: start-local.bat and HTTP readiness",
                        flush=True,
                    )
                    with urlopen("http://127.0.0.1:5173/") as response:
                        self.assertIn(b"<title>Manpower ERP</title>", response.read())
                    cookies = HTTPCookieProcessor(http.cookiejar.CookieJar())
                    browser = build_opener(cookies)
                    with browser.open(
                        Request(
                            "http://127.0.0.1:5173/api/auth/login",
                            data=json.dumps(
                                {
                                    "username": "smoke-user",
                                    "password": "a native synthetic password",
                                }
                            ).encode(),
                            headers={
                                "Content-Type": "application/json",
                                "Origin": "http://127.0.0.1:5173",
                            },
                        )
                    ) as response:
                        identity = json.load(response)
                    with browser.open("http://127.0.0.1:5173/api/auth/me") as response:
                        self.assertEqual(json.load(response)["id"], identity["id"])
                    with browser.open(
                        Request(
                            "http://127.0.0.1:5173/api/auth/logout",
                            data=b"{}",
                            headers={
                                "Content-Type": "application/json",
                                "Origin": "http://127.0.0.1:5173",
                                "X-CSRF-Token": identity["csrf_token"],
                            },
                        )
                    ) as response:
                        self.assertEqual(response.status, 204)
                    with self.assertRaises(HTTPError) as failure:
                        browser.open("http://127.0.0.1:5173/api/auth/me")
                    self.assertEqual(failure.exception.code, 401)
                    collision = subprocess.run(
                        [
                            os.environ["COMSPEC"],
                            "/d",
                            "/c",
                            "call",
                            str(repo / "start-local.bat"),
                            "--no-browser",
                        ],
                        cwd=ROOT,
                        input="\n",
                        text=True,
                        capture_output=True,
                        timeout=15,
                    )
                    self.assertNotEqual(collision.returncode, 0)
                    self.assertIn(
                        "Another local ERP operation is active", collision.stderr
                    )
                    with urlopen("http://127.0.0.1:5173/api/health/ready") as response:
                        self.assertEqual(response.status, 200)

                    def bat(
                        name: str, answer: str = "", argument: str = ""
                    ) -> subprocess.CompletedProcess[str]:
                        result = subprocess.run(
                            [
                                os.environ["COMSPEC"],
                                "/d",
                                "/c",
                                "call",
                                str(repo / name),
                            ]
                            + ([argument] if argument else []),
                            cwd=ROOT,
                            input=answer + "\n\n",
                            text=True,
                            capture_output=True,
                            timeout=300,
                        )
                        self.assertEqual(
                            result.returncode, 0, result.stdout + result.stderr
                        )
                        print(f"Native BAT verified: {name}", flush=True)
                        return result

                    bat("check-local.bat")
                    bat("backup-local-db.bat")
                    backup_files = list((repo / ".local-backups").glob("*.sqlite3"))
                    self.assertEqual(len(backup_files), 1)
                    saved = backup_files[0]
                    bat("stop-local.bat")
                    process.communicate("\n", timeout=20)
                    bat("stop-local.bat")
                    bat("restore-local-db.bat", "RESTORE LOCAL DATA", saved.name)
                    bat("reset-local-db.bat", "RESET LOCAL DATA")
                    bat("restore-local-db.bat", "RESTORE LOCAL DATA", saved.name)
                    bat("migrate-local.bat")
                    bat("migrate-local.bat")
                    bat("check-local.bat")
                    bat("test-local.bat")
                    self.assertEqual(
                        process.returncode, 0, (repo / "smoke.log").read_text()
                    )
                finally:
                    if process.poll() is None:
                        subprocess.run(
                            ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                            check=False,
                        )
                        process.wait(timeout=10)
            for port in (8000, 5173):
                with socket.socket() as probe:
                    self.assertNotEqual(probe.connect_ex(("127.0.0.1", port)), 0)


if __name__ == "__main__":
    unittest.main()
