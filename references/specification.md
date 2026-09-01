# Specification synthesis

## Turn settled intent into a contract

Start from the originating request and settled decision wording. Read only the current behavior, domain vocabulary, approved decisions, and authoritative sources needed to define the change. Keep separate:

- observed evidence;
- settled decisions;
- proposed choices;
- assumptions; and
- unverified or conflicted gaps.

Ask only questions that materially change scope, solution, acceptance, safety, or readiness. Never invent missing requirements. Preserve requested language, register, audience, and exact stakeholder wording where those are acceptance conditions.

Choose the smallest suitable form: scenarios, stories, use cases, invariants, technical requirements, or operational outcomes. Prefer observable behavior and the smallest sufficient test seams; do not impose one universal template.

Include only relevant elements:

- problem and intended outcome;
- source baseline and current-versus-intended boundary;
- scope and non-goals;
- behavior and observable acceptance;
- lifecycle, roles, permissions, and failure paths;
- implementation or testing decisions already settled;
- constraints, risks, and dependencies;
- compatibility, migration, rollout, and rollback;
- accessibility, security, privacy, performance, and observability; and
- open decisions with owners.

Classify readiness descriptively as draft, review-ready, implementation-ready, or blocked by named decisions. Do not score it. Readiness is not a tracker label, effect approval, or implementation authority.

Default to an inline draft. A named local file may be written within local edit authority. Repository-history publication, tracker publication, labels, state changes, messages, and deployment remain separate effects.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed to-spec guidance pinned at revision 321658273cb1d20b76026717d027d505790106d4:

- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/to-spec/SKILL.md
