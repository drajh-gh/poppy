---
name: poppy-delivery
description: Compose product, design, software engineering, testing, release, and project-specific skills from recommendation through verified implementation. Use behind Poppy for delivery work; directly invokable for focused testing.
---

# Poppy Delivery

Read [delegation and delivery](../../references/delegation-and-delivery.md), [authority and effects](../../references/authority-and-effects.md), and [evidence and assurance](../../references/evidence-and-assurance.md).

Invoke `poppy-context` before substantive project mutation if the project has not been oriented in this task.

## Compose the right expertise

Inspect the skills available in the current task and project. Load only the product, design, frontend, backend, data, testing, security, release, or other specialist guidance that could materially change the result. Project-specific instructions and skills remain authoritative within their scope.

Load detailed guidance only when the situation calls for it:

- terminology, context boundaries, or current-versus-intended behavior: [domain modeling](../../references/domain-modeling.md);
- incoming tracked work, readiness, or an untrusted contribution: [work intake](../../references/work-intake.md);
- architecture health, refactoring candidates, module/interface design, or dependency seams: [architecture and design](../../references/architecture-and-design.md);
- a bounded runnable or visual learning artifact: [prototype to learn](../../references/prototype-to-learn.md);
- diagnosis-only, diagnose-and-fix, test-first, regression-first, characterization, or alternate observable feedback: [diagnosis and test-first delivery](../../references/diagnosis-and-test-first-delivery.md);
- a specification, PRD, implementation brief, acceptance contract, or ticket decomposition/publication: [specification and tickets](../../references/specification-and-tickets.md);
- Git already stopped on a merge, rebase, cherry-pick, or revert conflict: [Git conflict resolution](../../references/git-conflict-resolution.md); and
- a guided checklist, helper, or effectful setup procedure: [human-guided procedures](../../references/human-guided-procedures.md).

## Move work forward

1. Establish the originating stakeholder wording, user outcome, observed current behavior, intended behavior, constraints, acceptance signal, and authorized target.
2. For a material business-behavior change, bind delivery to the smallest useful behavioral contract: the reported scenario, confirmed invariant, representative lifecycle or boundary cases, non-goals, decision owner, and observable acceptance. A reported example proves that case exists; it does not define the general policy. If a material item remains unsettled, return to intake or discovery instead of mutating behavior.
3. Bring in missing perspectives and recommend the smallest coherent vertical slice with material tradeoffs. Do not combine independently valuable requests merely because they touch the same subsystem.
4. Preserve existing changes. Stop if the intended edit overlaps them.
5. Implement in the authorized working tree. Use an ephemeral native plan only when dependencies matter.
6. Run targeted checks first, then broader checks sequentially when risk warrants them.
7. For a user-visible change that needs the user's judgment before PR preparation, create the smallest faithful visual-evidence packet described in [evidence and assurance](../../references/evidence-and-assurance.md). Use screenshots for static states and short video for interaction or motion when supported; do not install tooling merely to obtain a preferred medium.
8. Present the candidate-bound evidence and pause PR preparation for the user's explicit `ACCEPT`, `REJECT`, or `REQUEST_CHANGES` decision. Route rejection or requested changes back through the authorized implementation path, and recapture after any relevant candidate change. Missing or unfaithful capture remains unverified rather than being substituted with a claim.
9. Use `poppy-assure` for a fresh read-only pass when uncertainty, blast radius, or release consequence warrants independence.
10. Before a task, phase, or worktree transition, preserve every still-needed candidate through the artifact checkpoint in delegation and delivery; do not treat an ephemeral workspace as a durable deliverable.
11. Report the behavior changed, exact verification, candidate-acceptance decision when applicable, limitations, and every later acceptance state that remains unverified or conflicted.

Continue in the informed task by default. Delegate only when its expected decision or delivery value exceeds the context and integration cost. Keep one writer per target. Give any delegated writer an isolated worktree and explicit file boundary; all other delegates remain read-only. Root integrates and verifies the candidate.

Visual acceptance qualifies only the displayed candidate. It does not authorize a commit, push, pull request, merge, publication, deployment, dependency addition, installation, or other external effect. Obtain the authority required for each exact effect separately.
