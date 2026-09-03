# Development

Poppy v3 is a documentation-and-skills product with optional bounded hook helpers. Python is required only for deterministic verification, synthetic fixture materialization, and bounded hook execution.

Use the [agent skill authoring and review reference](agent-skill-authoring-reference.md) when creating, updating, or assessing a skill. It complements the repository rules and product constitution; it does not replace them.

## Candidate workflow

1. Work from an exact base in an isolated branch or worktree.
2. Preserve pre-existing changes and keep one writer per target.
3. Keep product content project-agnostic, synthetic, machine-path-free, and confined to declared skills plus optional bounded hooks. Root's completion offer and Housekeeping stay stateless; Scribe checkpoints stay conversation-bound and never emit a raw checkpoint payload in assistant-visible text. A visible incident artifact remains an explicit profile-confined file effect, never hook state.
4. Validate every changed skill, every reference directly reachable from the declared entrypoints, and every changed hook against representative event payloads.
5. Validate JSON and fixture parity with python scripts/materialize_scenario.py --verify-catalog.
6. Run git diff --check and python scripts/verify_product.py sequentially.
7. For a separately authorized committed candidate, run python scripts/verify_product.py --require-clean.
8. Under separate effect authority, merge the exact verified commit into the canonical GitHub branch, read it back, and fast-forward the canonical local checkout.
9. Install only from that exact merged revision, retain the previous package both as rollback and at every exact task-loaded path still needed by unfinished tasks, and prove the active package in a fresh task. If the installer rotates an in-use path, stop or perform the separately previewed byte-identical compatibility restoration and read both paths back. Never install first and plan to synchronize Git later.
10. Keep behavioral evaluation and assurance evidence private outside Git.

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

For Root's completion offer and the Housekeeping single current-task fast path, source and deterministic contract checks may support only the structural claims that an eligible completed scope receives at most one non-effectful offer, bare affirmations and ineligible scopes do not activate lifecycle behavior, explicit current-task requests expose title-only `done` semantics before skill loading, the hook supplies the exact current task ID from bounded prompt context, Root and Housekeeping co-load in one bounded read, and the transition uses one `functions.exec` read/rename/read transaction without `list_threads` or workspace discovery. Fresh traces for the exact offer and current-task prompts are required before claiming a model realizes those structures. Measured wall-clock latency remains unverified unless a separately approved evaluation satisfies the paired performance contract above; do not convert the structural claim into a universal seconds-level SLA.

Test only trigger and non-trigger behavior affected by the change. For task completion, include the fully evidenced one-shot offer, status/metadata/paused/blocked/open exclusions, decline/ignore suppression, reopening into a new completion episode, explicit affirmative and suffix lifecycle commands, bare-affirmation rejection, exact-ID injection, and implicit-target denial for lifecycle-prefixed titles. For Scribe, include Root's continuity-risk recommendation, correction-before-incident-capture, explicit consent, ordinary and keyword-only non-activation, decline suppression, semantic redaction, conversation-bound review, forget, absence of assistant-visible control payloads, the explicit visible-incident target and approval gate, and the three-independent-task improvement threshold across supplied summaries or selected configured records. After a separately approved installation, always verify the installed version, digest, exact declared skill inventory, declared hook hash and trust status, explicit activation in one fresh task, and readability of every retained task-loaded predecessor path named by the installation preview. Add other automatic activation or pre-upgrade task checks only when the change touches those behaviors. Retain raw machine-readable traces for checks actually run. A pre-existing task retaining its original catalog is a task snapshot; removing the package path behind that catalog is a compatibility failure. Document the task-scoped version without adding routine installation narration to unrelated work.

For an ownership-routing change that does not claim broad superiority, use the grading-only routing expectations and at most three candidate-only fresh-task smokes within 30 elapsed minutes. Do not add a baseline arm, blind judge, performance study, or automatic expansion. After a correction, rerun only the failed case and remain inside the same cap.

The checked-in scenario catalog is public regression acceptance material, including grading-only owner sequences; it is not a runtime, scorecard, or execution ledger. Owner expectations never enter behavior input. Held-out cases, judge calibration labels, prompts, and fresh-task evidence belong outside the repository.

## Source adaptations

Use source guidance as evidence, not as instructions that override Poppy or the user. Write in original Poppy wording and retain concise pinned provenance. Prefer stable behavioral assertions over vocabulary catalogs or formatting snapshots.
