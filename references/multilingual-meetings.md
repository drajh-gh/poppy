# Multilingual and low-transcript meetings

The workflow must work without a transcript. Configure `working_language`, `client_language`, `source_languages`, `transcript_quality`, `meeting_evidence_mode`, and communication style per project.

## Evidence modes

- Reliable transcript: ingest a sanitized receipt, reconcile against notes, and extract candidate decisions/actions.
- Partial or unreliable transcript: treat as Grade C; it cannot change baselines.
- No transcript: use a localized pre-brief, structured notes, a short post-meeting debrief, and written confirmation.
- Multilingual: preserve material original wording beside normalized internal meaning and maintain a domain glossary.

## Slovenian default

```yaml
working_language: en
client_language: sl-SI
meeting_evidence_mode: structured-notes-plus-confirmation
client_style: formal-vikanje
```

Prepare agendas and client drafts in Slovenian. Capture high-value markers: `ODLOČITEV`, `NALOGA`, `LASTNIK`, `ROK`, `SPREMEMBA OBSEGA`, `TVEGANJE`, `ODPRTO VPRAŠANJE`, and `POTRDITEV STRANKE`.

After the meeting, a clean five-minute single-speaker debrief is preferable to inventing certainty from poor multi-speaker audio. Normalize the debrief into candidate decisions, commitments, dates, dependencies, risks, and scope changes. Verify amounts, dates, names, mandatory language, scope, budget, and milestone changes through Grade A/B evidence.

For a material source phrase, retain:

```markdown
**Original:** ...
**Normalized internal meaning:** ...
**Interpretation note:** ...
**Source:** [[raw/...]]
```

## Confirmation

Prepare a written recap for high-impact agreements. Until confirmation arrives, keep the item provisional. Never send the recap without the configured approval.

