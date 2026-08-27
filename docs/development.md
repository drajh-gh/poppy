# Development

Poppy v3 is a documentation-and-skills product. Python is needed only for deterministic verification.

1. Work from an exact base in an isolated branch or worktree.
2. Keep one writer per target and preserve pre-existing changes.
3. Keep product content project-agnostic and machine-path-free.
4. Validate every skill changed in the candidate.
5. Run `python scripts/verify_product.py`.
6. Run impact-based scenario checks for a leaf-only change; rerun the complete suite for root, authority, context/profile, delegation, or assurance changes.

The scenario catalog is acceptance material, not a runtime contract or execution ledger. Evidence captured while dogfooding belongs outside the repository.
