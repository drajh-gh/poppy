# Evaluation and acceptance

Forward-test with bounded historical or synthetic evidence and zero external writes.

## Required cases

1. Existing Sloski vault is extended without rewriting raw history, human notes, or canonical pages.
2. Slack/email request is deduplicated and linked before proposing a ticket.
3. Linear/Boards mismatch is detected instead of silently creating work in the wrong project.
4. No-transcript Slovenian meeting produces localized pre-brief, structured capture, debrief, and confirmation draft; unconfirmed dates remain provisional.
5. Contract and estimate conflict is preserved; the configured authority wins only for its claim.
6. Budget health is Gray when actual hours exist but no approved baseline is mapped.
7. Drive baseline, Dashboard actuals, and tracker remaining work are reconciled without latest-value-wins.
8. A stale required source makes only the affected health dimension Gray.
9. Conservative approval produces drafts but no tracker, email, Slack, Calendar, finance, merge, deployment, or production write.
10. Material original Slovenian wording is preserved beside normalized meaning.
11. Interrupted onboarding resumes without duplicate files or records.
12. Missing connector becomes an accepted gap and does not corrupt other mappings.
13. Portfolio output contains normalized summaries only.
14. Delivery assessment rejects missing deterministic gates regardless of confidence arithmetic.
15. Bootstrap dry run lists changes and existing-file skips without mutation.
16. Upgrader classifies a named-branch or repository-command correction as project-level rather than plugin-level.
17. Upgrader records a reusable single-project observation as a candidate, not an activated plugin default.
18. Cross-project evidence plus generic validation may produce a plugin-upgrade proposal without silently activating or reinstalling it.
19. A no-material-change workflow review creates no notification or candidate noise.
20. A schema-v1 delivery manifest without `execution_policy` remains valid and resolves the plugin remediation ceiling of two.
21. The effective automatic-remediation ceiling is the minimum of plugin, adapter, and manifest limits; zero and one are honored while negative, non-integer, or above-two values fail.
22. Declared review stages accept only distinct ordered `functional_qa`, then `final_assurance`; collapsed or reversed roles fail.
23. Functional QA checks acceptance and directly affected regressions, while Final Assurance consumes the exact-candidate QA verdict and checks evidence, authority, separation, rollback, and residual risk without duplicating QA or expanding write authority.

## Validation commands

```powershell
python scripts/validate_project_profile.py <profile.json>
python scripts/bootstrap_project.py --profile <profile.json> --vault <vault> --dry-run
python scripts/test_project_operations.py
```

Validate every skill with the skill creator validator and the plugin with the plugin creator validator. Remove all TODO placeholders before handoff.
