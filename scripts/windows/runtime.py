"""Checkout-local locks and cooperative stop, without persisted PID authority."""

import ctypes
import json
import os
import re
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from ctypes import wintypes
from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

if os.name == "nt":
    import msvcrt


class Busy(RuntimeError):
    pass


def directory(root: Path, name: str = ".local") -> Path:
    path = root / name
    if (
        path.resolve() != path
        or str(path).startswith(("//", "\\\\"))
        or path.is_relative_to(Path(gettempdir()).resolve())
    ):
        raise RuntimeError(
            "Local tools require real checkout directories on a local disk."
        )
    path.mkdir(parents=True, exist_ok=True)
    return path


def local_file(root: Path, name: str) -> Path:
    path = directory(root) / name
    if path.resolve() != path or (path.exists() and path.stat().st_nlink != 1):
        raise RuntimeError("Local tool files must not be links or redirected paths.")
    return path


@contextmanager
def lock(root: Path, name: str = "run.lock") -> Iterator[None]:
    if os.name != "nt":
        raise RuntimeError("Windows local launchers require Windows.")
    with local_file(root, name).open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise Busy(
                "Another local ERP operation is active; stop it and retry."
            ) from None
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def running(root: Path) -> bool:
    try:
        with lock(root):
            return False
    except Busy:
        return True


def instance(root: Path) -> str | None:
    path = local_file(root, "run.json")
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text()[:1024])
        value = data["instance"]
        if not isinstance(value, str) or not re.fullmatch("[a-f0-9]{32}", value):
            raise ValueError
        return value
    except (ValueError, KeyError, TypeError):
        raise RuntimeError(
            "Invalid local run state; refusing to target any process."
        ) from None


@contextmanager
def supervisor(root: Path) -> Iterator[str]:
    with lock(root):
        identity = uuid4().hex
        request = local_file(root, "stop.request")
        request.unlink(missing_ok=True)
        state = local_file(root, "run.json")
        state.write_text(json.dumps({"instance": identity}))
        try:
            yield identity
        finally:
            state.unlink(missing_ok=True)
            request.unlink(missing_ok=True)


def stop_requested(root: Path, identity: str) -> bool:
    request = local_file(root, "stop.request")
    return request.exists() and request.read_text()[:64] == identity


def request_stop(root: Path) -> None:
    if not running(root):
        print("No managed local ERP instance is running.")
        return
    identity = instance(root)
    if identity is None:
        raise Busy(
            "A local database operation is active; retry stop after it finishes."
        )
    local_file(root, "stop.request").write_text(identity)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if not running(root) or instance(root) != identity:
            print("Owned local ERP instance stopped; data retained.")
            return
        time.sleep(0.1)
    raise RuntimeError(
        "Stop timed out. Use Enter in the owning launcher. No unrelated process killed."
    )


def enter_pressed() -> bool:
    if sys.stdin.isatty():
        return msvcrt.kbhit() and msvcrt.getwch() in {"\r", "\n"}
    # Poll redirected input without a daemon thread holding stdin at shutdown.
    available = wintypes.DWORD()
    handle = wintypes.HANDLE(msvcrt.get_osfhandle(sys.stdin.fileno()))
    if not ctypes.windll.kernel32.PeekNamedPipe(
        handle, None, 0, None, ctypes.byref(available), None
    ):
        return True
    return available.value > 0 and sys.stdin.read(1) in {"\r", "\n"}
