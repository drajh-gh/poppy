# Promotion registry

## Generic owned-process supervisor

- Classification: plugin candidate
- Status: not activated
- Evidence: ordinary shell timeout can leave owned descendant processes running even when the local-execution policy requires an owned-process ledger and zero survivors.
- Proposed contract: run a command under an owned process-tree supervisor, propagate output and exit status, terminate owned children and grandchildren on timeout, preserve unrelated processes, detect survivors, and provide a bounded rollback path.
- Promotion blocker: no project-neutral executable implementation currently has deterministic Windows and POSIX fixtures proving pass, fail, timeout, child and grandchild cleanup, unrelated-process survival, output and exit propagation, survivor detection, and rollback.
- Next validation: build the mechanism in isolation and run the complete cross-platform fixture matrix. Do not activate or claim the policy is executable until every required fixture passes and an independent assessment accepts the exact candidate.
