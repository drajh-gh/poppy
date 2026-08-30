# Human-guided procedures

Use this playbook when a project task combines human-only values or approvals with ordered local or provider actions. Do not copy a generic executable wizard when a checklist or small helper is safer.

## Select the artifact

Use the lowest-risk sufficient form:

1. guided checklist;
2. effect-free helper; or
3. effectful wizard.

Operations owns discovery of genuinely human-only steps and the target, stage, value, sensitivity, destination, and risk map. Delivery owns artifact selection, authoring, testing, recovery, cleanup, and handoff. Inspect available project and provider configuration before asking the user to restate facts.

An effectful artifact is a deferred effect bundle. Before authoring it, preview the intended targets and effects so the code cannot hide scope. Authoring authority does not authorize execution.

## Define every stage

For each stage record:

- exact provider, account, organization, repository, environment, and local destination as applicable;
- inputs, outputs, and sensitivity;
- effect and prerequisites;
- confirmation and authoritative verification;
- rollback, cleanup, and resume behavior; and
- repeat classification: safe-to-repeat, inspect-before-repeat, replacement, irreversible, or unverified.

Keep stages focused and resumable. On resume, reconcile prior local and remote effects before continuing. Prevent concurrent execution and unsafe noninteractive input. Fail closed when target, state, or verification is ambiguous.

## Protect secrets and systems

Do not print, log, publish, embed in unsafe command arguments, or retain secrets unnecessarily. Prefer approved secret stores. Before writing a local secret, validate the exact confined destination, Git tracking and ignore state, links or junctions, permissions, encoding, format, backup, and retention.

Do not infer a remote target from the current directory, Git remote, default provider context, or ambient account. Do not install tools automatically. Choose checklist, PowerShell, Bash, Python, or a project-native form based on the actual platform and project conventions.

Test only with temporary synthetic fixtures and stub provider commands unless real effects receive separate exact approval. After every mutation, read back the authoritative destination. A skipped or failed stage is not success. Stop on partial failure, inventory completed effects, and present recovery before retrying.

Retain a one-off helper only when authorized and useful. Otherwise follow the approved cleanup plan; never delete project artifacts automatically.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed `wizard` guidance pinned at revision `321658273cb1d20b76026717d027d505790106d4`. The upstream executable template was not copied:

- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/wizard/SKILL.md

