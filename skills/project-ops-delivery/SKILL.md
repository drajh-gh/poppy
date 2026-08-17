---
name: project-ops-delivery
description: Orchestrate an explicitly approved project delivery manifest through isolated implementation, bounded specialists, deterministic gates, distinct Functional QA and Final Assurance, bounded remediation, draft PR or structured handoff, verification, and Obsidian receipt. Use for multi-agent ticket delivery while preserving project-specific repository, tracker, test, release, and approval rules.
---

# Project Operations delivery

Read [delivery orchestration](../../references/delivery-orchestration.md), [project adapter contract](../../references/project-adapter-contract.md), [approval policy](../../references/approval-and-risk.md), [local execution safety](../../references/local-execution-safety.md), and [operational controls](../../references/operational-controls.md), then read the project's own delivery adapter and repository rules. Apply the local execution gate before any R1 or R2 repository mutation. Compose project-local preparation, orchestration, assessment, and lifecycle skills when they exist; do not replace them with generic behavior.

1. Validate the schema-v1 immutable dispatch manifest, current base, and project adapter. Enumerate every adapter-nominated project extension, require one structured `required` or `not-applicable` declaration with rationale and evidence for each, and validate the nominated IDs with `validate_delivery_manifest.py --required-extension <id>`. Resolve the automatic-remediation ceiling as the minimum of the plugin ceiling of two and any stricter adapter or manifest limit; reject every declared value outside `0..2`.
2. Create one parent run, isolated branch/worktree, and sole writer.
3. Delegate only bounded evidence or specialist tasks with explicit output and mutation boundaries.
4. Freeze the revision, validated extension declarations, and evidence packet before review. Keep project-specific execution and closure rules in the adapter.
5. Run a separate fresh Functional QA task against the exact candidate. Check only the approved outcome and directly affected regressions.
6. After Functional QA passes, run a separate fresh Final Assurance task against the same candidate and verdict. Check identity, deterministic and hosted evidence, authority, separation, external effects, rollback, and residual risk without repeating QA or inventing criteria.
7. Route rejection findings through the orchestrator to the sole writer, rerun affected gates, and count every automatic remediation against the one shared effective ceiling. A changed candidate invalidates both review verdicts and restarts at Functional QA.
8. Stop when the effective remediation ceiling is exhausted or on any scope, budget, evidence, or authority exception.
9. Perform only adapter- and manifest-approved R0–R2 actions. A stricter project adapter always wins.
10. Prepare a one-stop approval packet for any R3 action. A release-readiness claim separately records source revision, artifact digest, build, delivery/store event, and runtime evidence; any missing or mismatched link remains Gray.
11. Verify exact completion and capture one compact receipt.

If `execution_policy` is absent, retain the schema-v1 defaults of two automatic remediations and ordered `functional_qa`, then `final_assurance`. Backlog readiness and either review verdict are not dispatch or write approval. Never merge, deploy, mutate production, send client communication, or broaden scope without exact authority.
