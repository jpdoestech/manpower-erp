"""Windows SQLite setup and foreground supervisor; no persisted PID or credentials."""

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from contextlib import ExitStack
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

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


def run(*arguments: str, cwd: Path = ROOT / "backend") -> None:
    subprocess.run(arguments, cwd=cwd, env=environment(), check=True)


def tools() -> tuple[str, str]:
    node = shutil.which("node.exe")
    npm = shutil.which("npm.cmd")
    if not node or not npm:
        raise RuntimeError("Install Node.js 24 with npm, then reopen this launcher.")
    version = subprocess.check_output([node, "--version"], text=True).strip()
    if not version.startswith("v24."):
        raise RuntimeError("Node.js 24 is required.")
    return node, npm


def migrate() -> None:
    run(sys.executable, "-m", "alembic", "upgrade", "head")
    run(sys.executable, "-m", "alembic", "check")


def setup(no_account: bool) -> None:
    _, npm = tools()
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
    node, _ = tools()
    vite = ROOT / "frontend/node_modules/vite/bin/vite.js"
    if not vite.is_file():
        raise RuntimeError(
            "Run setup-local.bat first; frontend dependencies are missing."
        )
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
        input("Keep this window open. Press Enter or Ctrl+C to stop both servers. ")
    print("Local servers stopped. SQLite data retained.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("setup", "start"))
    parser.add_argument("--no-account", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "setup":
            setup(args.no_account)
        else:
            start(args.no_browser)
        return 0
    except KeyboardInterrupt:
        print("Local operation stopped; data retained.")
        return 0 if args.action == "start" else 1
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except (OSError, subprocess.SubprocessError, EOFError):
        print(
            "ERROR: Local operation failed. Check versions, ports and .local/logs.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
