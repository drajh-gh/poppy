---
name: project-ops-automate
description: Configure, inspect, deconflict, update, or retire Codex automations for Project Operations cadences. Use when a user wants recurring project health checks, weekly planning, monthly governance, external research, workflow improvement, meeting follow-ups, portfolio refreshes, reminders, monitoring, or changes to an existing Project Operations schedule.
---

# Project Operations automation

Read [automation and cadence](../../references/automation-and-cadence.md), [task orchestration](../../references/task-orchestration.md), [project profile schema](../../references/project-profile-schema.md), [health and cadence](../../references/health-and-cadence.md), and [approval policy](../../references/approval-and-risk.md).

1. Read the confirmed project profile and identify the requested control purpose.
2. Use the Codex automation tool to inspect matching existing automations before proposing a new one. If a project-specific automation is visible on disk, use it only to resolve its identifier and current fields; never edit its TOML directly.
3. Recommend the smallest useful cadence and notification policy. Prefer a heartbeat attached to the current task unless the user explicitly asks for standalone project work.
4. Show the proposed name, purpose, schedule in local human-readable time, target, expected outputs, no-change behavior, and external side effects.
5. Ask for explicit confirmation before creating, changing, enabling, disabling, or deleting an automation.
6. Rehearse the proposed prompt manually against the project contract before activation. Operational prompts explicitly invoke `project-ops-manager` and `project-ops-memory`. Research prompts explicitly invoke `project-ops-researcher` and `project-ops-memory`, keep repositories `inspect-only`, and hand actionable findings to `project-ops-upgrader` without applying them.
7. Use the automation tool, preserving all unspecified fields when updating.
8. Record the automation identifier and purpose in the project profile or onboarding receipt only after successful creation or update.

When a scheduled prompt delegates, rehearse the root-only authority, depth-1, bounded fan-out,
event-only update, closure-card, and root-archive approval behavior. Task-hygiene prompts may read
only a validated normalized snapshot and must mark missing compatible coverage Gray; they never
inspect private Codex task storage.

Never create competing automations for the same project and control purpose. Prefer one consolidated weekday changed-only loop with Friday semantic lint and first-Monday governance. Never put notification preferences inside the automation prompt, expose raw recurrence rules to the user, create a cron workaround for a heartbeat, or silently alter an existing project control loop.
