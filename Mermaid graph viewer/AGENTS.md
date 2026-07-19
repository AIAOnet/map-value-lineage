# AGENTS.md

## Purpose

This file defines how Codex or any AI coding assistant should work in this repository.

The goal is to make changes safely, understand the affected code before editing, avoid unnecessary rewrites, and keep all work traceable through Git and versioned Value Lineage and Change-Impact Graphs.

---

## General Rules

- Understand the request before changing code.
- Do not make large changes unless explicitly requested.
- Prefer the smallest safe change.
- Do not change unrelated files.
- Do not refactor unrelated code.
- Preserve existing behavior unless the task clearly requires changing it.
- Follow the current project structure, naming style, and coding conventions.
- When unsure, inspect the code first instead of guessing.
- Do not remove comments, tests, logs, or configuration unless there is a clear reason.
- Keep security, privacy, and maintainability in mind.
- For every behavior or data-value change, use `$map-value-lineage` before and after implementation as defined below.

---

## Value Lineage and Change-Impact Maps

All application maps must be stored under:

```text
entities_graphics/
```

Use one stable subdirectory per mapped entity:

```text
entities_graphics/<entity-slug>/
```

Each version consists of a JSON evidence map and a Mermaid graph with the same zero-padded version number:

```text
entities_graphics/<entity-slug>/<entity-slug>-<value-slug>-v001.json
entities_graphics/<entity-slug>/<entity-slug>-<value-slug>-v001.mmd
entities_graphics/<entity-slug>/<entity-slug>-<value-slug>-v002.json
entities_graphics/<entity-slug>/<entity-slug>-<value-slug>-v002.mmd
```

Do not overwrite an existing version. The highest numeric `vNNN` pair is the latest map. The version number in both filenames must match `mapVersion` inside the JSON.

Every generated JSON map must include:

```json
{
  "mapVersion": 2,
  "previousVersion": 1,
  "basedOnCommit": "full commit hash of the implemented code change",
  "previousMapCommit": "commit hash that added the previous map version",
  "generatedAt": "ISO-8601 timestamp"
}
```

For `v001`, use `previousVersion: null` and `previousMapCommit: null`.

The map must also include the entity/value definitions, origins, readers, writers, mutations, checks, branches, storage, APIs, events, derived values, direct effects, transitive effects, evidence, confidence, related Git history, coverage limitations, and answers required by `$map-value-lineage`.

### Before changing code

Before editing application code:

1. Run `git status` and preserve unrelated user changes.
2. Identify every entity attribute, variable, state, flag, configuration value, identifier, or derived value affected by the requested change.
3. Locate the highest matching version in `entities_graphics` by numeric `vNNN`, not by filesystem modification time.
4. Read both the latest JSON and Mermaid files.
5. Verify that the JSON `mapVersion` matches the filename and that `basedOnCommit` exists in the current Git history.
6. Use `$map-value-lineage` and current code to validate the existing map and trace the proposed change from origin to every direct and transitive consumer.
7. Use the map to determine affected methods, APIs, storage, events, UI, tests, contracts, migrations, compatibility risks, rollout, and rollback.
8. Record missing, stale, inferred, or unresolved relationships in the impact analysis.

If no matching map exists, generate and commit a `v001` baseline map of the current behavior before changing application code. Use the current `HEAD` as `basedOnCommit`. The later post-change map must then use `v002`.

Do not start implementation until the affected flow and likely impact are reasonably clear.

### After changing code

After implementation:

1. Run the relevant tests and inspect `git diff`.
2. Commit the application code and its tests first using a focused commit. Do not include the new map version in this commit.
3. Capture the full code commit hash with `git rev-parse HEAD`.
4. Run `$map-value-lineage` again against the committed code.
5. Create the next immutable JSON and Mermaid version by incrementing the latest version exactly once, for example `v002` to `v003`.
6. Set the JSON `basedOnCommit` to the full code commit hash from step 3.
7. Set `previousVersion` and `previousMapCommit` from the prior map version.
8. Include the code commit in `history.commits`, with the reason, affected paths, matched aliases, evidence, relationship, and confidence.
9. Validate that the JSON parses, its edges reference existing IDs, the Mermaid graph represents the same version, and the filenames match `mapVersion`.
10. Commit only the new map pair in a second focused commit:

```text
docs(entity-map): add <entity> <value> lineage vNNN
```

The required order is therefore:

```text
inspect latest map -> analyze impact -> change code -> test -> commit code -> capture commit hash -> generate next map version -> commit map
```

Never amend the code commit after recording its hash in a map. If application code changes again, create another code commit and another incremented map version.

---

## Before Making Changes

Before editing any file, perform impact analysis using the latest applicable map and current repository evidence.

Codex must identify:

- the requested behavior change
- the affected entities and values
- the latest map version inspected, or the need for a baseline map
- the entry point of the flow
- frontend files affected, if any
- backend files affected, if any
- API routes or controllers affected
- services, utilities, or helpers affected
- database models, schema, or migrations affected
- configuration files affected
- environment variables affected
- events, queues, jobs, caches, reports, and external consumers affected
- tests affected
- documentation affected
- direct and transitive side effects
- unresolved or inferred relationships

Before editing, provide a short analysis:

```text
Impact analysis:
- Requested change:
- Affected entities and values:
- Latest map version:
- Affected flow:
- Direct impact:
- Transitive impact:
- Files expected to change:
- Files inspected:
- Risks and unknowns:
- Compatibility or migration needs:
- Rollback approach:
```

Do not start editing until the affected area is reasonably clear.

---

## Code Path Tracing

For every change, trace the code path from input to output.

Examples:

- UI button -> frontend state -> API call -> backend route -> service -> database -> response
- user prompt -> preprocessing -> search service -> RAG service -> LLM call -> response
- config toggle -> stored setting -> runtime behavior -> fallback behavior

When changing a feature, check both:

- where the feature is triggered
- where the result is consumed

Trace values beyond the immediate call path, including validation, control-flow branches, transformations, storage, caches, serialization, events, external contracts, tests, and derived UI behavior.

---

## Change Scope

Only modify files that are required for the task.

Allowed changes:

- files directly related to the requested feature or bug
- tests for the changed behavior
- configuration required for the change
- documentation if behavior changes
- the next immutable map version under `entities_graphics`

Avoid:

- unrelated cleanup
- renaming files without need
- changing formatting across unrelated files
- rewriting working code
- changing public APIs without reason
- changing database schema without explaining why
- editing or deleting historical map versions

---

## Safety and Fallbacks

When adding new behavior:

- preserve the old behavior by default when possible
- use feature flags or configuration toggles for risky changes
- add fallback behavior if the new flow fails
- avoid breaking existing users or existing data
- validate inputs
- handle errors clearly
- log important failures without exposing sensitive data

For risky changes, explain how to disable or roll back the change.

---

## Testing Rules

When behavior changes, update or add tests.

Check for:

- enabled state
- disabled state
- success case
- failure case
- fallback behavior
- invalid input
- edge cases
- compatibility with stored values, API clients, event consumers, and exhaustive branches

Before finishing, run the relevant test command if available.

If tests cannot be run, explain why.

Examples:

```bash
npm test
npm run test
npm run lint
pytest
python -m pytest
```

Use the commands that match this repository.

---

## Git Rules

This repository uses Git. All changes must be easy to review and easy to revert.

Before changing code:

```bash
git status
```

Check what is already modified.

Do not overwrite existing user changes.

If there are existing changes that are not yours, mention them before editing.

After changes:

```bash
git diff
```

Review the exact changes before finalizing.

Use focused commits. One commit should represent one logical change. Application code and its post-change map must be separate commits because the map records the application commit hash.

Good commit message format:

```text
type(scope): short description
```

Common types:

```text
feat:      new feature
fix:       bug fix
refactor:  code cleanup without behavior change
config:    configuration change
docs:      documentation change
test:      tests added or updated
chore:     maintenance
```

Examples:

```text
feat(ontology): add light search toggle
fix(rag): preserve fallback when graph search fails
config(admin): add ontology service setting
test(search): cover disabled light search mode
docs(entity-map): add order status lineage v003
```

Before committing, verify:

- only intended files are staged
- no secrets are included
- no temporary files are included
- tests or lint were run when relevant
- historical map versions were not modified
- the new map version contains the full application commit hash

Use:

```bash
git status
git diff
git add <specific-files>
git commit -m "type(scope): short description"
```

Do not use:

```bash
git add .
```

unless all changed files were reviewed and are intended to be committed.

---

## Secrets and Sensitive Data

Never commit:

- API keys
- passwords
- private tokens
- database credentials
- private certificates
- `.env` files
- personal data
- production secrets

If a secret is found, stop and report it.

Use environment variables or secret managers instead.

---

## Documentation Rules

Update documentation when:

- setup steps change
- configuration changes
- environment variables are added
- API behavior changes
- a new service is added
- deployment behavior changes

Keep documentation short and practical.

Do not rewrite or delete an older `entities_graphics` version. A new application change must produce a new numbered version.

---

## Final Response Format

After completing changes, summarize clearly:

```text
Change summary:
- Files changed:
- What changed:
- Behavior preserved:
- Tests added or updated:
- Commands run:
- Application commit:
- Previous map version:
- New map version:
- Map commit:
- Possible side effects:
- Remaining lineage gaps:
- Rollback:
```

Also mention any files inspected but not changed if they were important to the decision.

---

## Important Principle

Do not only change the file that looks obvious.

First read the latest versioned map and verify it against current code.

Then understand what is affected.

Then change the smallest safe set of files.

Then commit the application change, generate the next map version containing that commit hash, commit the map, and report both commits.
