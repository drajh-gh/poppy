# Diagnosis and test-first delivery

Use this playbook when causal diagnosis or implementation benefits from an observable red/green feedback loop. Select only the applicable mode.

## Authority modes

- **Diagnosis-only:** read-only. Do not edit the repository, add instrumentation or tests, delete artifacts, write memory, commit, or cause an external effect. Return diagnosis evidence. If a faithful loop is unavailable, return a small ranked set of falsifiable unverified hypotheses and evidence requests—never a supported root-cause claim.
- **Diagnose-and-fix:** diagnose first, then enter authorized Delivery, functional verification, and final Assurance. Local harnesses, instrumentation, tests, and source changes use the existing mutation and one-writer gates. No automatic commit, push, pull request, deployment, production instrumentation, or artifact deletion.

## Diagnose with the tightest faithful loop

Define expected and observed symptoms, then choose the tightest feasible sufficiently repeatable loop within declared resource limits. Reproduce and minimize while preserving fidelity. Do not impose fixed seconds, absolute determinism, parallel stress, or arbitrary 100x/1000x iteration counts.

Keep a small ranked set of hypotheses. Each has an explicit prediction and a probe that can support, contradict, conflict with, or leave it unverified. Change one variable at a time. Prefer a debugger, REPL, targeted query, or tagged instrumentation over broad logging. Repository instrumentation is a write; production instrumentation is prohibited by this playbook.

For performance regressions, establish a baseline and use targeted profiling, query plans, controlled comparison, or bounded bisection. Respect the project's resource-safety policy and never run CPU-intensive gates concurrently.

Diagnosis evidence records:

- expected and observed symptom;
- candidate identity and context;
- loop procedure, redacted result, fidelity, repeatability, and cost;
- reproduction and minimization result;
- ranked hypotheses with evidence status;
- probes or instrumentation, authority, and cleanup state;
- performance evidence when relevant;
- root-cause claim status;
- regression-test status or absence of a faithful seam;
- retained artifact inventory and proposed disposition; and
- residual risks and next authorized action.

Redact secrets, authorization headers, production rows, personal data, and sensitive evidence. If redaction removes the deciding signal, the root-cause claim remains unverified.

## Choose implementation feedback

Before mutation, run or record the relevant existing baseline when feasible. Follow project conventions and confirmed domain language. Choose the narrowest stable observable seam; ask the user only when the choice materially changes interface, scope, risk, or architecture.

Available modes include:

- conventional test-driven development;
- regression-first defect repair;
- legacy characterization; and
- alternate observable feedback for visual, performance, nondeterministic, generated, integration, or infrastructure work.

Work one vertical slice at a time:

1. observe red for the expected reason;
2. implement the minimum coherent green behavior;
3. rerun the targeted feedback;
4. optionally make a small behavior-preserving refactor; and
5. rerun before broader sequential gates.

Use independent expected values and coherent behavioral assertions. Do not rewrite tests merely to accommodate an implementation. Public-interface-only tests, no internal mocks, and one assertion per test are not universal rules. Prefer real collaborators, but mock unstable, slow, nondeterministic, destructive, expensive, or failure-producing boundaries when useful.

For diagnose-and-fix, add a regression test at a faithful seam when available, observe red then green, and rerun the original unminimized loop. Preserve lower-level tests with unique defect, safety, compatibility, performance, or diagnostic value. Missing verification remains unverified.

Remove temporary instrumentation from the candidate before assessment, but inventory all artifacts and propose their disposition. A relevant candidate change invalidates earlier functional or assurance evidence.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed guidance pinned at revision `321658273cb1d20b76026717d027d505790106d4`:

- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/diagnosing-bugs/SKILL.md
- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/tdd/SKILL.md

