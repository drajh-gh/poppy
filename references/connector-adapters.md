# Connector adapters

## Google Drive

Discover files by stable ID and folder. Record MIME type, revision ID, modified time, effective date, approval state, language, sensitivity, document class, and authority. Fetch only the bounded content needed. For Sheets, nominate exact tabs and ranges for baseline, forecast, and reporting. Never assume newest means approved.

Document classes: discovery, proposal, estimate, contract, change-order, requirements, design, meeting, budget, invoice, status-report, client-content, integration-documentation.

## Povio Dashboard

Call the Dashboard guide once per tool session. Prefer read-only project, project-user, timesheet-summary, absence, invoice, planning, and weekly-report operations. Project roster does not prove weekly allocation. Snapshot dated facts into Obsidian and derive forecasts separately. Treat create/update health, planning, timesheet, invoice, or team operations as external writes requiring policy approval.

## Tracker

Boards or Linear owns work status, owner, priority, acceptance criteria, and discussion. Reconcile Slack/email/meeting requests to existing tickets before proposing a new one. Read the latest ticket state before reporting a blocker or completion.

## GitHub and CI

GitHub owns implementation and review evidence. Link request -> ticket -> PR -> deployment. Report PR age, review wait, CI, base/head, and release state. A merge is not deployment; a successful deployment is not exhaustive behavioral verification.

## Slack and Gmail

Read the latest thread or email reply before calling an ask unresolved. Classify new requests, deduplicate, link to the tracker, and surface commitments. Conversation provides context but does not automatically approve scope. Draft external responses unless the approval profile allows the exact send.

## Calendar and meetings

Calendar owns scheduled events, not decisions made during them. Link meeting evidence bundles to event IDs. Creating or changing an event is an external write.

## Source refresh

Each adapter returns: stable source ID, canonical locator, normalized request fingerprint, logical request ID, physical attempt, bounded coverage, observed facts, changed facts, freshness, contradictions, evidence grade, prior and next checkpoint, retained partial failures, missing access, and proposed canonical updates. Matching fingerprints reuse the first logical result within a run. Retries remain physical attempts inside that request; failure or partial coverage retains the prior checkpoint.

Before retrieval, reject retired roots and resolve mutable targets through a stable provider ID. Prefer change feeds, conditional requests, or webhooks; where unavailable, declare bounded polling and the resulting Partial or Gray limitation. Validate material multi-source runs through [operational controls](operational-controls.md). An adapter must not mutate a different system as a side effect of reading.

