# Development

Poppy v3 is a documentation-and-skills product. Python is needed only for deterministic verification.

1. Work from an exact base in an isolated branch or worktree.
2. Keep one writer per target and preserve pre-existing changes.
3. Keep product content project-agnostic and machine-path-free.
4. Validate every skill changed in the candidate.
5. Validate JSON syntax and exact scenario/fixture parity, then run `python scripts/materialize_scenario.py --verify-catalog`.
6. Run `python scripts/verify_product.py` sequentially.
7. Run impact-based scenario checks for a leaf-only change; rerun the complete suite for root, authority, context/profile, delegation, assurance, inventory, or scenario-contract changes.

The scenario catalog is acceptance material, not a runtime contract or execution ledger. Evidence captured while dogfooding belongs outside the repository.

Keep required scenario identifiers centralized in the verifier and derive counts from those sets. Add behavior-focused assertions instead of scattering fixed totals or matching incidental prose. Source adaptations must use original Poppy wording and retain concise upstream provenance.
