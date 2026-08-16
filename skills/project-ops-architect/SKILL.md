---
name: project-ops-architect
description: Design Poppy's architecture capability for initializing, adopting, or reconfiguring a project's evidence-backed operating system. Use behind Poppy for source authority, Project OS structure, profiles, adapters, approval boundaries, cadences, gates, workflow architecture, or reusable-versus-project configuration; direct invocation remains available when explicitly named.
---

# Project Operations architecture capability

Read [architecture](../../references/architecture.md), [onboarding workflow](../../references/onboarding-workflow.md), [project profile schema](../../references/project-profile-schema.md), [approval policy](../../references/approval-and-risk.md), and [delivery orchestration](../../references/delivery-orchestration.md).

1. Establish objectives, archetype, sources, authority, constraints, and accepted gaps.
2. When Poppy is active, return bounded source-discovery or adapter-analysis nodes to Poppy; Poppy alone decides whether to delegate them.
3. Design the smallest project-neutral core plus explicit project adapter.
4. Route onboarding mechanics through `project-ops-onboard`; route memory construction through `project-ops-memory`.
5. Define approval boundaries, cadences, research themes and repository access, deterministic gates, handoffs, and rollback.
6. Preview generated artifacts and external effects before applying them.
7. Validate the profile, scaffold, adapter, and source-authority map.
8. Return the validated operating design and typed follow-on needs to Poppy for onboarding, operations, research, or improvement routing.

Do not encode project-specific commands or terminology as plugin defaults, duplicate authoritative trackers, or treat architectural confidence as mutation authority.
