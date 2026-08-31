# External research

## Research for a decision

Start from the decision, not a topic dump. Name the material unknowns, freshness requirements, source standards, and stopping condition. Search only broadly enough to distinguish viable options and support the decisive claims.

Prefer the primary source that owns each claim: official documentation, source code, specifications, first-party APIs, regulatory text, or original research as appropriate. Use secondary evidence when it adds interpretation or primary evidence is unavailable, and state the limitation. For each material claim, track what the source supports, contradicts, conflicts with, or leaves unverified.

Synthesize:

- decision and current constraints;
- viable options;
- material tradeoffs and risks;
- recommendation and why it wins;
- inference separated from sourced fact; and
- affected unverified or conflicted claims.

Cite sources near the claims they support. Match the requested audience, language, format, and level of technical detail without smoothing away uncertainty.

Research authority is read-only. It never authorizes cloning, installing software, executing downloaded code, adding a dependency, contacting a party, publishing, or making another external change. Return findings in the response unless the user supplies an exact authoritative destination and separate write authority. Never invent a repository or memory destination.

## Current-signal research

Use this method when a decision depends on recent developments, public reaction, lived experience, adoption, recommendations, or momentum. It complements primary-source research; it does not replace it.

- State the exact start, end, and as-of date. Use a rolling 30-day window only when it fits the decision.
- Preserve the user's terminology. Resolve current names, official accounts, aliases, relevant communities, and source-specific vocabulary only where doing so materially improves recall or disambiguation.
- Build the smallest useful query plan: decision, subject, intent, source lanes, inclusion and exclusion terms, and stopping condition. Expand only for an observed coverage gap.
- Match sources to claims. Use owner or primary sources for facts they control; community and social sources for reported experience, recurring problems, language, sentiment, and attention; and transaction, market, or prediction data only for what it directly measures.
- Use engagement to rank what deserves inspection, not what deserves belief. Account for sampling, visibility, coordinated activity, and platform-specific bias.
- Cluster evidence by claim and remove duplicates, reposts, syndication, and sources dependent on the same original item before calling a pattern cross-source corroboration.
- Track every material source lane as completed with relevant results, completed with no relevant results, or incomplete. Qualify incomplete coverage with the observed reason.
- Infer source silence only from a completed lane with no relevant results. An incomplete lane leaves the affected claim unverified.
- Apply an explicit relevance floor. When recent evidence is thin, off-topic, or single-source, report insufficient recent signal rather than relaxing the window or presenting weak activity as a trend.

Lead with the implication for the named decision. State the window and coverage, separate observed activity from inference, identify short-lived claims with an as-of date, and cite evidence near every material claim. Source counts and engagement totals are supporting context, not confidence scores.

A specialized local research engine is optional. Research authority does not permit installing or executing one, reading browser cookies, writing credentials or persistent reports, or incurring provider cost. Preview and obtain exact authority for every required effect before composing such a tool into Poppy.

## Provenance

The decision framing and source-authority rules are retained in original wording from Poppy baseline revision f5939651c61c448f4c2cc46e64ddf66a7fe6f102, references/research-and-learning.md. Reader-focused synthesis is adapted in original Poppy wording from Cursor's MIT-licensed guidance pinned at revision 68836ddaf5697224520f1847d90cdb90ca8babaa:

- https://github.com/cursor/plugins/blob/68836ddaf5697224520f1847d90cdb90ca8babaa/pstack/skills/technical-writing/SKILL.md
- https://github.com/cursor/plugins/blob/68836ddaf5697224520f1847d90cdb90ca8babaa/pstack/skills/unslop/SKILL.md

The current-signal framing, source-lane planning, coverage-state discipline, and insufficient-signal outcome are adapted in original wording from Matt Van Horn's MIT-licensed `last30days` skill pinned at revision `a218edadbc3361672f5e5e2cd72a8212b0b3fbb8`:

- https://github.com/mvanhorn/last30days-skill/blob/a218edadbc3361672f5e5e2cd72a8212b0b3fbb8/skills/last30days/SKILL.md
- https://github.com/mvanhorn/last30days-skill/blob/a218edadbc3361672f5e5e2cd72a8212b0b3fbb8/CONFIGURATION.md
- https://github.com/mvanhorn/last30days-skill/blob/a218edadbc3361672f5e5e2cd72a8212b0b3fbb8/LICENSE
