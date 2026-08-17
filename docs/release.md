# Release policy

A Poppy candidate is eligible for handoff only when:

1. the complete product verifier passes;
2. the tree is clean and the candidate revision is frozen;
3. both preserved source revisions and the remote seed remain ancestors of the candidate;
4. the tracked-data boundary audit finds no client data, live configuration, credentials, runtime state, or generated installation;
5. fresh Functional QA passes against the exact candidate; and
6. fresh Final Assurance passes after QA against that same candidate.

Any candidate change invalidates both review verdicts. Publication, remote mutation, vault installation, reload, merge, deployment, and production changes are separate effects requiring exact authority.

Before publication, rollback is to retain the two immutable source repositories and discard the un-published canonical checkout only under separate cleanup authority. After publication, preserve history and use a new reviewed revert commit. Installed cockpit rollback restores the previously recorded package hashes; it never modifies canonical vault content.
