#!/usr/bin/env python3
"""Deterministically lint Project Operations structure and lifecycle invariants."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path


OPERATIONAL_TYPES = {
    "budget-snapshot",
    "change-request",
    "commitment",
    "health-snapshot",
    "improvement-candidate",
    "meeting-note",
    "milestone",
    "portfolio-summary",
    "raid-item",
    "stakeholder",
}
WIKILINK = re.compile(r"!?(?:\[\[)([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
FOLDER_FILTER = re.compile(r'file\.inFolder\("([^"]+)"\)')


def markdown_files(vault: Path) -> list[Path]:
    return sorted(
        path
        for path in vault.rglob("*.md")
        if "archive" not in path.relative_to(vault).parts and ".obsidian" not in path.parts
    )


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip('"\'')
    return values


def word_count(text: str) -> int:
    body = text.split("\n---", 1)[-1] if text.startswith("---") else text
    body = re.sub(r"[`#>*_\[\]()-]", " ", body)
    return len(re.findall(r"[\w'-]+", body, flags=re.UNICODE))


def resolve_project_key(vault: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    profile = json.loads((vault / "project-ops.json").read_text(encoding="utf-8"))
    return str(profile["project"]["key"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("vault", type=Path)
    parser.add_argument("--project-key")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()
    vault = args.vault.resolve()
    project_key = resolve_project_key(vault, args.project_key)
    root = vault / "wiki" / project_key
    errors: list[str] = []
    warnings: list[str] = []

    if not root.is_dir():
        errors.append(f"missing canonical project root: {root}")
    if not (root / "current.md").is_file():
        errors.append("missing canonical current.md")
    if not (root / "index.md").is_file():
        errors.append("missing canonical index.md")
    for nested in vault.glob("**/.obsidian"):
        if nested.parent != vault and "archive" not in nested.relative_to(vault).parts:
            errors.append(f"nested vault configuration: {nested.relative_to(vault)}")

    files = markdown_files(vault)
    text_by_path = {path: path.read_text(encoding="utf-8-sig") for path in files}
    meta_by_path = {path: frontmatter(text) for path, text in text_by_path.items()}
    active_health: list[Path] = []
    hashes: dict[str, list[Path]] = defaultdict(list)
    for path, text in text_by_path.items():
        relative = path.relative_to(vault)
        meta = meta_by_path[path]
        note_type = meta.get("type", "")
        if root in path.parents and not meta:
            warnings.append(f"canonical note lacks frontmatter: {relative}")
        if note_type in OPERATIONAL_TYPES:
            errors.append(f"legacy direct operational type {note_type}: {relative}")
        if meta.get("status") in {"blocked", "overdue", "approved", "at-risk", "red", "yellow", "green"}:
            errors.append(f"operational value in knowledge status: {relative}")
        if root in path.parents and meta.get("type") == "analysis" and meta.get("record_kind") == "health-snapshot" and meta.get("status") == "current":
            active_health.append(path)
        if root in path.parents and meta.get("status") != "superseded" and path.name not in {"current.md", "index.md"} and word_count(text) < 35:
            warnings.append(f"thin canonical note (<35 words): {relative}")
        normalized = re.sub(r"\s+", " ", text.casefold()).strip()
        if root in path.parents and normalized:
            hashes[hashlib.sha256(normalized.encode()).hexdigest()].append(path)

    if len(active_health) > 1:
        errors.append("multiple current health snapshots: " + ", ".join(str(p.relative_to(vault)) for p in active_health))
    current = root / "current.md"
    if current in text_by_path:
        words = word_count(text_by_path[current])
        if words > 1200:
            errors.append(f"current.md exceeds hard cap: {words} words")
        elif words > 750:
            warnings.append(f"current.md exceeds orientation budget: {words} words")
    for paths in hashes.values():
        if len(paths) > 1:
            warnings.append("exact duplicate canonical notes: " + ", ".join(str(p.relative_to(vault)) for p in paths))

    by_stem: dict[str, list[Path]] = defaultdict(list)
    by_rel: dict[str, Path] = {}
    for path in files:
        by_stem[path.stem.casefold()].append(path)
        by_rel[path.relative_to(vault).with_suffix("").as_posix().casefold()] = path

    def resolve(target: str) -> Path | None:
        key = target.replace("\\", "/").strip(" /").casefold()
        if key in by_rel:
            return by_rel[key]
        matches = by_stem.get(Path(key).name.casefold(), [])
        return matches[0] if len(matches) == 1 else None

    graph: dict[Path, set[Path]] = defaultdict(set)
    for path, text in text_by_path.items():
        for target in WIKILINK.findall(text):
            resolved = resolve(target)
            if resolved:
                graph[path].add(resolved)

    seeds = [path for path in (vault / "Start Here.md", root / "index.md") if path.exists()]
    reached = set(seeds)
    queue = deque(seeds)
    while queue:
        for linked in graph[queue.popleft()]:
            if linked not in reached:
                reached.add(linked)
                queue.append(linked)
    orphans = [
        path for path in files
        if root in path.parents and path not in reached and meta_by_path[path].get("status") != "superseded"
    ]
    if orphans:
        warnings.append(
            "unreachable canonical notes: "
            + ", ".join(str(path.relative_to(vault)) for path in orphans)
        )

    for base in sorted((vault / "dashboards").glob("*.base")):
        text = base.read_text(encoding="utf-8")
        for folder in FOLDER_FILTER.findall(text):
            if not (vault / folder).is_dir():
                errors.append(f"Base targets missing folder {folder}: {base.relative_to(vault)}")
        direct = re.findall(r'type == "([^"]+)"', text)
        for note_type in direct:
            if note_type in OPERATIONAL_TYPES:
                errors.append(f"Base filters legacy direct type {note_type}: {base.relative_to(vault)}")

    print(f"Project Operations vault: {vault}")
    print(f"Project: {project_key}; markdown: {len(files)}; canonical: {sum(root in p.parents for p in files)}")
    for item in errors:
        print(f"ERROR: {item}")
    for item in warnings:
        print(f"WARN: {item}")
    print(f"RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
