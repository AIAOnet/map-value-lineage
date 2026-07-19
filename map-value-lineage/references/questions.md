# Required graph questions

Ask and answer these exact questions for every target value:

1. What is the exact entity and value being mapped?
2. What does the value mean in the business or application domain?
3. What are its type, allowed values, nullability, default, constraints, and invariants?
4. What aliases represent the same value in code, APIs, storage, events, UI, configuration, and documentation?
5. Where does the value originate?
6. Which constructors, defaults, APIs, imports, events, configuration sources, database reads, or external systems can supply it?
7. Which methods, functions, jobs, handlers, queries, or users can create, assign, or mutate it?
8. Can any code bypass the intended mutation path?
9. Where is the value validated, normalized, sanitized, authorized, or rejected?
10. Where is the value compared, switched on, matched, filtered, or used to control a branch?
11. Where is the value stored, indexed, cached, copied, logged, measured, backed up, or searched?
12. Which database columns, schemas, constraints, migrations, and serialization formats represent it?
13. Which APIs, commands, forms, files, or messages accept it?
14. Which APIs, views, reports, exports, events, logs, or metrics expose it?
15. Which derived values are calculated from it?
16. Which methods, UI components, permissions, workflows, side effects, and external consumers depend on it directly?
17. What depends on those direct consumers transitively?
18. Which caches, calculations, contracts, assumptions, or indexes must be invalidated or rebuilt when it changes?
19. Which tests specify or depend on its current behavior?
20. Which commits introduced or changed the entity, value, aliases, constraints, mutations, checks, storage, APIs, events, and downstream behavior?
21. Why is each included commit relevant, and what evidence supports that conclusion?
22. Is repository history complete, shallow, squashed, renamed, split across repositories, or otherwise limited?
23. If the proposed change adds, removes, renames, retypes, or reinterprets the value, what is directly affected?
24. What is transitively affected by the proposed change?
25. Could existing stored data, API clients, event consumers, exhaustive branches, reports, or UI code reject or misunderstand the new behavior?
26. Are a migration, backfill, compatibility period, contract version, feature flag, rollout plan, or rollback plan required?
27. Which conclusions are confirmed by static analysis, runtime observation, contracts, declarations, or Git history?
28. Which relationships remain inferred, dynamic, external, or unknown?

Store all 28 questions in `questionsAnswered` with `status`, `answer`, `evidenceRefs`, and `gaps`.
