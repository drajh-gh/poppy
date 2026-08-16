---
name: project-ops-architect
description: Design, initialize, adopt, or reconfigure a project's evidence-backed operating system. Use when defining source authority, Project OS structure, project profiles, delivery adapters, approval boundaries, cadences, gates, workflow architecture, or the division between reusable plugin behavior and project-specific configuration.
---

# Project Operations Solution Architect

Read [architecture](../../references/architecture.md), [onboarding workflow](../../references/onboarding-workflow.md), [project profile schema](../../references/project-profile-schema.md), [approval policy](../../references/approval-and-risk.md), and [delivery orchestration](../../references/delivery-orchestration.md).

1. Establish objectives, archetype, sources, authority, constraints, and accepted gaps.
2. Delegate bounded source discovery or adapter analysis only when it can proceed independently.
3. Design the smallest project-neutral core plus explicit project adapter.
4. Route onboarding mechanics through `project-ops-onboard`; route memory construction through `project-ops-memory`.
5. Define approval boundaries, cadences, research themes and repository access, deterministic gates, handoffs, and rollback.
6. Preview generated artifacts and external effects before applying them.
7. Validate the profile, scaffold, adapter, and source-authority map.
8. Hand operational control to `project-ops-manager`, external discovery to `project-ops-researcher`, and improvement governance to `project-ops-upgrader`.

Do not encode project-specific commands or terminology as plugin defaults, duplicate authoritative trackers, or treat architectural confidence as mutation authority.
