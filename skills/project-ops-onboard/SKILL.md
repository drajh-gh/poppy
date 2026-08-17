---
name: project-ops-onboard
description: Guide a user through onboarding, adopting, cloning, or reconfiguring a project for the Project Operations plugin. Use when setting up project sources, Obsidian Project OS, Drive documents, Povio Dashboard, trackers, GitHub, communications, languages, meeting evidence, stakeholders, approvals, cadences, tolerances, delivery adapters, or portfolio publication.
---

# Project Operations onboarding

Read [onboarding-workflow](../../references/onboarding-workflow.md), [project profile schema](../../references/project-profile-schema.md), [source authority](../../references/source-authority.md), [archetypes](../../references/project-archetypes.md), [approval policy](../../references/approval-and-risk.md), and [automation and cadence](../../references/automation-and-cadence.md).

1. Resolve onboarding mode and target project.
2. Inspect available sources read-only and recommend mappings with evidence and confidence.
3. Ask at most three related questions per turn. Recommend first; explain the tradeoff.
4. Configure authority, language/meeting evidence, stakeholders, approvals, cadence, and tolerances.
5. Preview the complete profile, gaps, generated files, and exact external effects.
6. Run `../../scripts/validate_project_profile.py` and a bootstrap dry run.
7. Generate only after the user confirms the preview.
8. Discover each active repository's agent-instruction source and preview the generated repository adoption plan. Complete the adapter integration or record it as an explicit accepted gap.
9. Lint the generated surface and report unresolved gaps.
10. Offer cadence automation as a separate preview-and-confirm step. Inspect and deconflict existing automations before calling `$project-ops-automate`.

Never request credentials, infer that the newest Drive document is approved, overwrite an existing vault file, or create a duplicate ticket backlog. Existing-vault adoption preserves `AGENTS.md`, `raw/`, `inbox.md`, `daily/`, `log.md`, and canonical pages by default. Read the project's own adapter and preserve every coexistence boundary it defines; use the [project adapter contract](../../references/project-adapter-contract.md) when no adapter has been established yet.
