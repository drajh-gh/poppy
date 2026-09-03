#!/usr/bin/env python3
"""Stateless lifecycle guardrails for the Poppy Housekeeping skill."""

from __future__ import annotations

import json
import re
import sys


TITLE_TOOL = "mcp__codex_app__set_thread_title"
ARCHIVE_TOOL = "mcp__codex_app__set_thread_archived"
EXACT_MARKER = re.compile(r"^(?:✅ \[D\]|⏸️ \[P\]|🚧 \[B\]) (?P<base>\S.*)$")
MARKER_LIKE = re.compile(r"^(?:✅|⏸️|🚧|\[(?:D|P|B)\])", re.IGNORECASE)
STACKED_MARKER = re.compile(r"^(?:✅ \[D\]|⏸️ \[P\]|🚧 \[B\]) (?:✅ \[D\]|⏸️ \[P\]|🚧 \[B\]) ")
CURRENT_TASK_LIFECYCLE_REQUEST = re.compile(
    r"\s*(?:(?:yes|yes\s+please|sure|okay|ok)[\s,;:-]+)?"
    r"(?:poppy[\s,:-]+)?(?:please\s+)?mark\s+(?:this|the\s+current)\s+"
    r"(?:thread|task)\s+(?:as\s+)?(?:done|complete|completed|active|paused|blocked)"
    r"(?:\s+(?:with|using)\s+(?:the\s+)?(?:tag|marker|completion\s+(?:tag|marker)))?"
    r"\s*[.!?]?\s*",
    re.IGNORECASE,
)
SAFE_TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")


def emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))


def context(event: str, message: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": message,
        }
    }


def deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def user_prompt_submit(event: dict) -> dict:
    prompt = event.get("prompt")
    if not isinstance(prompt, str) or CURRENT_TASK_LIFECYCLE_REQUEST.fullmatch(prompt) is None:
        return {}

    task_id = event.get("session_id")
    if not isinstance(task_id, str) or SAFE_TASK_ID.fullmatch(task_id.strip()) is None:
        return context(
            "UserPromptSubmit",
            "Poppy Housekeeping: exact current-task ID unavailable. Do not list tasks, probe the workspace, or mutate; fail closed now.",
        )

    return context(
        "UserPromptSubmit",
        f"Poppy Housekeeping exact current task ID: {task_id.strip()}. Use it for read/title/read; do not list tasks or infer identity.",
    )


def pre_tool_use(event: dict) -> dict:
    tool = event.get("tool_name")
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return deny("Housekeeping requires a structured task-tool input.")

    if tool == TITLE_TOOL:
        task_id = tool_input.get("threadId")
        implicit_current = "threadId" not in tool_input
        if not implicit_current and (not isinstance(task_id, str) or not task_id.strip()):
            return deny("Housekeeping title mutations require an explicit non-empty threadId or an ordinary native implicit title target.")
        title = tool_input.get("title")
        if not isinstance(title, str) or not title.strip():
            return deny("Housekeeping titles require a non-empty meaningful base title.")
        title = title.strip()
        match = EXACT_MARKER.fullmatch(title)
        if STACKED_MARKER.match(title) or (MARKER_LIKE.match(title) and match is None):
            return deny("Use one exact lifecycle prefix—✅ [D], ⏸️ [P], or 🚧 [B]—or no prefix for active work.")
        if match and MARKER_LIKE.match(match.group("base")):
            return deny("Housekeeping lifecycle markers cannot be stacked.")
        if implicit_current and match:
            return deny("Housekeeping lifecycle-marker mutations require an explicit threadId for exact read, rollback, and read-back. Native implicit targeting is only for ordinary non-lifecycle title edits.")
        target = "the native calling task" if implicit_current else "the explicit task ID"
        return context(
            "PreToolUse",
            f"Poppy Housekeeping: this title targets {target}. A marker records an evidenced lifecycle disposition; it does not create one. Preserve the base title and confirm exact authority.",
        )

    if tool == ARCHIVE_TOOL:
        task_id = tool_input.get("threadId")
        if not isinstance(task_id, str) or not task_id.strip():
            return deny("Housekeeping archive mutations require an explicit non-empty threadId.")
        archived = tool_input.get("archived")
        if not isinstance(archived, bool):
            return deny("Housekeeping archive mutations require an explicit boolean archived value.")
        return context(
            "PreToolUse",
            "Poppy Housekeeping: archive only an exact freshly reread eligible task under current authority; pinned, active, paused, blocked, ambiguous, or reopened tasks are ineligible.",
        )

    return {}


def post_tool_use(event: dict) -> dict:
    tool = event.get("tool_name")
    if tool == TITLE_TOOL:
        effect = "title"
    elif tool == ARCHIVE_TOOL:
        effect = "archive state"
    else:
        return {}
    return context(
        "PostToolUse",
        f"Poppy Housekeeping: read the authoritative task {effect} back before reporting this metadata effect as complete; retain the exact rollback target.",
    )


def main() -> int:
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        emit({"systemMessage": "Poppy Housekeeping received malformed hook input and made no lifecycle claim."})
        return 0

    if not isinstance(event, dict):
        emit({"systemMessage": "Poppy Housekeeping received non-object hook input and made no lifecycle claim."})
        return 0

    name = event.get("hook_event_name")
    if name == "SessionStart":
        emit(
            context(
                "SessionStart",
                "Poppy Housekeeping: on resume/compaction, reconcile lifecycle markers with new actionable scope. Clear the marker before substantive work; status-only activity does not reopen it. Do not repeat a completion offer without a newly completed scope.",
            )
        )
    elif name == "UserPromptSubmit":
        emit(user_prompt_submit(event))
    elif name == "PreToolUse":
        emit(pre_tool_use(event))
    elif name == "PostToolUse":
        emit(post_tool_use(event))
    else:
        emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
