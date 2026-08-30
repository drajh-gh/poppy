# Domain modeling

Use this discipline when terminology, context boundaries, lifecycle, exceptions, authority, or current-versus-intended behavior could materially change a decision or implementation.

## Model claims, not just words

For each material term distinguish:

- source wording and source authority;
- observed meaning in current evidence;
- proposed canonical wording;
- confirmed decision and approver;
- aliases, translations, deprecated terms, and audience-specific wording; and
- ambiguity that remains prohibited, unverified, or conflicted.

Challenge fuzzy or conflicting language with concrete edge cases. Test boundaries, lifecycle transitions, exceptions, authority, current versus intended behavior, and audience or language differences. Invented scenarios test a proposed model; they do not prove project facts.

Code is authoritative for current implementation within the inspected scope. It does not automatically override approved requirements, confirmed decisions, operations evidence, or intended behavior. Do not infer domain contexts from directories, services, namespaces, or the placement of a context file.

## Capture selectively

Keep terminology and boundary findings in the response or working analysis first. Persist only to an explicitly nominated authoritative destination with applicable write authority and valid memory policy. Preserve provenance and read back the result.

Prefer, in order:

1. an existing project-nominated canonical destination;
2. an existing configured glossary, typed decision, or open-question surface; or
3. a newly proposed location only when no suitable destination exists and the user approves it.

Never mandate `CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr`, or another Poppy silo. Retain useful aliases and translations instead of applying a blanket avoid rule.

Offer a technical ADR only when the decision is hard to reverse, surprising without context, and has a real tradeoff—and only when an ADR convention exists or is explicitly adopted. Operational, scope, or contractual decisions may belong in a different project decision record. Any record should retain status, source or authority, current-versus-intended distinction, rationale, material alternatives, consequences, and supersession where useful.

Only confirmed source-backed terminology, boundaries, or rationale may become durable learning. Proposals, review findings, and unresolved conflicts remain in the response or as explicitly authorized open questions.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed `domain-modeling` guidance pinned at revision `321658273cb1d20b76026717d027d505790106d4`:

- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/domain-modeling/SKILL.md

