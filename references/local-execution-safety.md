# Local execution safety

Use this gate for every R1 or R2 repository mutation. The project adapter remains authoritative and may add stricter checks or nominate project-specific dependencies and prerequisites.

1. Assert that the nominated and observed repository roots are syntactically absolute and have the same safe lexical identity. Reject relative, drive-relative, parent-traversing, or cross-platform aliases without resolving the filesystem. On absence, invalidity, or mismatch, stop repository-dependent work and report the affected coverage as Gray with the observed state.
2. Allocate exactly one writer in a clean isolated worktree on a branch related to the approved change. Reject a dirty, shared, locked, non-isolated, or unrelated-branch mutation surface.
3. Declare the complete dependency and prerequisite check set nominated by the project adapter, then record exactly one categorized result for each declaration. Reject omissions, extras, duplicates, category changes, missing or failed checks, inconsistent state, and evidence of a partial mutation; record a repair path rather than assuming rollback.
4. Record every process started by the run in an owned-process ledger. After a timeout, stop only owned survivors, prove that none remain, and pass the nominated scoped integrity check before continuing.
5. After interruption, emit a complete resume packet containing branch and revision, changed files, last passed gate, the exact process IDs from the authoritative owned-process ledger, blocker, remaining external-write gates, and an exact resume instruction.

Validate the evidence packet with `scripts/validate_local_execution_preflight.py`. A passing packet proves only these generic gates; it does not replace adapter rules, repository rules, test evidence, or write approval.
