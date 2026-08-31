# Test-first delivery

Use this playbook when implementation benefits from an observable red/green feedback loop. It guides candidate mutation after the outcome or correction is sufficiently selected.

## Choose useful implementation feedback

Before mutation, run or record the relevant existing baseline when feasible. Follow project conventions and confirmed domain language. Choose the narrowest stable observable seam; ask the user only when the choice materially changes interface, scope, risk, or architecture.

Applicable modes include:

- conventional test-driven development;
- regression-first defect repair;
- legacy characterization; and
- alternate observable feedback for visual, performance, nondeterministic, generated, integration, or infrastructure work.

Work one coherent vertical slice at a time:

1. observe red for the expected reason;
2. implement the minimum coherent green behavior;
3. rerun targeted feedback;
4. optionally make a small behavior-preserving refactor; and
5. rerun before broader sequential gates.

Use independent expected values and coherent behavioral assertions. Do not rewrite tests merely to accommodate an implementation. Public-interface-only tests, no internal mocks, and one assertion per test are not universal rules. Prefer real collaborators, but mock unstable, slow, nondeterministic, destructive, expensive, or failure-producing boundaries when useful.

For a defect correction, add a regression test at a faithful seam when available, observe red then green, and rerun the original unminimized loop. Preserve lower-level tests with unique defect, safety, compatibility, performance, or diagnostic value. Missing verification remains unverified.

Remove temporary instrumentation from the candidate before assessment, but inventory all artifacts and follow their authorized disposition. A relevant candidate change invalidates earlier functional or assurance evidence.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed test-driven guidance pinned at revision `321658273cb1d20b76026717d027d505790106d4`:

- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/tdd/SKILL.md
