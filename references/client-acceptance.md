# Client and exact-candidate acceptance

## Keep acceptance states separate

Technical verification, product-owner acceptance, client acceptance, deployment, runtime read-back, and publication are separate claims. No earlier state implies a later one.

Bind evidence to the exact candidate, environment, scenario, observer, and decision authority. A relevant candidate change invalidates only acceptance states whose observed behavior could change. Leave unavailable states unverified.

For a business workflow change, map the exact candidate to confirmed behavioral scenarios and production-shaped state. Choose the closest faithful evidence:

- screenshots for important static visual states;
- a concise video for interaction, motion, roles, or sequences;
- bounded fixtures or dry-run manifests for imports, migrations, and data repair;
- API or integration responses for nonvisual system behavior; and
- authorized runtime observation where local evidence cannot establish the claim.

An incident report establishes reported behavior, not approval of a generalized policy.

## Visual product acceptance

Use visual evidence when user-visible experience is part of acceptance and the project or user asks for pre-release judgment. It complements deterministic checks; it does not prove accessibility, security, production behavior, or broader usability.

- Bind captures to the exact commit or working-tree snapshot.
- Map each capture to the original acceptance wording.
- Record the reproduction state, viewport or device where relevant, capture time, and material limitations.
- Present media in the current task when supported.
- Keep local artifacts disposable and outside Git unless separately authorized.
- Never fabricate evidence when faithful execution or capture is unavailable.

When pre-PR acceptance is an agreed gate, pause before pull-request preparation for the user's accept, reject, or requested-changes decision. The response can be ordinary language; it qualifies only the displayed candidate and does not authorize a commit, push, pull request, merge, publication, or deployment.

## Client-ready recording

A recording checkpoint applies only when a named client-facing behavioral change or project policy makes client review relevant. Do not add recording ceremony to ordinary internal or nonvisual work. Offer it only after direct local evidence covers every agreed client-visible acceptance item. If one item remains unverified, delivery is incomplete and the checkpoint stays premature. If a recording was not requested during implementation, offer it after complete local verification rather than preparing data or recording automatically.

At that handoff, call it the client-acceptance recording checkpoint and state both sides of the boundary: local behavior is verified, while client acceptance remains unverified until an authorized owner reviews faithful evidence. Offer the checkpoint as optional and state that recording begins only after the user requests it and approves the demo contract. The checkpoint does not itself imply acceptance.

Before recording, propose a compact demo contract for approval. Derive it from original stakeholder wording, accepted behavior, exact candidate, implementation, and tests. Include relevant scenarios, starting state, synthetic seed data, acting roles, visible steps and outcomes, permission or validation paths, lifecycle or error cases, and exclusions. Ask only when an ambiguity could change client expectations or material scope.

Choose an authorized local, development, or preview environment by fidelity. Any deployment is a separate effect. Use realistic synthetic, client-safe accounts and records. Never expose personal data, credentials, production exports, terminals, setup machinery, secrets, or irrelevant environment detail.

Produce one concise video when the story remains easy to follow, or several named clips when roles or scenarios need separation. Use a readable interface scale, deliberate movement, useful pauses, concise burned-in subtitles in the client's language, and no audio narration unless requested. Keep client media free of ticket numbers, commit hashes, test names, AI references, implementation detail, and ornamental introductions or conclusions.

Watch every rendered clip from beginning to end. Hand off:

- the media;
- private candidate and environment identity;
- scenario coverage and limitations;
- artifact location and disposition; and
- a short natural client-message draft.

Do not upload, publish, contact the client, or retain media in Git without separate authority.

## Interpret responses semantically

A named decision owner's ordinary affirmative response supports acceptance of the behavior faithfully shown. User acceptance qualifies client acceptance only when the user owns that product decision. Neither supplies Git, release, deployment, production-write, or publication authority.

Requested changes invalidate the affected scenarios. Return those scenarios through implementation, verification, and replacement evidence. A demonstrably irrelevant candidate change does not invalidate unrelated accepted scenarios.
