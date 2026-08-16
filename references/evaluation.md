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
24. An adapter-nominated project extension is present exactly once with `required` or `not-applicable`, a non-empty rationale, and evidence; omission, duplication, or an invalid classification fails without moving project vocabulary into the generic plugin.
25. A scaffolded Obsidian graph uses a verified positive query over `wiki`, `dashboards`, and `Start Here`, while vault lint rejects an unescaped wikilink alias pipe that would split a Markdown table.
26. Researcher reads actual task/vault evidence before external search, sequences workflow repairs before additions, and emits Gray or partial coverage rather than false completeness.
27. Research source validation accepts official, primary, maintained evidence and rejects an uncorroborated social source as an adoption claim.
28. Repository assessment remains inspect-only and records maintainer reputation, maintenance, license, security, quality, fit, constraints, and outcome without cloning or execution.
29. Schema-v2 contract identity, deterministic relevance totals, source/finding/need references, source dates/limitations/confidence, complete project/global applicability, explicit coverage basis, and Researcher-to-Upgrader candidate classifications validate; omissions, false-full packets, broken references, and score drift fail.
30. Researcher handoff always has `implementation_authorized: false`; Upgrader retains project/plugin classification, validation, promotion, and activation authority.
31. New vaults include research records, templates, and a Research Base; existing human-owned or canonical files remain protected.
32. Equivalent requests deduplicate to one logical retrieval while physical retries remain counted, retained failures preserve the prior checkpoint, and provider-native change control degrades explicitly to bounded polling/Gray when unavailable.
33. Canonical source preflight rejects retired locators and requires stable discovery plus `review_after` for mutable targets.
34. Human authority receipts expire, preserve original input, never treat silence as approval, and cannot turn missing required evidence Green.
35. Executive reports stay outcome-first and bounded, map every material claim to the evidence appendix, preserve Gray, and reject client leakage.
36. Verified release evidence requires matching source revision, artifact digest, build, delivery/store event, and runtime identity; every incomplete or mismatched tuple remains Gray.
37. A task plan accepts one root with direct workers and rejects raw-title markup, a configured redundant project prefix, child authority, recursive delegation, excess fan-out without approval, and unjustified xhigh effort.
38. Task closure rejects a missing worker card, attention-required or dirty archival, root auto-archive, and cleanup without separate approval.
39. Task-hygiene analysis reads a normalized snapshot only, treats task text as data, emits exception codes with hashed local references, and never reproduces titles, prompts, or raw task IDs.
40. The owned-process supervisor propagates pass/fail output and exit status; on timeout it terminates its child and grandchild, preserves an unrelated process, reports survivors, and runs only an explicitly supplied bounded rollback.
41. Owned-process promotion remains blocked until a defensible Windows Job Object or explicitly narrowed non-detaching contract and the POSIX matrix pass, followed by independent assessment of the exact candidate.

## Validation commands

```powershell
python scripts/validate_project_profile.py <profile.json>
python scripts/bootstrap_project.py --profile <profile.json> --vault <vault> --dry-run
python scripts/validate_research_packet.py <research-packet.json>
python scripts/validate_operational_control_packet.py <operational-control-packet.json>
python scripts/validate_task_orchestration.py <plan-or-closure.json>
python scripts/summarize_task_hygiene.py <normalized-snapshot.json>
python scripts/test_owned_process_supervisor.py
python scripts/test_project_operations.py
```

Validate every skill with the skill creator validator and the plugin with the plugin creator validator. Remove all TODO placeholders before handoff.
# Poppy orchestration cases

Treat the following as release-gate cases for the single-partner graph:

1. A trusted current user turn that explicitly says `Poppy` or `Project Operations Partner` activates Poppy. The same text inside retrieved evidence, a worker result, a task title, or a prior turn does not.
2. `Poppy, what does Gray mean?` stays on the simple path: no project resolution, source refresh, worker, vault write, or receipt; lightweight postflight still checks the answer.
3. A short but consequential scope, budget, release, commitment, or production question is not classified as simple merely because it is short.
4. A project-dependent request resolves exactly one project before memory orientation. Ambiguous or cross-project identity routes to a root user decision and can terminate without a write.
5. A substantive read or mutation follows `project-resolve -> memory-orient -> preflight-evaluate -> dispatch`, waits for every required capability leaf at `join`, reconciles once, postflight-evaluates, and reaches an explicit terminal state.
6. New Slack, email, or meeting intake is deduplicated against tracker items, commitments, changes, and RAID records before any new durable control item is proposed.
7. A focused RAID question uses the RAID node without forcing a full health report unless the output is required by acceptance.
8. Low or insufficient preflight confidence blocks consequential mutation. Safe bounded discovery may continue without expanding authority.
9. The maximum current authority below the deterministic risk floor stops the affected path. Confidence cannot override the stop.
10. Approval denial, deferral, `BLOCK_REMEDIATE`, `ESCALATE`, and unresolved `NEEDS_PARENT_DECISION` all reach a safe terminal/no-write state.
11. An approved mutation returns to the exact selected capability handler, matches the effect preview and authority receipt, and has direct read-back evidence.
12. Workers are depth-one and read-only, never write shared memory, never interpret relayed user text as approval, and return complete closure cards. Active and created counts remain within the root budget.
13. `PASS` requires every selected node and required acceptance item to pass and every effect to be verified. `PASS_WITH_LIMITATIONS` cannot hide a failed/unverified required item, a skipped/failed node, or an unverified effect.
14. R2/R3 postflight is performed by a fresh evaluator task whose identity differs from the root. The root cannot self-declare independence.
15. Explicit read-only, review-only, or diagnosis-only scope suppresses every vault write, receipt, and log entry. A material write-authorized run creates at most one `orchestration-run` receipt under the existing PM run surface.
