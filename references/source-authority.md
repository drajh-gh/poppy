# Source authority and evidence

## Default authority matrix

| Claim | Default authority |
| --- | --- |
| Contracted scope and commercial terms | Executed contract, SOW, or change order on Drive |
| Approved estimate | Explicitly approved estimate file or Sheet |
| Budget baseline | Nominated budget Sheet and approved revision |
| Actual hours and team | Povio Dashboard timesheets and project membership |
| Planned allocation | Explicit weekly allocation plan; roster membership alone is insufficient |
| Invoice state | Nominated finance record or Povio Dashboard |
| Work status and ownership | Boards, Linear, or nominated tracker |
| Implementation | GitHub repository and pull requests |
| Deployment and runtime | CI/deployment record and current runtime evidence |
| Requirements and decisions | Approved specification, decision, or written confirmation |
| Client intent | Confirmed client communication; discovery evidence remains context until approved |
| Current forecast and health | Derived assessment citing the above sources |

Never assume the newest Drive file is executed or approved. Preserve conflicting claims, identify which source is newer and authoritative for the claim, and escalate material contradictions.

## Evidence grades

- **A — confirmed:** executed document, approved decision, explicit written client confirmation, or verified authoritative system state.
- **B — reliable:** contemporaneous notes by a named participant or manually reviewed transcript.
- **C — provisional:** unreviewed transcript, partial notes, or second-hand recap.
- **D — inferred:** model interpretation or implication from several sources.

Grade C or D may create a candidate or open question. Scope, budget, milestone, and contractual baselines require Grade A. Material dates, amounts, owners, and commitments require Grade A or B.

## Receipt rules

Every raw receipt records source system, stable identifier, bounded coverage, capture time, language, sensitivity, evidence grade, known gaps, and exclusions. Prefer a sanitized digest to transcript or channel mirroring. Never store credentials, access instructions, raw production rows, unnecessary personal data, or case-specific financial detail when a minimized statement is sufficient.

## Freshness

- Volatile project state: normally 7–14 days or the configured project tolerance.
- Stable domains, roles, workflows, and accepted decisions: 30–90 days.
- A stale required source makes the affected health dimension Gray until refreshed.
- Advancing `valid_as_of` requires rereading the authoritative source.

