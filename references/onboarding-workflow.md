# Onboarding workflow

Run a resumable, recommendation-first wizard:

```text
Discover -> Recommend -> Confirm -> Generate -> Validate
```

Modes: `new-project`, `adopt-existing-vault`, `clone-project-archetype`, and `reconfigure-project`.

## Interaction contract

- Ask no more than three related questions per interaction.
- Put the recommended option first and explain the evidence or tradeoff.
- Inspect configured sources read-only and prefill only what can be proved.
- Never request credentials or make an external write during onboarding.
- Allow `confirm`, `change`, `exclude`, or `configure later` for each mapping.
- Persist the last completed step so onboarding can resume idempotently.

## Stages

1. Identify project, client, stage, migration mode, data isolation, and vault.
2. Discover Obsidian, Drive, Povio Dashboard, tracker, GitHub, Slack, Gmail, Calendar, and recurring meetings.
3. Recommend a primary archetype and overlays.
4. Capture objectives, next milestone, commercial model, currency, and authoritative contract/estimate/budget sources.
5. Confirm the source-authority matrix and contradiction policy.
6. Configure working/client languages, transcript quality, meeting evidence, glossary, and communication style.
7. Protect human-owned vault surfaces and confirm portfolio publication policy.
8. Confirm stakeholders, decision rights, and approvers.
9. Select approval preset and exact external-write boundaries.
10. Confirm cadence, quiet hours, destinations, changed-only notifications, research themes, and inspect-only repository policy. Leave research automation disabled unless explicitly activated after rehearsal.
11. Recommend archetype-specific RAG tolerances and allow adjustment.
12. Discover every active repository's agent-instruction source and preview a compact repository memory adapter; never edit generated instruction outputs directly.
13. Preview source map, authority map, artifact plan, repository-adoption plan, gaps, and exact external effects.
14. Run a zero-write dry report over bounded historical evidence.
15. Generate files only after confirmation, then validate and lint.

## Completion gates

Onboarding is complete only when required mappings are confirmed or accepted as gaps, every material claim has an authority or Unknown state, human-owned files are protected, approvals/language/cadence/tolerances are configured, every active repository has a validated memory adapter or an accepted gap, generated artifacts validate, and the dry run made zero unauthorized external writes.

Use `scripts/onboard_project.py` for deterministic profile generation and `scripts/bootstrap_project.py` for dry-run or confirmed vault scaffolding.
