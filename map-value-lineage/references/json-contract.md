# JSON output contract

Use the example asset as the baseline. The result must contain:

- `format`, `version`, `repository`, and `target`
- `relationshipTypes`
- `entities`, `values`, `nodes`, and `edges`
- `mutationRules`
- `history.commits` and `history.coverage`
- `changeScenarios`
- `questionsAnswered` containing all required questions
- `coverage`, `gaps`, and `recommendedVerification`

Every node must have a stable `id`, `kind`, `name`, and location when available. Every edge must contain `from`, `type`, `to`, `evidence`, `evidenceRefs`, and `confidence`.

Each history commit must use this shape:

```json
{
  "hash": "full commit hash",
  "author": {"name": "", "email": ""},
  "authoredAt": "ISO-8601",
  "committedAt": "ISO-8601",
  "subject": "",
  "affectedPaths": [],
  "matchedAliases": [],
  "relationship": "introduced|modified|validated|persisted|exposed|consumed|migrated|tested|removed|renamed|other",
  "reason": "Why this commit is related to the target value",
  "evidence": [{"type": "diff|path|message|rename", "detail": ""}],
  "confidence": 0.0
}
```

`history.coverage` must record examined refs, whether the clone is shallow, followed paths, search aliases, earliest examined commit, limitations, and excluded candidate count.

For proposed changes, identify direct and transitive nodes, compatibility risks, data migration, required verification, rollout, and rollback.
