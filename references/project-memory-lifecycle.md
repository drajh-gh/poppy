# Project memory lifecycle

Use Project Operations memory as a bounded lifecycle for substantive project work, not as a reason to load the whole vault.

## Substantive work

A task is substantive when it investigates or changes product behavior, project state, delivery evidence, architecture, scope, decisions, commitments, incidents, operations, or a reusable workflow. Pure formatting, trivial lookups, and no-change checks do not require memory writes.

## Orient

1. Resolve the project and vault from the repository adapter or `project-ops.json`.
2. Read `current.md` and the project index. Keep the repository adapter under 150 words and `current.md` under 750 words.
3. After `current.md` and the index, follow task routing to at most three additional canonical pages or about 2,500 total routed-page words before justifying a wider read.
4. Read the profile or source map only when authority, freshness, sensitivity, or external effects matter.
5. Follow raw receipts or live authorities only for current, disputed, exact, or high-impact claims.

Researcher may widen beyond the default routed-page budget when the authorized research scope requires full task-history or vault coverage. Record the reason and coverage; do not bulk-copy the corpus into outputs.

## Work

- Treat the tracker as the task system and Obsidian as compiled memory.
- Reuse the working set within the task. Do not repeat broad retrieval.
- Separate verified fact, interpretation, decision, hypothesis, contradiction, and open question.
- Advance `valid_as_of` only after rereading the nominated authority.

## Close

Explicit read-only, review-only, or diagnosis-only scope suppresses all vault writes, including receipts and log entries. Return proposed memory updates instead. The lifecycle never expands the task's write authority.

1. Decide whether source-backed durable understanding changed.
2. If it changed, update an existing canonical page before creating a distinct record. Promote confirmed decisions, commitments, risks, milestones, incidents, contradictions, and reusable findings from task or meeting evidence.
   Store substantive research briefs, repository assessments, and Upgrader handoffs under `wiki/<project>/pm/records/research/`; use `raw/<project>/research/` only for immutable minimized source receipts that lack a stable reference.
3. Update `current.md` only when present orientation changed. Keep dated history in snapshots or canonical history pages.
4. Preserve stable ticket, PR, commit, CI, deployment, and verification references. Create an immutable receipt when mutable evidence lacks a stable durable reference or is needed to support a compiled claim.
5. Append one concise audit entry and lint only the changed surface.
6. If nothing durable changed, write nothing.

## Cadence

- Event-driven: close of material meetings, delivery, incidents, decisions, and source changes.
- Weekdays: changed-only operational refresh.
- Weekly: semantic lint and freshness review.
- Monthly: authority, source coverage, retention, and governance review.

Scheduled execution never expands write authority. Update an existing automation for the same project and control purpose rather than creating a competing job.
