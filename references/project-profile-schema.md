# Project profile schema

Store the validated profile as `project-ops.json` at the vault root. The onboarding wizard may leave unresolved values as `null` only when it records them under `onboarding.accepted_gaps`.

## Required shape

```json
{
  "schema_version": 1,
  "project": {
    "key": "project-key",
    "name": "Project name",
    "client": "Client name",
    "stage": "active-delivery",
    "archetypes": {
      "primary": "fixed-scope-delivery",
      "overlays": []
    },
    "objectives": [],
    "next_milestone": null,
    "timezone": "Europe/Ljubljana",
    "sensitivity": "confidential"
  },
  "vault": {
    "strategy": "per-project",
    "path": null,
    "adoption_mode": "new",
    "project_root": "wiki/project-key",
    "human_owned": ["inbox.md", "daily/"],
    "portfolio_publish": "sanitized-summary",
    "raw_retention": "sanitized-receipts",
    "canonical_language": "en"
  },
  "language": {
    "client_language": "en",
    "source_languages": ["en"],
    "transcript_quality": "reliable",
    "meeting_evidence_mode": "transcript-plus-confirmation",
    "preserve_material_originals": true,
    "client_style": "professional"
  },
  "sources": {
    "drive": {"folder_ids": [], "classes": {}},
    "povio_dashboard": {"project_id": null, "access": "read-only", "capabilities": []},
    "tracker": {"system": null, "project_ids": [], "canonical_for": ["work-status", "owner", "priority"]},
    "github": {"repositories": [], "default_branches": {}},
    "slack": {"client_channels": [], "internal_channels": [], "support_channels": []},
    "gmail": {"client_domains": [], "contacts": []},
    "calendar": {"calendar_ids": [], "recurring_meetings": []}
  },
  "authority": {
    "contracted_scope": null,
    "approved_estimate": null,
    "budget_baseline": null,
    "actual_hours": null,
    "planned_allocation": null,
    "invoice_state": null,
    "work_status": null,
    "implementation": null,
    "deployment": null,
    "requirements": null,
    "milestone_dates": null,
    "client_commitments": null,
    "conflicts": "preserve-and-escalate"
  },
  "stakeholders": {"records": [], "approvers": {"scope": [], "budget": [], "milestone": [], "release": [], "client_communication": []}},
  "approvals": {
    "preset": "conservative",
    "obsidian_internal_write": "allow-with-audit",
    "external_drafts": "allow",
    "tracker_write": "confirm",
    "email_send": "confirm",
    "slack_send": "confirm",
    "calendar_write": "confirm",
    "baseline_change": "named-approver",
    "finance_write": "deny",
    "merge_or_deploy": "deny"
  },
  "cadence": {
    "daily_brief": {"enabled": true, "time": "08:30", "changed_only": true},
    "weekly_review": {"enabled": true, "day": "friday", "time": "14:00"},
    "monthly_portfolio": {"enabled": true},
    "workflow_improvement": {"enabled": false, "frequency": "weekly", "time": "17:30", "changed_only": true, "max_specialists": 2},
    "workflow_research": {"enabled": false, "frequency": "weekly", "time": "16:30", "changed_only": true, "max_specialists": 2, "repository_access": "inspect-only", "themes": []},
    "meeting_followup": "event-driven",
    "quiet_hours": ["18:00", "08:00"]
  },
  "controls": {
    "retrieval": {
      "mode": "ledger",
      "fingerprint_components": ["provider", "stable-source-id", "normalized-request"],
      "retry_scope": "physical-attempt",
      "checkpoint_policy": "success-only",
      "failure_policy": "retain"
    },
    "source_identity": {
      "canonical": "stable-id-or-verified-root",
      "mutable_target_policy": "discover-and-review",
      "retired_locator_policy": "reject"
    },
    "human_authority": {
      "require_source": true,
      "require_review_after": true,
      "silence_is_approval": false
    },
    "reporting": {
      "executive_body_word_cap": 350,
      "outcome_first": true,
      "evidence_appendix": true
    },
    "release_evidence": {
      "required_links": ["source", "artifact", "build", "delivery", "runtime"],
      "missing_link_state": "gray"
    }
  },
  "tolerances": {
    "schedule_yellow_days": 3,
    "schedule_red_days": 7,
    "budget_yellow_percent": 10,
    "budget_red_percent": 20,
    "critical_blocker_yellow_business_days": 2,
    "client_response_yellow_business_days": 2,
    "pr_review_yellow_hours": 48,
    "volatile_source_max_age_days": 7,
    "missing_required_baseline": "gray"
  },
  "onboarding": {"status": "draft", "last_completed_step": null, "accepted_gaps": [], "discovered_at": null, "completed_at": null}
}
```

## Enumerations

- `project.stage`: `discovery`, `active-delivery`, `stabilization`, `maintenance`, `paused`, `closed`
- primary archetype: `support-maintenance`, `product-launch`, `discovery-validation`, `fixed-scope-delivery`, `retainer-capacity`, `internal-initiative`
- `language.transcript_quality`: `reliable`, `partial`, `unreliable`, `unavailable`
- `vault.adoption_mode`: `new`, `existing`, `clone`, `reconfigure`
- sensitivity: `internal`, `confidential`, `restricted`
- `cadence.workflow_improvement.frequency`: `weekdays` or `weekly`
- `cadence.workflow_research.frequency`: `weekly` or `monthly`; repository access must be `inspect-only`

## Validation invariants

- Project key uses lowercase letters, numbers, and hyphens.
- A project has exactly one primary archetype.
- Every material authority is mapped or explicitly accepted as a gap.
- `tracker` and `github` references never authorize external writes.
- A budget health result is Gray when no approved baseline exists.
- Existing vault adoption never overwrites `AGENTS.md`, `raw/`, `inbox.md`, `daily/`, canonical pages, or `log.md`.
- Research cadence is optional and disabled by default; scheduling never authorizes repository download/execution or project/plugin mutation.
- `controls` is optional for backward-compatible schema-v1 profiles. When present, it enables the validated retrieval, source-identity, expiring-authority, executive-report, and release-evidence defaults without storing dynamic checkpoints or provider credentials in the profile.
- Dynamic checkpoints, request fingerprints, failures, authority receipts, and release observations belong in dated run evidence validated by `validate_operational_control_packet.py`.
