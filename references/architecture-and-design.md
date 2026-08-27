# Architecture assessment and software design

Use the smallest applicable section. An architecture survey, a selected design, and implementation are distinct phases with separate stopping and authority conditions.

## Assess before designing

Name the bounded scope and decision. Read applicable project instructions, domain language, architecture decisions, and source authority without assuming fixed filenames. Do not default to a whole-repository scan.

Combine evidence proportionately from code structure, dependency and call paths, contracts, tests, defects, operational evidence, and bounded history. Git churn is one signal, never a required or dominant proxy.

Consider deletion and simplification, ownership and cohesion, coupling, effect boundaries, contracts and interface burden, observability, dependency direction, and module depth. For each candidate report:

- affected scope and direct evidence;
- observed friction;
- proposed direction, not detailed design;
- expected benefit and tradeoffs;
- conflicts with existing decisions;
- confidence plus unverified or conflicted claims; and
- what would show that no change is preferable.

Recommend one candidate when evidence supports it, but allow a justified no-change outcome. Stop for user selection before detailed design or implementation. Selection authorizes detailed exploration only.

## Design the selected change

Use interface depth, leverage, locality, deletion as a thought experiment, dependency categories, seam placement, module depth, and adapter count as heuristics—not universal laws.

- Do not require one interface per module.
- Do not universally avoid side effects or require dependency injection.
- One software adapter may be justified by ownership, protocol, security, deployment, or migration boundaries.
- Keep software adapters distinct from any historical Poppy project-adapter terminology.
- Prefer interfaces that hide meaningful complexity, localize change, and keep effect boundaries legible, while preserving project vocabulary and conventions.

Classify dependencies only when it helps: stable or volatile, internal or external, effectful or pure, owned or third-party, synchronous or asynchronous. Place seams where independent change, testing, failure handling, security, or migration value outweighs added indirection.

Treat deletion as a thought experiment: if removing a module, adapter, abstraction, or test clarifies where its responsibility would move, that evidence informs the design. It does not automatically authorize deletion.

## Tests and alternatives

Do not automatically delete lower-level tests. Preserve tests with unique defect, safety, compatibility, performance, or diagnostic value. Reconcile the portfolio around observable behavior and the chosen seams.

For consequential or genuinely ambiguous designs, optionally design it twice. Produce structurally distinct alternatives, compare locality, leverage, ownership, failure behavior, migration, testability, and recovery, then recommend one. Alternatives may be reasoned serially or delegated when useful; no agent count or parallel execution is mandatory.

Visual before/after explanation is optional and must have accessible text equivalence. Detailed design does not authorize implementation, documentation capture, or durable memory.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed guidance reviewed at source revision `321658273cb1d20b76026717d027d505790106d4`:

- https://github.com/mattpocock/skills/tree/main/skills/engineering/improve-codebase-architecture
- https://github.com/mattpocock/skills/tree/main/skills/engineering/codebase-design

