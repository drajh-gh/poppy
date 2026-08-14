#!/usr/bin/env python3
"""Deterministic current-platform tests for the owned-process supervisor candidate."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from owned_process_supervisor import pid_alive, surviving_pids


SCRIPTS = Path(__file__).resolve().parent
SUPERVISOR = SCRIPTS / "owned_process_supervisor.py"
FIXTURE = SCRIPTS / "tests" / "process_tree_fixture.py"


def wait_for(path: Path, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while not path.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    if not path.exists():
        raise AssertionError(f"fixture did not create {path}")


def run_supervisor(
    command: list[str],
    report: Path,
    *,
    timeout: float = 5.0,
    rollback: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        str(SUPERVISOR),
        "--timeout",
        str(timeout),
        "--grace",
        "0.4",
        "--report",
        str(report),
    ]
    if rollback is not None:
        args.extend(["--rollback-command-json", json.dumps(rollback), "--rollback-timeout", "5"])
    args.extend(["--", *command])
    return subprocess.run(args, text=True, capture_output=True, timeout=30, check=False)


class OwnedProcessSupervisorTests(unittest.TestCase):
    def test_pass_output_and_exit_propagation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="owned-process-pass-") as temporary:
            report = Path(temporary) / "report.json"
            result = run_supervisor([sys.executable, str(FIXTURE), "echo"], report)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("fixture-stdout", result.stdout)
            self.assertIn("fixture-stderr", result.stderr)
            packet = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(packet["status"], "passed")
            self.assertEqual(packet["child_exit_code"], 0)

    def test_failure_exit_propagation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="owned-process-fail-") as temporary:
            report = Path(temporary) / "report.json"
            result = run_supervisor(
                [sys.executable, str(FIXTURE), "echo", "--exit-code", "7"], report
            )
            self.assertEqual(result.returncode, 7)
            packet = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(packet["status"], "failed")
            self.assertEqual(packet["child_exit_code"], 7)

    def test_timeout_cleans_owned_tree_and_preserves_unrelated_process(self) -> None:
        with tempfile.TemporaryDirectory(prefix="owned-process-timeout-") as temporary:
            root = Path(temporary)
            pid_dir = root / "owned"
            unrelated_pid_file = root / "unrelated.pid"
            unrelated = subprocess.Popen(
                [
                    sys.executable,
                    str(FIXTURE),
                    "sleeper",
                    "--pid-file",
                    str(unrelated_pid_file),
                ]
            )
            try:
                wait_for(unrelated_pid_file)
                report = root / "report.json"
                result = run_supervisor(
                    [sys.executable, str(FIXTURE), "tree", "--pid-dir", str(pid_dir)],
                    report,
                    timeout=1.5,
                )
                self.assertEqual(result.returncode, 124, result.stderr)
                for name in ("root.pid", "child.pid", "grandchild.pid"):
                    path = pid_dir / name
                    wait_for(path)
                    pid = int(path.read_text(encoding="utf-8").strip())
                    self.assertFalse(pid_alive(pid), f"owned {name} survived: {pid}")
                self.assertTrue(pid_alive(unrelated.pid), "unrelated process was terminated")
                packet = json.loads(report.read_text(encoding="utf-8"))
                self.assertEqual(packet["status"], "timed_out")
                self.assertEqual(packet["survivors"], [])
                self.assertGreaterEqual(len(packet["owned_pids"]), 3)
            finally:
                if unrelated.poll() is None:
                    unrelated.terminate()
                    try:
                        unrelated.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        unrelated.kill()
                        unrelated.wait(timeout=5)

    def test_timeout_runs_bounded_rollback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="owned-process-rollback-") as temporary:
            root = Path(temporary)
            marker = root / "rollback.txt"
            report = root / "report.json"
            result = run_supervisor(
                [sys.executable, str(FIXTURE), "sleeper"],
                report,
                timeout=0.5,
                rollback=[sys.executable, str(FIXTURE), "rollback", "--marker", str(marker)],
            )
            self.assertEqual(result.returncode, 124, result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "rollback-complete\n")
            packet = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(packet["rollback"], {"status": "passed", "exit_code": 0})

    def test_survivor_reporting_is_exact_and_sorted(self) -> None:
        self.assertEqual(surviving_pids([9, 3, 9, 1], lambda pid: pid in {3, 9}), [3, 9])

    def test_start_failure_writes_machine_readable_report(self) -> None:
        with tempfile.TemporaryDirectory(prefix="owned-process-start-fail-") as temporary:
            report = Path(temporary) / "report.json"
            result = run_supervisor([str(Path(temporary) / "missing-command")], report)
            self.assertEqual(result.returncode, 126)
            packet = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(packet["status"], "supervisor_error")
            self.assertEqual(packet["supervisor_exit_code"], 126)


if __name__ == "__main__":
    unittest.main(verbosity=2)
