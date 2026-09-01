# Architecture assessment

Use this reference to select an architecture direction, including a justified no-change outcome. Detailed implementation design and candidate mutation are later Delivery work.

## Assess a bounded decision

Name the scope and decision. Read applicable project instructions, domain language, architecture decisions, and source authority without assuming fixed filenames or defaulting to a whole-repository scan.

Combine evidence proportionately from code structure, dependency and call paths, contracts, tests, defects, operational evidence, and bounded history. Git churn is one signal, never a required or dominant proxy. A topology diagram, import edge, visual adjacency, or structural reachability shows possible relationship; it does not by itself establish runtime causality, ownership, failure propagation, or blast radius.

Consider deletion and simplification, ownership and cohesion, coupling, effect boundaries, contracts and interface burden, observability, dependency direction, module depth, migration, and recovery. For each viable direction report:

- affected scope and direct evidence;
- observed friction;
- proposed direction, not implementation detail;
- expected benefit and tradeoffs;
- conflicts with existing decisions;
- unverified or conflicted claims; and
- what would show that no change is preferable.

Recommend one direction when evidence supports it, but allow a justified no-change outcome. Stop for selection before implementation design or mutation. Selection authorizes detailed exploration only.

## Compare alternatives proportionately

For consequential or genuinely ambiguous choices, optionally design the direction twice at decision altitude. Compare structurally distinct alternatives on locality, leverage, ownership, failure behavior, migration, testability, reader load, and recovery. Alternatives may be reasoned serially or delegated when useful; no agent count or parallel execution is mandatory.

Visual explanation is optional and must have accessible text equivalence. An assessment does not authorize implementation, documentation capture, or durable memory.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed guidance reviewed at source revision `321658273cb1d20b76026717d027d505790106d4`:

- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/improve-codebase-architecture/SKILL.md
- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/codebase-design/SKILL.md

The reader-load heuristic is adapted in original Poppy wording from Cursor's MIT-licensed guidance pinned at revision `68836ddaf5697224520f1847d90cdb90ca8babaa`:

- https://github.com/cursor/plugins/blob/68836ddaf5697224520f1847d90cdb90ca8babaa/pstack/skills/principle-minimize-reader-load/SKILL.md
