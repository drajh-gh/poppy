# Implementation design

Use this reference after the outcome and architecture direction are sufficiently selected. It guides the shape of the candidate; it does not reopen settled product decisions.

## Design the selected change

Use interface depth, leverage, locality, deletion as a thought experiment, dependency categories, seam placement, module depth, and adapter count as heuristics—not universal laws.

- Do not require one interface per module.
- Do not universally avoid side effects or require dependency injection.
- A software adapter may be justified by ownership, protocol, security, deployment, or migration boundaries.
- Keep software adapters distinct from any historical Poppy project-adapter terminology.
- Prefer interfaces that hide meaningful complexity, localize change, and keep effect boundaries legible while preserving project vocabulary and conventions.

Include reader load in the tradeoff. Consider both the layers a maintainer must trace and the hidden or mutable state needed to predict behavior. Pass-through wrappers, duplicated abstractions, and interfaces that hide no meaningful decision are candidates for simplification. Do not impose an arbitrary timing metric, universal preference for pure functions, or fixed maximum layer count.

Classify dependencies only when it helps: stable or volatile, internal or external, effectful or pure, owned or third-party, synchronous or asynchronous. Place seams where independent change, testing, failure handling, security, or migration value outweighs added indirection.

Treat deletion as a thought experiment. If removing a module, adapter, abstraction, or test clarifies where responsibility would move, that evidence informs the design; it does not automatically authorize deletion.

## Preserve useful verification

Do not automatically delete lower-level tests. Preserve tests with unique defect, safety, compatibility, performance, or diagnostic value. Reconcile the portfolio around observable behavior and selected seams.

If implementation evidence contradicts the selected behavior or architecture premise, preserve the finding and return the material decision to Poppy Decide rather than silently redesigning the outcome.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed guidance reviewed at source revision `321658273cb1d20b76026717d027d505790106d4`:

- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/improve-codebase-architecture/SKILL.md
- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/codebase-design/SKILL.md

The reader-load heuristic is adapted in original Poppy wording from Cursor's MIT-licensed guidance pinned at revision `68836ddaf5697224520f1847d90cdb90ca8babaa`:

- https://github.com/cursor/plugins/blob/68836ddaf5697224520f1847d90cdb90ca8babaa/pstack/skills/principle-minimize-reader-load/SKILL.md
