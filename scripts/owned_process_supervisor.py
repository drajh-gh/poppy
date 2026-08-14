#!/usr/bin/env python3
"""Run one command in an owned process tree with bounded timeout cleanup."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Iterable, Sequence


WINDOWS = os.name == "nt"


def _process_table() -> dict[int, int]:
    """Return pid -> parent pid using platform tools, or an empty safe fallback."""
    try:
        if WINDOWS:
            shell = shutil.which("powershell") or shutil.which("pwsh")
            if not shell:
                return {}
            command = (
                "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId "
                "| ConvertTo-Json -Compress"
            )
            completed = subprocess.run(
                [shell, "-NoProfile", "-NonInteractive", "-Command", command],
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            if completed.returncode != 0 or not completed.stdout.strip():
                return {}
            parsed = json.loads(completed.stdout)
            rows = parsed if isinstance(parsed, list) else [parsed]
            return {
                int(row["ProcessId"]): int(row["ParentProcessId"])
                for row in rows
                if isinstance(row, dict) and "ProcessId" in row and "ParentProcessId" in row
            }
        completed = subprocess.run(
            ["ps", "-eo", "pid=,ppid="],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        if completed.returncode != 0:
            return {}
        table: dict[int, int] = {}
        for line in completed.stdout.splitlines():
            fields = line.split()
            if len(fields) == 2:
                table[int(fields[0])] = int(fields[1])
        return table
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired):
        return {}


def descendants(root_pid: int, table: dict[int, int]) -> set[int]:
    owned = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent in table.items():
            if parent in owned and pid not in owned:
                owned.add(pid)
                changed = True
    return owned


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if WINDOWS:
        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.windll.kernel32
        kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        kernel32.GetExitCodeProcess.restype = ctypes.c_int
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            # Access denied proves a process exists; an invalid parameter means it does not.
            return kernel32.GetLastError() == 5
        try:
            exit_code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return True
            return exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    if not WINDOWS:
        stat = Path(f"/proc/{pid}/stat")
        if stat.exists():
            try:
                if stat.read_text(encoding="utf-8").split()[2] == "Z":
                    return False
            except (OSError, IndexError):
                pass
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def surviving_pids(pids: Iterable[int], alive: Callable[[int], bool] = pid_alive) -> list[int]:
    return sorted(pid for pid in set(pids) if alive(pid))


def _wait_for_exit(pids: set[int], seconds: float) -> list[int]:
    deadline = time.monotonic() + seconds
    survivors = surviving_pids(pids)
    while survivors and time.monotonic() < deadline:
        time.sleep(0.05)
        survivors = surviving_pids(survivors)
    return survivors


def terminate_owned_tree(root_pid: int, grace_seconds: float) -> tuple[list[int], list[int], str]:
    owned = descendants(root_pid, _process_table())
    if WINDOWS:
        taskkill = shutil.which("taskkill") or "taskkill"
        completed = subprocess.run(
            [taskkill, "/PID", str(root_pid), "/T", "/F"],
            text=True,
            capture_output=True,
            timeout=max(5.0, grace_seconds + 2.0),
            check=False,
        )
        method = f"taskkill-tree:{completed.returncode}"
        if completed.returncode != 0:
            for pid in sorted(owned, reverse=True):
                subprocess.run(
                    [taskkill, "/PID", str(pid), "/F"],
                    text=True,
                    capture_output=True,
                    timeout=max(5.0, grace_seconds + 2.0),
                    check=False,
                )
            method += "+owned-pid-fallback"
    else:
        method = "posix-process-group"
        try:
            os.killpg(root_pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        survivors = _wait_for_exit(owned, grace_seconds)
        if survivors:
            try:
                os.killpg(root_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    survivors = _wait_for_exit(owned, max(0.2, grace_seconds))
    return sorted(owned), survivors, method


def _parse_command_json(value: str | None) -> list[str] | None:
    if value is None:
        return None
    parsed = json.loads(value)
    if not isinstance(parsed, list) or not parsed or any(not isinstance(item, str) or not item for item in parsed):
        raise ValueError("rollback command JSON must be a non-empty string array")
    return parsed


def _run_rollback(command: Sequence[str] | None, timeout: float) -> dict[str, object]:
    if command is None:
        return {"status": "not_requested", "exit_code": None}
    try:
        completed = subprocess.run(command, timeout=timeout, check=False)
        return {"status": "passed" if completed.returncode == 0 else "failed", "exit_code": completed.returncode}
    except subprocess.TimeoutExpired:
        return {"status": "timed_out", "exit_code": None}
    except OSError as exc:
        return {"status": "failed_to_start", "exit_code": None, "error": type(exc).__name__}


def run_owned(
    command: Sequence[str],
    timeout: float,
    grace: float,
    rollback_command: Sequence[str] | None,
    rollback_timeout: float,
) -> tuple[int, dict[str, object]]:
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if WINDOWS else 0
    child = subprocess.Popen(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=not WINDOWS,
        creationflags=creationflags,
    )
    report: dict[str, object] = {
        "schema_version": 1,
        "root_pid": child.pid,
        "status": "running",
        "timed_out": False,
        "child_exit_code": None,
        "owned_pids": [child.pid],
        "survivors": [],
        "termination_method": "not_required",
        "rollback": {"status": "not_requested", "exit_code": None},
    }
    try:
        stdout, stderr = child.communicate(timeout=timeout)
        report["child_exit_code"] = child.returncode
        report["status"] = "passed" if child.returncode == 0 else "failed"
        exit_code = int(child.returncode or 0)
    except subprocess.TimeoutExpired:
        report["timed_out"] = True
        owned, _pre_reap_survivors, method = terminate_owned_tree(child.pid, grace)
        report["owned_pids"] = owned
        report["termination_method"] = method
        try:
            stdout, stderr = child.communicate(timeout=max(1.0, grace + 1.0))
        except subprocess.TimeoutExpired:
            child.kill()
            stdout, stderr = child.communicate()
        # The direct child can remain observable until Popen reaps its handle. Re-check only
        # after communicate(), and use poll() as the authoritative direct-child result.
        descendant_survivors = _wait_for_exit(set(owned) - {child.pid}, max(0.2, grace))
        survivors = ([child.pid] if child.poll() is None else []) + descendant_survivors
        report["survivors"] = sorted(set(survivors))
        report["child_exit_code"] = child.returncode
        report["rollback"] = (
            {"status": "blocked_by_survivors", "exit_code": None}
            if survivors and rollback_command is not None
            else _run_rollback(rollback_command, rollback_timeout)
        )
        report["status"] = "survivors" if survivors else "timed_out"
        exit_code = 125 if survivors else 124
    if stdout:
        sys.stdout.write(stdout)
    if stderr:
        sys.stderr.write(stderr)
    report["supervisor_exit_code"] = exit_code
    return exit_code, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("--grace", type=float, default=1.0)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--rollback-command-json")
    parser.add_argument("--rollback-timeout", type=float, default=30.0)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or args.timeout <= 0 or args.grace < 0 or args.rollback_timeout <= 0:
        parser.error("positive timeout, non-negative grace, and a command are required")
    try:
        rollback = _parse_command_json(args.rollback_command_json)
        exit_code, report = run_owned(command, args.timeout, args.grace, rollback, args.rollback_timeout)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.report:
            args.report.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "supervisor_error",
                        "error": type(exc).__name__,
                        "supervisor_exit_code": 126,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        return 126
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(rendered, encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
