# Example project adapter

This synthetic example shows the minimum decisions a real project adapter should make. Replace every placeholder inside the project that owns the adapter; do not commit live paths or client identities to the Poppy product repository.

## Identity

- Project key: `atlas-demo`
- Project name: `Atlas Demo`
- Canonical repository: supplied by project-local configuration
- Canonical evidence root: supplied by project-local configuration

## Delivery controls

- Tracker: project-nominated structured tracker
- Base branch: project-nominated protected branch
- Work isolation: one writer in an isolated branch or worktree
- Deterministic gates: project unit, integration, and packaging tests
- Review: fresh Functional QA followed by fresh Final Assurance
- Publication: separately authorized only after both gates pass against the same candidate

## Coexistence

- Preserve existing repository rules and project-local delivery skills.
- Preserve human-authored notes, raw inputs, daily notes, and canonical pages.
- Extend an existing automation only after inspecting it; never create a duplicate cadence by default.
- Treat missing source identity, authority, or rollback evidence as Gray.
