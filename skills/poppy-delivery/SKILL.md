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

1. Establish the user outcome, current behavior, constraints, acceptance signal, and authorized target.
2. Bring in missing perspectives and recommend the smallest coherent solution with material tradeoffs.
3. Preserve existing changes. Stop if the intended edit overlaps them.
4. Implement in the authorized working tree. Use an ephemeral native plan only when dependencies matter.
5. Run targeted checks first, then broader checks sequentially when risk warrants them.
6. Use `poppy-assure` for a fresh read-only pass when uncertainty, blast radius, or release consequence warrants independence.
7. Report the behavior changed, exact verification, limitations, and unverified or conflicted evidence.

The owner prefers adaptive delegation when useful. Keep one writer per target. Give any delegated writer an isolated worktree and explicit file boundary; all other delegates remain read-only. Root integrates and verifies the candidate.

Do not commit, push, open or merge a pull request, add a dependency, install software, deploy, or alter an external system unless the user authorizes that exact effect.
