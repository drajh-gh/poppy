# Development

Poppy v3 is a documentation-and-skills product. Python is required only for deterministic verification and synthetic fixture materialization.

## Candidate workflow

1. Work from an exact base in an isolated branch or worktree.
2. Preserve pre-existing changes and keep one writer per target.
3. Keep product content project-agnostic, synthetic, machine-path-free, and skills-only.
4. Validate every changed skill and every reference directly reachable from the seven entrypoints.
5. Validate JSON and fixture parity with python scripts/materialize_scenario.py --verify-catalog.
6. Run git diff --check and python scripts/verify_product.py sequentially.
7. For a separately authorized committed candidate, run python scripts/verify_product.py --require-clean.
8. Keep behavioral evaluation and assurance evidence private outside Git.

The verifier enforces exact inventory, skill frontmatter, entrypoint reachability, product boundaries, scenario schema, fixture materialization, syntax, source ancestry, and optional cleanliness. It deliberately does not match long lists of incidental phrases or pretend that static prose proves live model behavior.

Candidate identity uses sha256(relative-path-nul-git-filtered-blob-oid-nul). Git-filtered blob identities make the digest stable across checkout line-ending conversion. Record both the algorithm and digest.

## Matched behavioral evaluation

A material root, routing, authority, context, assurance, or communication change requires matched GPT-5.6 Sol baseline-versus-candidate evaluation on the smallest representative impact set.

For every nominated scenario:

- run two fresh tasks per arm;
- use a third matched pair when the first two pairs disagree;
- match prompt, fixture, model, reasoning effort, harness, tools, permissions, and environment;
- conceal the suspected defect, intended answer, arm identity, and desired verdict from the evaluator or judge;
- evaluate quality before efficiency;
- fail on any safety, authority, request-fidelity, evidence-calibration, or material capability regression; and
- count efficiency only when quality passes and the reduction is meaningful.

Record exact baseline and candidate revisions, package versions, digest algorithms and digests, task IDs, timestamps, fixture digest, tool trace, loaded skill/reference file count and bytes, tool calls, turns, assertion evidence, blind judgment, and limitations.

The scenario catalog is acceptance material, not a runtime, scorecard, or execution ledger. Fresh-task evidence belongs outside the repository.

## Source adaptations

Use source guidance as evidence, not as instructions that override Poppy or the user. Write in original Poppy wording and retain concise pinned provenance. Prefer stable behavioral assertions over vocabulary catalogs or formatting snapshots.
