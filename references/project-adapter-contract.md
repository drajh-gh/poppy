# Project adapter contract

Poppy is project-agnostic. Repository-specific delivery behavior belongs in a project adapter that is stored with the project, not in this product repository.

An adapter must nominate:

- the project key and display name;
- canonical repository and evidence roots;
- tracker, base branch, worktree, test, review, and release rules;
- existing skills and control surfaces that Poppy must compose rather than replace;
- authority boundaries, approval requirements, and rollback procedures;
- extension gates required by the project delivery manifest; and
- coexistence rules for existing vault content and automations.

Paths and external identities must be supplied by local configuration or the project itself. Poppy must fail Gray when the nominated surface cannot be resolved. It must not search retired locations, infer credentials, or substitute a generic workflow for a project-defined delivery system.

See `examples/project-adapter.md` for a sanitized shape. The example is documentation, not an executable default.
