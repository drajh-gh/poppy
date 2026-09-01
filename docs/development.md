# Development

Poppy v3 is a documentation-and-skills product with an optional stateless hook helper. Python is required only for deterministic verification, synthetic fixture materialization, and bounded hook execution.

Use the [agent skill authoring and review reference](agent-skill-authoring-reference.md) when creating, updating, or assessing a skill. It complements the repository rules and product constitution; it does not replace them.

## Candidate workflow

1. Work from an exact base in an isolated branch or worktree.
2. Preserve pre-existing changes and keep one writer per target.
3. Keep product content project-agnostic, synthetic, machine-path-free, and confined to declared skills plus optional stateless hooks.
4. Validate every changed skill, every reference directly reachable from the declared entrypoints, and every changed hook against representative event payloads.
5. Validate JSON and fixture parity with python scripts/materialize_scenario.py --verify-catalog.
6. Run git diff --check and python scripts/verify_product.py sequentially.
7. For a separately authorized committed candidate, run python scripts/verify_product.py --require-clean.
8. Keep behavioral evaluation and assurance evidence private outside Git.

The verifier enforces exact inventory, skill frontmatter, entrypoint reachability, hook shape and representative deterministic behavior, product boundaries, scenario schema, fixture materialization, syntax, source ancestry, and optional cleanliness. It deliberately does not match long lists of incidental phrases or pretend that static prose proves live model behavior.

Candidate identity uses sha256(relative-path-nul-git-filtered-blob-oid-nul). Git-filtered blob identities make the digest stable across checkout line-ending conversion. Record both the algorithm and digest.

## Proportionate behavioral evidence

Start with source review, the deterministic catalog, and the repository verifier. Add model-based baseline-versus-candidate evaluation only when those checks cannot establish a material changed behavior and the result can change the current decision. A broad superiority claim, rather than an ordinary candidate, requires the full paired-evaluation contract in the scenario catalog.

Before starting any model-based evaluation, record the exact decision question, selected scenarios, maximum model calls, maximum elapsed time, and stop condition. Without a separate approved budget, the ceiling is one scenario and one fresh task per arm. Never automatically resume, widen, or repeat a run after that boundary. If the bounded result is inconclusive, leave only the dependent claim unverified or ask for approval of a concrete expansion.

For every approved nominated scenario:

- run one fresh task per arm by default;
- add another matched pair only for a named material stochastic uncertainty and within the approved budget; if disagreement remains at the boundary, stop with an unverified comparison;
- match prompt, fixture, model, reasoning effort, harness, tools, permissions, and environment;
- give the behavior task only the authentic user prompt and fixture files or evidence; keep setup instructions, permissions, evidence limits, assertions, expected verification, arm identity, intended answer, and desired verdict judge-only;
- run read-only behavior tasks from a fresh empty disposable directory and record hashes of the exact rendered behavior and judge prompts;
- use deterministic graders first where state or effects are observable;
- use A/B and B/A semantic judging only when a subjective comparison is decision-bearing;
- require calibrated or human adjudication only when the current decision depends on that semantic judgment;
- freeze a separate private held-out set before repeated tuning or a broad capability claim, not for every ordinary release;
- evaluate quality before efficiency;
- fail on any safety, authority, request-fidelity, evidence-calibration, or material capability regression; and
- count efficiency only when quality passes and the reduction is meaningful.

Record exact baseline and candidate revisions, package versions, digest algorithms and digests, task IDs, timestamps, fixture digest, tool trace, loaded skill/reference file count and bytes, tool calls, turns, assertion evidence, blind judgment, and limitations.

For a latency or response-efficiency claim, separately approve the evaluation cost, then use at least five interleaved pairs on each route named by that claim. Report paired input and output tokens, loaded bytes, response characters, tool calls, turns, median latency, dispersion, outliers, cache state, and task success. Do not infer general speed from summed duration. When efficiency is not an acceptance item, its absence remains unverified and does not block a quality-only candidate.

Test only trigger and non-trigger behavior affected by the change. After a separately approved installation, always verify the installed version, digest, exact declared skill inventory, declared hook hash and trust status, and explicit activation in one fresh task. Add automatic activation, routine non-activation, or pre-upgrade task checks only when the change touches those behaviors. Retain raw machine-readable traces for checks actually run. If the host retains stale task catalogs, document that lifecycle limitation rather than adding version narration to Poppy.

For an ownership-routing change that does not claim broad superiority, use the grading-only routing expectations and at most three candidate-only fresh-task smokes within 30 elapsed minutes. Do not add a baseline arm, blind judge, performance study, or automatic expansion. After a correction, rerun only the failed case and remain inside the same cap.

The checked-in scenario catalog is public regression acceptance material, including grading-only owner sequences; it is not a runtime, scorecard, or execution ledger. Owner expectations never enter behavior input. Held-out cases, judge calibration labels, prompts, and fresh-task evidence belong outside the repository.

## Source adaptations

Use source guidance as evidence, not as instructions that override Poppy or the user. Write in original Poppy wording and retain concise pinned provenance. Prefer stable behavioral assertions over vocabulary catalogs or formatting snapshots.
