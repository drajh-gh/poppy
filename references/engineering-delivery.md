# Engineering delivery

## Enter with a selected candidate

Delivery begins when the intended outcome is sufficiently settled to create or change an exact candidate. Retain the originating acceptance wording, selected behavior, non-goals, constraints, authority, and relevant evidence.

Return a material decision to project work when any of these remains unsettled enough to change the outcome:

- user-visible behavior or success;
- scope or non-goals;
- lifecycle, state ownership, or integration boundary;
- compatibility, migration, or recovery expectation; or
- who may accept the result.

Resolve minor reversible implementation details in place. Do not reopen settled product decisions merely to optimize the implementation.

## Inspect before editing

Read applicable repository instructions and inspect the exact target and working state. Preserve modified and untracked user work. If the intended edit overlaps user changes and cannot be safely separated, stop for direction.

Use the smallest relevant source, history, runtime, test, and domain evidence. Avoid broad discovery when a bounded read can answer the implementation question. Name assumptions that affect behavior and leave unsupported ones unverified.

Choose the smallest coherent change that satisfies the acceptance anchor. Preserve project vocabulary and conventions. Prefer deletion or simplification when it removes accidental complexity without changing required behavior. Treat architecture heuristics as judgment aids, not laws.

## Implement through observable seams

For a defect, reproduce or characterize the decisive failure before correcting it when feasible. For new behavior, identify the closest observable seam and establish useful feedback early. Tests should protect behavior and material failure modes, not merely mirror implementation structure.

Keep one writer per target. A delegated writer uses an isolated worktree and explicit file boundary. Do not let implementation or remediation broaden the authorized target.

Generated helpers, repository instrumentation, dependencies, commits, installations, deployments, and external writes retain their own authority boundaries. Preparing one does not authorize executing it.

## Verify proportionately

Verify every observable acceptance item for the changed behavior, then the smallest relevant static, integration, build, visual, or repository gate. A passing subcheck does not establish an unchecked sibling behavior. Run broader checks sequentially when blast radius or project policy requires them. Respect local resource limits and report unavailable gates instead of disguising them as passing.

For a meaningful safety or blast-radius claim, identify the one or two facts on which safety depends and verify them against the closest faithful allowed artifact or runtime path. This supplements, rather than replaces, acceptance-by-acceptance verification.

Use independent read-only assurance when consequence, uncertainty, breadth, or release readiness warrants a fresh perspective. Any relevant candidate change invalidates the earlier verdict.

## Hand off the exact result

Report:

- exact candidate identity and files or artifacts changed;
- behavior implemented and preserved;
- checks run and observed results;
- limitations and affected unverified or conflicted claims;
- disposable artifacts and their disposition; and
- the next acceptance or effect, if one genuinely remains.

Technical verification does not imply product acceptance, client acceptance, commit, publication, installation, deployment, or production correctness. Keep each state separate and ask only for the next decision the user owns.
