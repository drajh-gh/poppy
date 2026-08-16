# Repository assessment

Assess third-party repositories through published GitHub pages, APIs, documentation, and metadata only. The default and currently authorized mode is `inspect-only`: do not clone, download archives, install packages, import modules, run examples, execute scripts, or add dependencies.

## Evidence checklist

1. **Identity:** canonical repository URL, owner, repository name, purpose, and relation to the researched need.
2. **Maintainer reputation:** verifiable work history, organizational affiliation when relevant, prior maintained projects, published research or engineering evidence, and signs that the canonical owner controls the repository. Stars and followers are context only.
3. **Maintenance:** default-branch activity, releases/tags, issue and pull-request responsiveness, roadmap or deprecation state, supported platforms, and documentation freshness.
4. **Quality evidence:** visible tests, CI, typed or documented interfaces, examples, changelog, reproducible benchmarks, independent users or case studies, and clear failure behavior.
5. **Security and privacy:** `SECURITY.md`, dependency/supply-chain surface, permissions, network/data behavior described by maintainers, known advisories, credential handling, telemetry, and sandbox assumptions.
6. **License and adoption:** license file and compatibility, attribution or redistribution obligations, versioning, installation footprint, integration constraints, reversibility, migration path, lock-in, and maintenance burden.
7. **Fit:** exact current workflow repaired, project-specific constraints, global plugin applicability, evidence gaps, and the smallest safe experiment.

Use `Unknown` rather than guessing. A missing license, unclear ownership, abandoned maintenance, unverifiable benchmark, security ambiguity, or unexplained binary lowers confidence and may block recommendation.

## Evidence-backed repository rule

A repository is recommendation-eligible only when all are true:

- its owner or maintainer reputation has a concrete evidence basis;
- the relevant capability is visible in primary repository documentation or code pages;
- maintenance, license, quality, and security signals were checked and dated;
- the finding maps to an observed need or an explicitly gated addition;
- constraints, unknowns, and adoption cost are stated;
- no claim relies on popularity alone.

Forks, templates, and derivative repositories must identify their upstream and material differences. Prefer the canonical upstream unless the derivative has a documented, relevant advantage and a credible maintenance case.

## Assessment outcome

Return `strong-candidate`, `experiment-candidate`, `watch`, or `reject`, with direct evidence links. This is research disposition only; Upgrader still owns change classification and adoption governance.
