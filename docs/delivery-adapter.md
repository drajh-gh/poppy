# Delivery adapter

## Identity

- Project: `poppy-ops-cockpit`
- Run: `poppy-ops-cockpit-20260817-01`
- Work item: `POC-001`
- Branch: `feature/poppy-ops-cockpit`
- Repository: `C:\Users\david\Documents\Codex\2026-08-17\ho\outputs\poppy-ops-cockpit`
- Frozen manifest: `C:\Users\david\Documents\Codex\2026-08-17\ho\work\poppy-ops-cockpit-delivery-manifest.json`
- Local preflight: `C:\Users\david\Documents\Codex\2026-08-17\ho\work\poppy-ops-cockpit-local-preflight.json`

## Repository contract

The repository itself is the tracker for POC-001. `main` is the base branch and the isolated feature branch has one writer. The deterministic gate is `python scripts/verify.py`. Evidence is frozen in `evidence/verification.json` and a candidate commit. No hosted CI, PR, deployment, or remote repository is in scope.

## Extension declarations

| Gate | Classification | Evidence |
| --- | --- | --- |
| `obsidian-runtime-smoke` | required | Dependency-free Node harness loads the exact packaged `main.js`, registers the view and command, activates the view, then fixture installation hashes are read back. Real-vault runtime proof remains pending until post-assurance installation. |
| `codex-stream-compatibility` | required | Passed under POC-DEC-002 using `C:\Users\david\.codex\.sandbox-bin\codex.exe app-server --stdio`: an initialized response and real ephemeral `thread/started` event were captured with read-only sandbox and `approvalPolicy: never`. Evidence: `evidence/codex-appserver-probe.json`. |

The manifest remediation ceiling is two and does not widen the plugin ceiling. Functional QA and Final Assurance are sequential, identity-distinct stages against one candidate. Installation is ordered after both reviews and does not change the candidate.

## Receipt schema

The closure packet records base/head revisions, changed files, commands, gate outcomes, artifact hashes, external effects, rollback, residual risks, and the exact decision receipt when a required gate is Gray.
