"""Exercise the actual BAT files with cmd/PowerShell and a disposable Docker stub."""

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.name == "nt", "Requires the real Windows command interpreter")
class WindowsLaunchers(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "ERP folder & local!%"
        self.repo.mkdir()
        for name in ("setup.bat", "run.bat", ".env.example", "compose.yaml"):
            shutil.copyfile(ROOT / name, self.repo / name)
        self.stub = Path(self.temp.name) / "stub"
        self.stub.mkdir()
        (self.stub / "docker.cmd").write_bytes(
            b"@echo off\r\n"
            b'echo %*>>"%ERP_TEST_LOG%"\r\n'
            b'if /I "%~3"=="info" (\r\n'
            b'  if "%ERP_TEST_FAIL%"=="engine" exit /b 1\r\n'
            b'  if "%ERP_TEST_FAIL%"=="windows" (echo windows & exit /b 0)\r\n'
            b"  echo linux\r\n"
            b"  exit /b 0\r\n"
            b")\r\n"
            b'if /I "%~4"=="version" (\r\n'
            b'  if "%ERP_TEST_FAIL%"=="compose" exit /b 1\r\n'
            b"  exit /b 0\r\n"
            b")\r\n"
            b'echo %*| findstr /c:"config --quiet" >nul\r\n'
            b"if not errorlevel 1 (\r\n"
            b'  if "%ERP_TEST_FAIL%"=="config" exit /b 1\r\n'
            b"  exit /b 0\r\n"
            b")\r\n"
            b'echo %*| findstr /c:"up --build" >nul\r\n'
            b"if not errorlevel 1 (\r\n"
            b'  if "%ERP_TEST_FAIL%"=="startup" exit /b 1\r\n'
            b"  exit /b 0\r\n"
            b")\r\n"
            b'if "%ERP_TEST_FAIL%"=="account" exit /b 1\r\n'
            b"exit /b 0\r\n"
        )
        system = Path(os.environ["SystemRoot"]) / "System32"
        self.env = {
            **os.environ,
            "PATH": os.pathsep.join(
                [str(self.stub), str(system), str(system / "WindowsPowerShell/v1.0")]
            ),
            "ERP_TEST_LOG": str(Path(self.temp.name) / "commands.log"),
            "ERP_TEST_FAIL": "",
            "DOCKER_CONTEXT": "unintended-remote",
            "COMPOSE_FILE": "unintended.yaml",
            "COMPOSE_PROJECT_NAME": "unintended-project",
        }

    def run_script(
        self, script: str, answer: str = "N"
    ) -> subprocess.CompletedProcess[str]:
        # Invoke from outside the fixture repo to prove cwd handling.
        return subprocess.run(
            [os.environ["COMSPEC"], "/d", "/c", "call", str(self.repo / script)],
            cwd=self.temp.name,
            env=self.env,
            input=answer + "\n\n",
            text=True,
            capture_output=True,
            check=False,
            timeout=45,
        )

    def commands(self) -> str:
        path = Path(self.env["ERP_TEST_LOG"])
        return path.read_text() if path.exists() else ""

    def test_fresh_setup_creates_matching_secret_and_preserves_it_on_repeat(
        self,
    ) -> None:
        first = self.run_script("setup.bat")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        original = (self.repo / ".env").read_bytes()
        settings = original.decode()
        match = re.search(r"^POSTGRES_PASSWORD=([a-f0-9]{64})$", settings, re.MULTILINE)
        self.assertIsNotNone(match)
        assert match is not None
        secret = match.group(1)
        self.assertIn(f":{secret}@127.0.0.1", settings)
        self.assertNotIn(secret, first.stdout + first.stderr + self.commands())
        second = self.run_script("setup.bat")
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual((self.repo / ".env").read_bytes(), original)
        commands = self.commands()
        self.assertTrue(
            all(line.startswith("--context default ") for line in commands.splitlines())
        )
        self.assertNotIn("unintended", commands)
        self.assertIn("--context default compose version", commands)
        self.assertIn(
            "-f compose.yaml --env-file .env -p manpower-erp config --quiet", commands
        )
        self.assertIn("up --build --wait --wait-timeout 180", commands)
        self.assertNotIn(" exec ", commands)

    def test_existing_config_is_not_overwritten_on_failure(self) -> None:
        original = b"POSTGRES_PASSWORD=\r\n# existing local file\r\n"
        (self.repo / ".env").write_bytes(original)
        self.env["ERP_TEST_FAIL"] = "config"
        result = self.run_script("setup.bat")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid .env or Compose", result.stdout)
        self.assertEqual((self.repo / ".env").read_bytes(), original)
        self.assertNotIn("up --build", self.commands())
        self.assertNotIn("Setup complete", result.stdout)

    def test_missing_template_stops_before_docker(self) -> None:
        (self.repo / ".env.example").unlink()
        result = self.run_script("setup.bat")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Could not create .env", result.stdout)
        self.assertFalse((self.repo / ".env").exists())
        self.assertEqual(self.commands(), "")

    def test_missing_docker_fails_with_guidance(self) -> None:
        # Hosted Windows may ship Docker in System32; isolate discovery too.
        (self.stub / "docker.cmd").unlink()
        shutil.copyfile(
            Path(os.environ["SystemRoot"]) / "System32/where.exe",
            self.stub / "where.exe",
        )
        self.env["PATH"] = str(self.stub)
        subprocess.run(
            [str(self.stub / "where.exe"), "where.exe"],
            cwd=self.temp.name,
            env=self.env,
            capture_output=True,
            check=True,
            timeout=10,
        )
        result = self.run_script("run.bat")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Docker was not found", result.stdout)
        self.assertEqual(self.commands(), "")

    def test_missing_compose_or_engine_stops_before_startup(self) -> None:
        for failure in ("compose", "engine", "windows"):
            with self.subTest(failure=failure):
                self.env["ERP_TEST_FAIL"] = failure
                result = self.run_script("run.bat")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ERROR:", result.stdout)
                self.assertNotIn("up --build", self.commands())

    def test_missing_env_requires_setup(self) -> None:
        result = self.run_script("run.bat")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Run setup.bat first", result.stdout)
        self.assertFalse((self.repo / ".env").exists())

    def test_startup_failure_is_not_reported_as_ready(self) -> None:
        self.env["ERP_TEST_FAIL"] = "startup"
        result = self.run_script("setup.bat")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Startup or readiness failed", result.stdout)
        self.assertNotIn("System ready", result.stdout)
        self.assertNotIn("Setup complete", result.stdout)
        self.assertNotIn(" exec ", self.commands())

    def test_optional_account_uses_cli_and_propagates_failure(self) -> None:
        for failure, expected in (("", 0), ("account", 1)):
            with self.subTest(failure=failure):
                self.env["ERP_TEST_FAIL"] = failure
                result = self.run_script("setup.bat", "Y")
                self.assertEqual(
                    result.returncode, expected, result.stdout + result.stderr
                )
                self.assertIn("exec api .venv/bin/python", self.commands())
                self.assertIn("input('Username: ')", self.commands())
                self.assertIn("'create-user'", self.commands())
                self.assertNotIn("bootstrap-admins", self.commands())


if __name__ == "__main__":
    unittest.main()
