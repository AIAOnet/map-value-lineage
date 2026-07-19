---
name: map-value-lineage
description: Map an entity attribute, variable, configuration value, state, flag, identifier, or derived value across an application and assess change impact. Use when Codex must find where a value originates, is read, checked, mutated, transformed, stored, accepted or exposed by APIs, carried by events, consumed downstream, shown in UI, or changed through Git history; produce a Value Lineage and Change-Impact Graph JSON file and a Mermaid graph.
---

# Map Value Lineage

Build an evidence-backed, value-centered graph. Do not substitute a service-level DFD or a list of text-search matches.

## Inputs

Identify the target value, entity, repository root, and proposed change from the request or repository. If the target is ambiguous, ask only for the missing identifier or entity. Continue without a proposed change by mapping the current value.

Read [references/questions.md](references/questions.md) before analysis. Ask and answer every listed graph question. Resolve answers from code and repository evidence before asking the user.

Read [references/json-contract.md](references/json-contract.md) before writing output. Use [assets/value-lineage-impact-map.example.json](assets/value-lineage-impact-map.example.json) as the structural example.

## Workflow

1. Establish repository state.
   - Record repository name, current revision, target value, entity, aliases, and analysis timestamp.
   - Preserve user changes. Perform read-only inspection unless the user requests code changes.

2. Find the semantic definition.
   - Locate declarations, types, defaults, enum members, schemas, database mappings, generated contracts, and documentation.
   - Record exact repository-relative paths, symbols, and line numbers when available.
   - Separate the conceptual value from its aliases in code, storage, APIs, and events.

3. Trace backward to origins.
   - Find constructors, defaults, request inputs, deserializers, database loads, configuration, event consumers, imports, and external sources.

4. Trace mutations and checks.
   - Find all assignments, setters, commands, update queries, migrations, validators, guards, comparisons, switches, match expressions, feature gates, and authorization or business decisions.
   - Distinguish readers from writers. Identify bypasses around canonical mutation methods.

5. Trace forward to effects.
   - Find derived values, branches, returned API fields, UI behavior, persistence, caches, indexes, logs, metrics, messages, event consumers, reports, tests, and external contracts.
   - Continue transitively until a boundary, terminal side effect, or unresolved dynamic dependency is reached.

6. Inspect Git history.
   - Run `scripts/collect-entity-commits.ps1` with the repository, entity/value search pattern, and every confirmed defining path.
   - Inspect each candidate diff. Include a commit only when the diff, affected path, or commit message provides evidence of relevance.
   - Store commit hash, author, authored and committed dates, subject, affected paths, matched aliases, relationship to the value, evidence, and confidence in `history.commits`.
   - Include relevant rename history with `--follow` for confirmed paths.
   - Never claim history is exhaustive when it may live in deleted files, squashed commits, unavailable branches, shallow history, submodules, generated artifacts, or external repositories. Record these gaps in `history.coverage`.

7. Model a proposed change.
   - Classify it as add/remove/rename/retype/reinterpret/default-change/constraint-change/storage-change/behavior-change.
   - Separate direct effects from transitive effects.
   - Include migration, backward compatibility, exhaustive branching, serialization, events, consumers, tests, rollout, and rollback questions.

8. Generate two required artifacts in the user-approved output directory:
   - `<entity>-<value>-lineage.json`
   - `<entity>-<value>-lineage.mmd`
   - Render the Mermaid graph inline as well when the client supports Mermaid.

9. Validate.
   - Parse the JSON.
   - Confirm every edge references existing node/value IDs.
   - Confirm every assertion has `declared`, `static`, `runtime`, `contract`, `history`, or `inferred` evidence.
   - Mark inference explicitly; do not present inference as confirmed behavior.
   - Confirm every question in `questionsAnswered` has an answer, evidence, or a documented gap.

## Evidence rules

- Prefer semantic references and call/data-flow analysis over raw text matches.
- Use static analysis for potential paths, runtime traces for observed paths, contracts for public interfaces, and Git history for past intent.
- Give each relationship a confidence from `0.0` to `1.0`.
- Treat reflection, dependency injection, dynamic SQL, generated code, message routing, and configuration-driven calls as possible gaps.
- Do not treat tests as production consumers, but use them as behavioral evidence.

## Relationship vocabulary

Use `ORIGINATES_FROM`, `READS`, `WRITES`, `MUTATES`, `VALIDATES`, `BRANCHES_ON`, `TRANSFORMS_TO`, `STORES_IN`, `LOADS_FROM`, `ACCEPTS`, `EXPOSES`, `EMITS`, `CONSUMES`, `CALLS`, `INVALIDATES`, `CONSTRAINS`, or `AFFECTS`. Add a custom relationship only when none applies, and define it in `relationshipTypes`.

## Graph design

Center the graph on the target value. Group nodes into origins, mutation/checking, storage, and downstream effects. Use solid edges for confirmed relationships and dashed edges for inferred or unresolved relationships. Label every edge with its relationship type. Keep node IDs stable between runs so diffs remain meaningful.

## Result summary

Report the target, direct impact, transitive impact, risky unknowns, history coverage, and links to both artifacts. State clearly whether the map is based on static, runtime, declared, contract, and historical evidence.
