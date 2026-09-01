# Causal diagnosis

Use this playbook when the requested outcome is to establish or narrow the cause of an observed defect, incident, or performance regression without changing the candidate.

## Diagnose with the tightest faithful loop

Define expected and observed symptoms, exact candidate, environment, and material constraints. Choose the tightest feasible sufficiently repeatable read-only loop. Reproduce and minimize while preserving fidelity. Do not impose fixed seconds, absolute determinism, parallel stress, or arbitrary iteration counts.

Keep a small ranked set of hypotheses. Each has an explicit prediction and a probe that can support, contradict, conflict with, or leave it unverified. Change one evidentiary variable at a time. Prefer a debugger, REPL, targeted query, bounded bisection, or existing diagnostic surface over broad logging.

For performance regressions, establish a baseline and use targeted profiling, query plans, controlled comparison, or bounded bisection. Respect project resource limits and never run CPU-intensive gates concurrently.

Diagnosis evidence records:

- expected and observed symptom;
- candidate identity and context;
- loop procedure, redacted result, fidelity, repeatability, and cost;
- reproduction and minimization result;
- ranked hypotheses with evidence status;
- root-cause claim status;
- absent or available regression seam;
- sensitive or retained artifact limitations; and
- smallest next authorized probe or Delivery handoff.

If a faithful loop is unavailable, return falsifiable unverified hypotheses and evidence requests—never a supported root-cause claim. A failure signal is not its cause.

## Remain read-only

Do not edit the repository, add instrumentation or tests, delete artifacts, write memory, commit, or cause an external effect. Repository instrumentation and harness changes belong to authorized Delivery. Production instrumentation is prohibited by this playbook.

Redact secrets, authorization headers, production rows, personal data, and sensitive evidence. If redaction removes the deciding signal, the root-cause claim remains unverified.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed diagnosing guidance pinned at revision `321658273cb1d20b76026717d027d505790106d4`:

- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/diagnosing-bugs/SKILL.md
