# Decision discovery

Use decision discovery when material preferences, intent, sequencing, or uncertainty must be clarified before recommendation, capture, or delivery. Poppy remains the sole conversational control surface.

## Choose the smallest mode

- **Interview-only:** work in conversation and return a compact session delta. No write.
- **Interview-plus-proposal:** show exact proposed changes to nominated glossaries, decisions, open questions, or other artifacts. No write.
- **Interview-plus-authorized-capture:** preview exact destinations at stable checkpoints, obtain approval for those writes, write only those destinations, and read them back.

Selecting a mode does not grant authority. Interview authority is not documentation, tracker, memory, implementation, or external-effect authority.

## Build the decision tree

Start from the destination and the condition for a useful handoff. Map only the uncertainty needed to reach it:

- settled decisions and rationale;
- actionable questions whose prerequisites are satisfied;
- blocked questions with explicit dependencies;
- uncertainty not yet formulable;
- out-of-scope boundaries; and
- evidence that remains unverified or conflicted.

Ask one dependency layer per round. Ask at most three independent questions, defaulting to one for consequential or terminology-heavy decisions. Recommend an option with each question when evidence supports one. Inspect available environmental facts instead of asking the user to restate them.

For a large foggy effort, use an ephemeral map in the current task. Each decision unit records its question, importance, evidence needed, method, responsible owner, blockers, completion signal, and effect gates. Owner means responsibility, not assignment, permission, or authority.

Methods are optional and proportional: research for external evidence, a prototype for artifact-based learning, domain modeling for unclear concepts, Operations for decisions and coordination, Delivery for implementation evidence, and Assurance for an independent check. None implies a subagent or external effect.

## Preserve checkpoints

A session delta records:

- exact project or topic and selected mode;
- settled decisions and rationale;
- canonical, source, deprecated, translated, and audience-specific terms;
- concrete scenarios and boundary conclusions;
- contradictions and unverified claims;
- open decisions with dependency links;
- candidate capture destinations and required authority;
- a monotonic checkpoint identifier; and
- the last user-confirmed checkpoint.

Confirmed checkpoints remain stable until explicitly reopened. Recompute only affected downstream branches. Confirmation records the user's decision; it does not make a factual claim true or expand authority.

## Stop and hand off

Stop when the route is responsibly clear enough for a recommendation, specification, ticket preview, or Delivery handoff—not when every possible uncertainty disappears. Discovery must not route directly into implementation merely because the interview ended. Apply the phase-boundary decision and carry original evidence and wording forward.

A durable map is exceptional. Use only a project-authoritative tracker or explicitly nominated document, preview the exact effect, obtain approval, and read it back. Never create a local shadow tracker, private graph, automatic assignment, credential record, or durable-memory mirror.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed `grilling`, `grill-with-docs`, and `wayfinder` guidance reviewed on 2026-08-27:

- https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling
- https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs
- https://github.com/mattpocock/skills/tree/main/skills/engineering/wayfinder

