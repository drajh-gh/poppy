#!/usr/bin/env python3
"""Bounded semantic-checkpoint lifecycle support for Poppy Scribe."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCHEMA_VERSION = 1
RETENTION_DAYS = 7
MAX_FILES = 128
MAX_MARKER_BYTES = 16_384
MAX_STATE_BYTES = 12_288
MAX_CONTEXT_CHARS = 2_200
MAX_RESTORED_CHECKPOINT_CHARS = 1_400
MARKER_START = "<!-- poppy-scribe:v1"
MARKER_END = "poppy-scribe:end -->"
MARKER = re.compile(
    re.escape(MARKER_START) + r"\s*(\{.*?\})\s*" + re.escape(MARKER_END),
    re.DOTALL,
)
ACTIVATION = re.compile(r"\b(?:poppy[- ]?scribe|scribe)\b", re.IGNORECASE)
IMPROVEMENT = re.compile(r"\b(?:improv|pattern|recurr|friction|learn)\w*\b", re.IGNORECASE)
REVIEW = re.compile(r"\b(?:review|checkpoint|handoff|challenge)\w*\b|what (?:changed|is unverified)", re.IGNORECASE)
FORGET = re.compile(
    r"\bforget\b|\b(?:clear|erase|delete)\s+(?:the\s+)?(?:scribe\s+)?(?:checkpoint|state)\b",
    re.IGNORECASE,
)
ALLOWED_MODES = {"quiet", "review", "improve"}
DECISION_STATUSES = {
    "proposed",
    "user-confirmed",
    "source-confirmed",
    "superseded",
    "conflicted",
}
EVIDENCE_STATUSES = {"supported", "unverified", "conflicted", "contradicted"}
CHANGE_STATES = {"proposed", "observed", "locally-verified", "read-back-verified"}
ATTENTION_KINDS = {
    "decision-conflict",
    "scope-drift",
    "authority-drift",
    "candidate-drift",
    "stale-evidence",
    "blind-retry",
    "unsupported-closure",
}
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{12,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{12,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}\b", re.IGNORECASE),
    re.compile(
        r"\b(?:api[_ -]?key|access[_ -]?token|password|private[_ -]?key|secret)\b"
        r"\s*[:=]\s*[^\s,;]{4,}",
        re.IGNORECASE,
    ),
)


def emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))


def hook_context(event: str, message: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": message[:MAX_CONTEXT_CHARS],
        }
    }


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


def session_key(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()


def data_root() -> Path | None:
    raw = os.environ.get("PLUGIN_DATA")
    if not raw:
        return None
    return Path(raw) / "scribe"


def paths_for(root: Path, key: str) -> tuple[Path, Path]:
    return root / "checkpoints" / f"{key}.json", root / "pending" / f"{key}.json"


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_STATE_BYTES:
        raise ValueError("bounded Scribe state exceeded its size limit")
    temporary = path.with_suffix(f".{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def read_json(path: Path) -> dict | None:
    try:
        if path.stat().st_size > MAX_STATE_BYTES:
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def remove(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def prune(root: Path, current: datetime) -> None:
    for directory in (root / "checkpoints", root / "pending"):
        try:
            files = sorted(
                (item for item in directory.iterdir() if item.is_file() and item.suffix == ".json"),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )[: MAX_FILES * 2]
        except (FileNotFoundError, OSError):
            continue
        for index, path in enumerate(files):
            value = read_json(path)
            expiry = parse_time(value.get("expires_at")) if value else None
            if index >= MAX_FILES or expiry is None or expiry <= current:
                remove(path)


def redact(value: str) -> tuple[str, bool]:
    changed = False
    for pattern in SECRET_PATTERNS:
        value, count = pattern.subn("[redacted]", value)
        changed = changed or bool(count)
    return value, changed


def clean_text(value: object, limit: int = 180) -> tuple[str, bool]:
    if not isinstance(value, str):
        return "", False
    value = " ".join(value.replace("\x00", " ").split())
    value, redacted = redact(value)
    return value[:limit], redacted


def clean_status(value: object, allowed: set[str], fallback: str) -> str:
    return value if isinstance(value, str) and value in allowed else fallback


def clean_items(
    value: object,
    fields: tuple[str, ...],
    maximum: int,
    status_field: str | None = None,
    statuses: set[str] | None = None,
    fallback: str = "unverified",
) -> tuple[list[dict], bool]:
    if not isinstance(value, list):
        return [], False
    output: list[dict] = []
    redacted = False
    for item in value[:maximum]:
        if not isinstance(item, dict):
            continue
        cleaned: dict[str, str] = {}
        for field in fields:
            if field == status_field and statuses is not None:
                cleaned[field] = clean_status(item.get(field), statuses, fallback)
            else:
                cleaned[field], changed = clean_text(item.get(field))
                redacted = redacted or changed
        if any(cleaned.values()):
            output.append(cleaned)
    return output, redacted


def normalize_checkpoint(raw: dict) -> tuple[dict, bool]:
    mode = clean_status(raw.get("mode"), ALLOWED_MODES, "quiet")
    intent, redacted = clean_text(raw.get("intent"), 500)
    decisions, changed = clean_items(
        raw.get("decisions"),
        ("statement", "status", "rationale", "evidence"),
        5,
        "status",
        DECISION_STATUSES,
        "proposed",
    )
    redacted = redacted or changed
    evidence, changed = clean_items(
        raw.get("evidence"),
        ("claim", "status", "source", "freshness"),
        6,
        "status",
        EVIDENCE_STATUSES,
    )
    redacted = redacted or changed
    changes, changed = clean_items(
        raw.get("changes"),
        ("target", "state", "summary", "verification"),
        5,
        "state",
        CHANGE_STATES,
        "observed",
    )
    redacted = redacted or changed
    questions, changed = clean_items(
        raw.get("questions"), ("question", "dependency", "owner"), 5
    )
    redacted = redacted or changed
    friction, changed = clean_items(
        raw.get("friction"),
        ("fingerprint", "summary", "evidence_status"),
        3,
        "evidence_status",
        EVIDENCE_STATUSES,
    )
    redacted = redacted or changed

    next_raw = raw.get("next_step") if isinstance(raw.get("next_step"), dict) else {}
    next_step: dict[str, str] = {}
    for field in ("action", "owner", "authority", "stop_condition"):
        next_step[field], changed = clean_text(next_raw.get(field))
        redacted = redacted or changed

    attention_raw = raw.get("attention") if isinstance(raw.get("attention"), dict) else None
    attention = None
    if attention_raw:
        kind = clean_status(attention_raw.get("kind"), ATTENTION_KINDS, "scope-drift")
        summary, changed = clean_text(attention_raw.get("summary"), 240)
        redacted = redacted or changed
        if summary:
            attention = {"kind": kind, "summary": summary}

    redactions: list[str] = []
    if isinstance(raw.get("redactions"), list):
        for item in raw["redactions"][:4]:
            cleaned, _ = clean_text(item, 100)
            if cleaned:
                redactions.append(cleaned)
    if redacted:
        redactions.append("secret-shaped content removed by hook")

    checkpoint = {
        "mode": mode,
        "intent": intent,
        "decisions": decisions,
        "evidence": evidence,
        "changes": changes,
        "questions": questions,
        "next_step": next_step,
        "attention": attention,
        "friction": friction,
        "redactions": list(dict.fromkeys(redactions))[:4],
    }
    shrink_order = ("questions", "changes", "evidence", "decisions", "friction")
    while len(json.dumps(checkpoint, ensure_ascii=True, separators=(",", ":")).encode("utf-8")) > 8_192:
        for field in shrink_order:
            if checkpoint[field]:
                checkpoint[field].pop()
                break
        else:
            checkpoint["intent"] = checkpoint["intent"][:240]
            break
    return checkpoint, redacted


def parse_marker(message: object) -> tuple[str, dict | None, str | None]:
    if not isinstance(message, str):
        return "missing", None, None
    matches = list(MARKER.finditer(message))
    if not matches:
        return "missing", None, None
    encoded = matches[-1].group(1)
    if len(encoded.encode("utf-8")) > MAX_MARKER_BYTES:
        return "invalid", None, "checkpoint marker exceeded its size limit"
    try:
        value = json.loads(encoded)
    except json.JSONDecodeError:
        return "invalid", None, "checkpoint marker contained malformed JSON"
    if not isinstance(value, dict):
        return "invalid", None, "checkpoint marker must contain one JSON object"
    action = value.get("action")
    if action == "forget":
        return "forget", None, None
    if action != "checkpoint" or not isinstance(value.get("checkpoint"), dict):
        return "invalid", None, "checkpoint marker has an unsupported action or payload"
    return "checkpoint", value["checkpoint"], None


def compact_checkpoint(state: dict) -> str:
    checkpoint = json.loads(json.dumps(state.get("checkpoint", {})))
    visible = {
        "sequence": state.get("sequence"),
        "captured_at": state.get("captured_at"),
        "expires_at": state.get("expires_at"),
        "mode": checkpoint.get("mode"),
        "intent": checkpoint.get("intent"),
        "decisions": checkpoint.get("decisions", []),
        "evidence": checkpoint.get("evidence", []),
        "changes": checkpoint.get("changes", []),
        "questions": checkpoint.get("questions", []),
        "next_step": checkpoint.get("next_step", {}),
        "attention": checkpoint.get("attention"),
        "friction": checkpoint.get("friction", []),
        "redactions": checkpoint.get("redactions", []),
    }
    shrink_order = ("questions", "changes", "evidence", "decisions", "friction", "redactions")
    encoded = json.dumps(visible, ensure_ascii=True, separators=(",", ":"))
    while len(encoded) > MAX_RESTORED_CHECKPOINT_CHARS:
        for field in shrink_order:
            if isinstance(visible.get(field), list) and visible[field]:
                visible[field].pop()
                break
        else:
            visible["intent"] = str(visible.get("intent", ""))[:180]
            next_step = visible.get("next_step")
            if isinstance(next_step, dict):
                visible["next_step"] = {
                    key: str(value)[:80] for key, value in next_step.items()
                }
            attention = visible.get("attention")
            if isinstance(attention, dict):
                attention["summary"] = str(attention.get("summary", ""))[:100]
            encoded = json.dumps(visible, ensure_ascii=True, separators=(",", ":"))
            if len(encoded) <= MAX_RESTORED_CHECKPOINT_CHARS:
                return encoded
            minimal = {
                "sequence": visible.get("sequence"),
                "captured_at": visible.get("captured_at"),
                "expires_at": visible.get("expires_at"),
                "mode": visible.get("mode"),
                "intent": visible.get("intent"),
                "next_step": visible.get("next_step"),
                "attention": visible.get("attention"),
                "checkpoint_truncated": True,
            }
            return json.dumps(minimal, ensure_ascii=True, separators=(",", ":"))
        encoded = json.dumps(visible, ensure_ascii=True, separators=(",", ":"))
    return encoded


def improvement_candidates(root: Path, current: datetime) -> list[dict]:
    sessions: dict[str, set[str]] = {}
    summaries: dict[str, str] = {}
    directory = root / "checkpoints"
    try:
        files = sorted(
            (item for item in directory.iterdir() if item.is_file() and item.suffix == ".json"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )[:MAX_FILES]
    except (FileNotFoundError, OSError):
        return []
    for path in files:
        state = read_json(path)
        expiry = parse_time(state.get("expires_at")) if state else None
        if not state or expiry is None or expiry <= current:
            continue
        key = state.get("session_key")
        checkpoint = state.get("checkpoint")
        if not isinstance(key, str) or not isinstance(checkpoint, dict):
            continue
        for item in checkpoint.get("friction", []):
            if not isinstance(item, dict) or item.get("evidence_status") != "supported":
                continue
            fingerprint = item.get("fingerprint")
            if not isinstance(fingerprint, str) or not fingerprint:
                continue
            sessions.setdefault(fingerprint, set()).add(key)
            summaries.setdefault(fingerprint, str(item.get("summary", "")))
    return [
        {
            "fingerprint": fingerprint,
            "independent_sessions": len(keys),
            "summary": summaries.get(fingerprint, "")[:120],
        }
        for fingerprint, keys in sorted(sessions.items())
        if len(keys) >= 3
    ][:3]


def load_live_checkpoint(path: Path, current: datetime) -> dict | None:
    state = read_json(path)
    expiry = parse_time(state.get("expires_at")) if state else None
    if (
        not state
        or state.get("schema_version") != SCHEMA_VERSION
        or not isinstance(state.get("session_key"), str)
        or not isinstance(state.get("sequence"), int)
        or not isinstance(state.get("checkpoint"), dict)
        or expiry is None
        or expiry <= current
    ):
        remove(path)
        return None
    return state


def stop(event: dict, root: Path, checkpoint_path: Path, pending_path: Path, current: datetime) -> dict:
    kind, raw, error = parse_marker(event.get("last_assistant_message"))
    if kind == "forget":
        remove(checkpoint_path)
        remove(pending_path)
        return {"systemMessage": "Poppy Scribe forgot this task's local checkpoint."}
    if kind == "checkpoint" and raw is not None:
        prior = load_live_checkpoint(checkpoint_path, current)
        checkpoint, redacted = normalize_checkpoint(raw)
        key = checkpoint_path.stem
        prior_sequence = prior.get("sequence", 0) if prior else 0
        if not isinstance(prior_sequence, int) or prior_sequence < 0:
            prior_sequence = 0
        state = {
            "schema_version": SCHEMA_VERSION,
            "session_key": key,
            "sequence": prior_sequence + 1,
            "captured_at": iso(current),
            "expires_at": iso(current + timedelta(days=RETENTION_DAYS)),
            "turn_id": clean_text(event.get("turn_id"), 120)[0],
            "checkpoint": checkpoint,
        }
        try:
            atomic_json(checkpoint_path, state)
        except (OSError, ValueError):
            return {"systemMessage": "Poppy Scribe could not persist the bounded checkpoint; continuity remains unverified."}
        remove(pending_path)
        prune(root, current)
        if redacted:
            return {"systemMessage": "Poppy Scribe stored the checkpoint after removing secret-shaped content."}
        return {}
    if kind == "invalid":
        return {"systemMessage": f"Poppy Scribe ignored an invalid marker: {error}. The prior checkpoint is unchanged."}

    active = load_live_checkpoint(checkpoint_path, current) is not None or read_json(pending_path) is not None
    if active and not event.get("stop_hook_active"):
        return {
            "decision": "block",
            "reason": (
                "Poppy Scribe is active. Continue once only to append the hidden poppy-scribe:v1 "
                "checkpoint marker required by the loaded Scribe contract. Do not change the visible answer."
            ),
        }
    if active:
        return {"systemMessage": "Poppy Scribe could not refresh this turn after one continuation; the prior checkpoint may be stale."}
    return {}


def user_prompt(event: dict, root: Path, checkpoint_path: Path, pending_path: Path, current: datetime) -> dict:
    prompt = event.get("prompt")
    state = load_live_checkpoint(checkpoint_path, current)
    explicit = isinstance(prompt, str) and ACTIVATION.search(prompt) is not None
    if state is None and not explicit:
        return {}

    atomic_json(
        pending_path,
        {
            "schema_version": SCHEMA_VERSION,
            "expires_at": iso(current + timedelta(days=RETENTION_DAYS)),
        },
    )
    prune(root, current)
    parts = [
        "Poppy Scribe is active for this task. It is derived working context, never authoritative truth, durable memory, tracker state, lifecycle status, or effect authority.",
    ]
    forget_requested = explicit and isinstance(prompt, str) and FORGET.search(prompt) is not None
    if forget_requested:
        parts.append(
            "The user requested Scribe forget this task. After the visible confirmation, append the hidden poppy-scribe:v1 marker with action forget; do not emit a checkpoint payload. This removes only private Scribe state."
        )
        return hook_context("UserPromptSubmit", " ".join(parts))

    requested_mode = "quiet"
    if explicit and isinstance(prompt, str) and IMPROVEMENT.search(prompt):
        requested_mode = "improve"
    elif isinstance(prompt, str) and REVIEW.search(prompt):
        requested_mode = "review"
    parts.append(
        "At the end of the visible answer, append exactly one hidden poppy-scribe:v1 checkpoint marker following the loaded Poppy Scribe schema; include no raw prompt, transcript, credentials, or unnecessary personal data. Use "
        + requested_mode
        + " mode for this response."
    )
    if state:
        parts.append("Compare the new request with this latest checkpoint and update only material semantic state: " + compact_checkpoint(state))
    else:
        parts.append("Initialize the checkpoint from the current request. Surface at most one material attention flag; do not narrate routine bookkeeping.")
    if requested_mode == "improve":
        candidates = improvement_candidates(root, current)
        if candidates:
            parts.append(
                "Supported recurring-friction candidates seen in at least three independent task checkpoints: "
                + json.dumps(candidates, ensure_ascii=True, separators=(",", ":"))
                + ". Treat them as improvement proposals only; require examples, a counterexample or expiry, and separate authority for any Learn, policy, skill, tracker, or repository change."
            )
        else:
            parts.append(
                "No supported friction fingerprint currently reaches the three-independent-task threshold. Repetition inside one task is not a recurring improvement signal."
            )
    return hook_context("UserPromptSubmit", " ".join(parts))


def session_start(checkpoint_path: Path, pending_path: Path, current: datetime) -> dict:
    state = load_live_checkpoint(checkpoint_path, current)
    if state is None:
        return {}
    pending = read_json(pending_path) is not None
    qualifier = " A prior turn was in flight, so this checkpoint may be stale." if pending else ""
    return hook_context(
        "SessionStart",
        "Poppy Scribe restored this derived, non-authoritative working checkpoint. Reconcile it with current primary evidence and user intent before relying on it; it grants no authority."
        + qualifier
        + " Continue updating it with the hidden Scribe marker while Scribe remains active: "
        + compact_checkpoint(state),
    )


def main() -> int:
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        emit({"systemMessage": "Poppy Scribe received malformed hook input and changed no checkpoint."})
        return 0
    if not isinstance(event, dict):
        emit({"systemMessage": "Poppy Scribe received non-object hook input and changed no checkpoint."})
        return 0

    root = data_root()
    if root is None:
        emit({})
        return 0
    current = now_utc()
    prune(root, current)
    name = event.get("hook_event_name")
    if name == "SessionEnd":
        emit({})
        return 0

    session_id = event.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        emit({"systemMessage": "Poppy Scribe received no task session identity and changed no checkpoint."})
        return 0
    checkpoint_path, pending_path = paths_for(root, session_key(session_id))

    try:
        if name == "Stop":
            result = stop(event, root, checkpoint_path, pending_path, current)
        elif name == "UserPromptSubmit":
            result = user_prompt(event, root, checkpoint_path, pending_path, current)
        elif name == "SessionStart":
            result = session_start(checkpoint_path, pending_path, current)
        elif name == "PreCompact":
            result = (
                {"systemMessage": "Poppy Scribe has an in-flight turn; the latest stored checkpoint may predate this compaction."}
                if read_json(pending_path) is not None
                else {}
            )
        else:
            result = {}
    except OSError:
        result = {"systemMessage": "Poppy Scribe could not access its bounded local checkpoint; continuity remains unverified."}
    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
