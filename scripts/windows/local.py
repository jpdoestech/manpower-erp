"""Windows SQLite development tools; fixed local data, no persisted PID authority."""

import argparse
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
import webbrowser
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import database_tools
import runtime

ROOT = Path(__file__).resolve().parents[2]


def environment() -> dict[str, str]:
    return {
        **os.environ,
        "APP_ENV": "local",
        "DATABASE_MODE": "sqlite",
        "DATABASE_URL": "sqlite:///./.local/manpower_erp.db",
        "AUTH_PROVIDER": "local",
        "AUTH_ORIGIN": "http://127.0.0.1:5173",
        "AUTH_COOKIE_SECURE": "false",
        "API_PROXY_TARGET": "http://127.0.0.1:8000",
        "PYTHONPATH": str(ROOT / "backend/.venv/Lib/site-packages"),
        "PYTHONNOUSERSITE": "1",
        "VERCEL": "",
    }


def run(
    *arguments: str, cwd: Path | None = None, settings: dict[str, str] | None = None
) -> None:
    subprocess.run(
        arguments,
        cwd=cwd or ROOT / "backend",
        env=settings or environment(),
        check=True,
    )


def tools() -> tuple[str, str]:
    node = shutil.which("node.exe")
    npm = shutil.which("npm.cmd")
    if not node or not npm:
        raise RuntimeError("Install Node.js 24 with npm, then reopen this launcher.")
    version = subprocess.check_output([node, "--version"], text=True).strip()
    if not version.startswith("v24."):
        raise RuntimeError("Node.js 24 is required.")
    return node, npm


def migrate(path: Path | None = None) -> None:
    settings = environment()
    if path is not None:
        settings["DATABASE_URL"] = f"sqlite:///{path.as_posix()}"
    run(sys.executable, "-m", "alembic", "upgrade", "head", settings=settings)
    run(sys.executable, "-m", "alembic", "check", settings=settings)


def setup(no_account: bool) -> None:
    _, npm = tools()
    with offline():
        run(npm, "ci", cwd=ROOT / "frontend")
        migrate()
        if (
            not no_account
            and input("Create an ordinary test account? [y/N] ").lower() == "y"
        ):
            username = input("Username: ").strip()
            run(sys.executable, "-m", "app.identity.cli", "create-user", username)
    print("SQLite setup verified. Existing accounts/data and .env are preserved.")


def require_free_ports() -> None:
    for port in (8000, 5173):
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError(
                    f"Port {port} is already in use; stop its owner before starting."
                )


def wait_ready(processes: list[subprocess.Popen[bytes]]) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if any(process.poll() is not None for process in processes):
            raise RuntimeError("A server exited. Inspect .local/logs and rerun setup.")
        try:
            with urlopen(
                "http://127.0.0.1:5173/api/health/ready", timeout=1
            ) as response:
                if response.status == 200 and response.read() == b'{"status":"ready"}':
                    return
        except (OSError, URLError):
            pass
        time.sleep(0.2)
    raise RuntimeError("Readiness timed out. Inspect .local/logs and occupied ports.")


def stop(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        # Only this invocation's still-live process tree; never kill by image/port.
        subprocess.run(
            ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    process.wait(timeout=10)


def start(no_browser: bool) -> None:
    with runtime.supervisor(ROOT) as identity:
        start_owned(no_browser, identity)


def start_owned(no_browser: bool, identity: str) -> None:
    node, _ = tools()
    vite = ROOT / "frontend/node_modules/vite/bin/vite.js"
    if not vite.is_file():
        raise RuntimeError(
            "Run setup-local.bat first; frontend dependencies are missing."
        )
    with runtime.lock(ROOT, "database.lock"):
        require_free_ports()
        migrate()
    logs = ROOT / ".local/logs"
    logs.mkdir(parents=True, exist_ok=True)
    commands = (
        (
            [
                str(Path(sys.base_prefix) / "python.exe"),
                "-m",
                "uvicorn",
                "app.main:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
                "--no-access-log",
            ],
            ROOT / "backend",
            "api.log",
        ),
        (
            [node, str(vite), "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
            ROOT / "frontend",
            "web.log",
        ),
    )
    processes: list[subprocess.Popen[bytes]] = []
    with ExitStack() as stack:
        for arguments, cwd, name in commands:
            output = stack.enter_context((logs / name).open("wb"))
            process = subprocess.Popen(
                arguments, cwd=cwd, env=environment(), stdout=output, stderr=output
            )
            processes.append(process)
            stack.callback(stop, process)
        wait_ready(processes)
        print("System ready: http://127.0.0.1:5173", flush=True)
        if not no_browser:
            webbrowser.open("http://127.0.0.1:5173")
        print(
            "Keep this window open. Press Enter/Ctrl+C, or use stop-local.bat.",
            flush=True,
        )
        while not runtime.enter_pressed():
            if runtime.stop_requested(ROOT, identity):
                break
            if any(process.poll() is not None for process in processes):
                raise RuntimeError(
                    "A server exited; both owned processes are being stopped."
                )
            time.sleep(0.2)
    print("Local servers stopped. SQLite data retained.")


@contextmanager
def offline() -> Iterator[None]:
    with runtime.lock(ROOT):
        require_free_ports()
        with runtime.lock(ROOT, "database.lock"):
            yield


def test_local() -> None:
    _, npm = tools()
    settings = environment()
    # Tests select disposable databases themselves; never supply the active URL.
    for key in list(settings):
        if key.startswith(("POSTGRES_", "AUTH_")) or key in {
            "DATABASE_URL",
            "DATABASE_MODE",
            "APP_ENV",
        }:
            settings.pop(key)
    settings["ERP_NATIVE_SMOKE"] = "0"  # Never recursively run fresh-checkout smoke.
    run(
        sys.executable, "-m", "pytest", "-q", "-m", "not integration", settings=settings
    )
    run(
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "../scripts/tests",
        "-p",
        "test_*launchers.py",
        "-v",
        settings=settings,
    )
    run(npm, "test", cwd=ROOT / "frontend")


def check_local() -> None:
    tools()
    if not (ROOT / "frontend/node_modules/vite/bin/vite.js").is_file():
        raise RuntimeError("Frontend dependencies are missing; rerun setup-local.bat.")
    uv = ROOT / ".tools/Scripts/uv.exe"
    executable = str(uv) if uv.is_file() else shutil.which("uv.exe")
    if not executable:
        raise RuntimeError("uv is missing; rerun setup-local.bat.")
    version = subprocess.check_output([executable, "--version"], text=True).split()
    if version[:2] != ["uv", "0.13.7"] or sys.version_info[:3] != (3, 13, 18):
        raise RuntimeError("uv 0.13.7 and Python 3.13.18 are required; rerun setup.")
    with runtime.lock(ROOT, "database.lock"):
        database_tools.validate(ROOT, database_tools.database(ROOT))
        run(sys.executable, "-m", "alembic", "check")
    with socket.socket() as probe:
        listening = probe.connect_ex(("127.0.0.1", 8000)) == 0
    if listening:
        with urlopen("http://127.0.0.1:8000/api/health/ready", timeout=2) as response:
            if response.read() != b'{"status":"ready"}':
                raise RuntimeError("API is not ready.")
        print("API ready.")
    else:
        print("API stopped; use start-local.bat when needed.")
    print(
        f"Dependencies, SQLite {sqlite3.sqlite_version}, integrity/migrations verified."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=(
            "setup",
            "start",
            "stop",
            "test",
            "backup",
            "restore",
            "reset",
            "migrate",
            "check",
        ),
    )
    parser.add_argument("backup_name", nargs="?")
    parser.add_argument("--no-account", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "setup":
            setup(args.no_account)
        elif args.action == "start":
            start(args.no_browser)
        elif args.action == "stop":
            runtime.request_stop(ROOT)
            require_free_ports()
        elif args.action == "test":
            test_local()
        elif args.action == "check":
            check_local()
        elif args.action == "backup":
            with runtime.lock(ROOT, "database.lock"):
                database_tools.backup(ROOT)
        else:
            with offline():
                if args.action == "migrate":
                    migrate()
                else:
                    name = args.backup_name or ""
                    if args.action == "restore" and not name:
                        for path in sorted(
                            database_tools.backups(ROOT).glob("backup-*.sqlite3")
                        )[-10:]:
                            print(path.name)
                        name = input("Backup filename from .local-backups: ")
                    database_tools.replace(ROOT, args.action, migrate, name)
        return 0
    except database_tools.Cancelled as error:
        print(str(error))
        return 2
    except KeyboardInterrupt:
        print("Local operation stopped; data retained.")
        return 0 if args.action == "start" else 1
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except (OSError, sqlite3.Error, subprocess.SubprocessError, EOFError):
        print(
            "ERROR: Local operation failed. Check versions, ports and .local/logs.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
