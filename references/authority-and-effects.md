# Authority and effects

## Default authority

An ordinary implementation request authorizes scoped, reversible working-tree edits and targeted verification when project identity and authority are valid. It does not silently authorize:

- commits, pushes, pull requests, merges, or remote tag changes;
- tracker, calendar, email, chat, or other external writes;
- dependency adoption, third-party code execution, or installation;
- deployment, production, financial, or destructive actions;
- publication or personal plugin installation; or
- durable project-memory writes.

Profiles, roles, confidence, conventions, and earlier broad consent may narrow action but never widen it.

When a profile appears to permit an effect but the current request does not, state that current approval is missing or unverified. Any later approval must bind the exact target, effect, and preview; profile permission is never a substitute.

Requested read-only investigation and plan preparation proceed without a separate approval ceremony. Complete safe preparation that does not itself cause the gated effect before asking the user to approve that effect.

## Consequential-effect gate

Before an external or difficult-to-recover effect:

1. name the exact target and effect;
2. show a concrete preview;
3. explain material risk and the rollback path;
4. obtain approval for that target and effect;
5. execute without broadening the target;
6. read back the authoritative destination; and
7. report the observed result.

Changed target, content, or effect invalidates approval. Silence is not approval.

Approval is semantic, not an incantation. A direct affirmative answer to an exact current preview is valid; do not require the user to repeat targets, hashes, or prescribed wording unless an external system inherently requires it. Multiple named effects may be approved as one explicit bundle, while each still receives its own execution boundary and read-back. Reacquire approval only when the target, content, effect, material risk, or rollback changes.

## Poppy source-first release gate

For a Poppy self-update, preserve one-way promotion: candidate → verified committed revision → merged canonical branch → synchronized clean local checkout → personal installation → fresh-task activation proof. A hotfix shortens waiting and scope; it does not change the order.

Pin the candidate branch and working state, canonical remote and branch, intended commit, version, digest algorithm and digest, installation target, currently active rollback package, and fresh-task read-back before requesting the applicable effects. Commit, push, pull request, merge, local fast-forward, installation, and fresh-task creation remain distinct effects even when approved as one exact bundle. Read back each authoritative destination and stop on the first mismatch or partial failure.

Never install a dirty or unmerged working-tree candidate as the intended release, publish by copying an installed cache backward into Git, or infer that a pre-existing task adopted an upgrade. An installed package is release-artifact evidence, not source authority. If source and installation diverge, first pin both identities and the canonical remote. Prefer the canonical source when it contains the installed artifact exactly; copying an installed package back to source is exceptional recovery only when authoritative source is genuinely missing and provenance establishes the exact artifact.

### Explicit current-task lifecycle marker

Poppy Housekeeping may use its self-contained single current-task fast path without loading this reference when the user directly requests one lifecycle-marker rename of the calling Codex task and every entrypoint eligibility condition is already supported. The direct command is semantic approval for that exact reversible rename only; it is not evidence that the substantive lifecycle disposition is true. A bounded prompt hook supplies the current Codex `session_id` as the exact task ID for this exception; absent that developer-context identity, the fast path stops without discovery or mutation.

An unqualified request to mark the calling task done authorizes only the completed title marker. It never authorizes archive or archive language; archive requires an explicit request and remains outside this exception.

One concise informational preview may say that the guarded call will resolve and retain the exact prior title as rollback. Do not list tasks or make a preliminary native task call solely to populate that preview. Follow it immediately with exactly one `functions.exec` call that reads the supplied exact task ID, validates title/activity, applies at most one title mutation to that ID, and reads the same ID back. Do not request duplicate approval when the target, lifecycle-title state, title-only effect, risk, and prior-title rollback remain unchanged. An already-correct lifecycle title, including an already-unmarked active title, is an idempotent read-back result rather than a reason to rewrite it.

This exception does not cover a named other task, a batch, archive state, pinning, moving, sidebar organization, worktrees, trackers, automation, standing policies, ambiguous intent, missing or conflicting disposition evidence, unresolved target/title/activity drift, malformed or stacked markers, or any consequential or less-reversible effect. Those cases use the full gate. If authoritative read-back after the rename contradicts the intended result or reveals newer activity, report the observed effect as unverified or conflicted and stop; do not hide the contradiction or automatically broaden approval into a rollback.

For an effectful helper or production repair, validate the approval contract first: exact target selection, schema and type assumptions, imports and runtime compatibility, prepare-only compilation or dry run, preservation guards, rollback behavior, and expected read-back. Human approval is the final gate to a prepared effect, not part of iterative harness debugging.

## User work and destructive actions

Inspect the relevant working tree before editing. Preserve modified and untracked files. If intended edits overlap user changes, stop and ask for direction. Never clean, reset, replace, or delete unrelated work.

Resolve exact absolute targets before a destructive action. Prefer recoverable operations. Never use broad roots, unresolved variables, or cross-shell path construction for recursive deletion or moves.

## Honest outcomes

Report only observed effects. A command exit is not enough when the destination can be read back. If verification is missing, the effect is unverified; if authoritative evidence contradicts the claimed result, it failed.

## Deferred effects and partial failure

Treat tracker publication, Git history changes, provider mutations, and effectful generated procedures as distinct effects. They may share one explicit approval bundle, but preview exact targets, content, ordering, idempotency or repeat behavior, verification, recovery, and rollback before approval. Approval to author an effectful helper does not authorize running it.

After every external mutation, read back the authoritative destination. Stop immediately on partial failure, inventory observed effects, and reconcile before retrying. Never silently continue, duplicate an effect, or report aggregate success.

Staging and Git operation completion are separate from resolving working-tree content. Never use broad staging such as `git add .`, `git add -A`, or `git commit -a`; stage only reviewed exact paths with applicable authority. Continuing, committing, aborting, skipping, quitting, changing branches, and publishing each retain separate authority.

Production instrumentation is never authorized by a diagnosis playbook. Repository instrumentation, local harnesses, regression tests, and artifact deletion are writes and require the task's applicable authority. Inventory temporary artifacts and follow a declared disposition rather than deleting them automatically.

Keep secrets out of prompts, logs, command arguments, public artifacts, and unnecessary retention. Before a local secret write, validate the exact confined path, Git tracking and ignore state, links or junctions, permissions, encoding, format, backup, and retention requirements.
