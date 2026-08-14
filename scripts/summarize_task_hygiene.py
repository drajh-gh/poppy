#!/usr/bin/env python3
"""Summarize exceptions from a normalized task snapshot without exposing task text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


RAW_MARKUP = re.compile(r"<[^>]+>|\{\{[^}]+\}\}|\[(?:TODO|INSERT|PLACEHOLDER)[^]]*\]|```", re.IGNORECASE)


def _ref(task_id: str) -> str:
    return f"task-{hashlib.sha256(task_id.encode('utf-8')).hexdigest()[:12]}"


def summarize(snapshot: Any) -> dict[str, Any]:
    if not isinstance(snapshot, dict) or snapshot.get("schema_version") != 1:
        raise ValueError("snapshot schema_version must be 1")
    tasks = snapshot.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("snapshot.tasks must be a list")

    by_id: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(tasks):
        if not isinstance(value, dict) or not isinstance(value.get("task_id"), str) or not value["task_id"].strip():
            raise ValueError(f"snapshot.tasks[{index}].task_id must be a non-empty string")
        task_id = value["task_id"]
        if task_id in by_id:
            raise ValueError("snapshot task IDs must be unique")
        by_id[task_id] = value

    exceptions: list[dict[str, str]] = []

    def add(task_id: str, code: str, action: str) -> None:
        exceptions.append({"task_ref": _ref(task_id), "code": code, "action": action})

    for task_id, task in by_id.items():
        title = task.get("title")
        if not isinstance(title, str) or not title.strip():
            add(task_id, "missing_title", "assign a concise structured title")
        elif RAW_MARKUP.search(title):
            add(task_id, "raw_title_markup", "replace prompt or placeholder text with a structured title")
        parent_id = task.get("parent_task_id")
        if isinstance(parent_id, str) and parent_id in by_id and title == by_id[parent_id].get("title"):
            add(task_id, "copied_parent_title", "differentiate the worker role and outcome")
        if task.get("kind") == "worker":
            if task.get("delegation_depth") != 1 or task.get("created_child_count", 0) != 0:
                add(task_id, "recursive_delegation", "return control to the root and stop child creation")
            if task.get("human_authority") is not False:
                add(task_id, "worker_authority", "relay decisions to the root human-control surface")
            terminal = task.get("status") in {"complete", "failed", "cancelled"}
            safe_state = task.get("repository_state") in {"clean", "commit_recoverable", "not_applicable"}
            if (
                terminal
                and task.get("archived") is not True
                and task.get("attention_required") is False
                and task.get("result_captured_by_parent") is True
                and safe_state
            ):
                add(task_id, "archive_candidate", "parent may archive after confirming the captured closure card")
        elif (
            task.get("kind") == "root"
            and task.get("archive_requested") is True
            and task.get("user_archive_approved") is not True
        ):
            add(task_id, "root_archive_without_approval", "ask the user before archiving the root task")

    exceptions.sort(key=lambda item: (item["code"], item["task_ref"]))
    return {
        "schema_version": 1,
        "summary": {"task_count": len(tasks), "exception_count": len(exceptions)},
        "exceptions": exceptions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
        result = summarize(snapshot)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
