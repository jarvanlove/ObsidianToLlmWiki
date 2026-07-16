# Tasks

## Now

| ID | Task | Risk | Acceptance | Status |
|---|---|---|---|---|
| OTW-CTRL-001 | Integrate AI project control workflow into public scaffold | P2 | Public repo has control files, shared workflow assets, and updated project bridge templates without making Codex depend on CLAUDE.md | Done |
| OTW-CTRL-002 | Add AI coding lifecycle protocol scaffold | P2 | Public repo has lifecycle protocol docs, control-file templates, session checklist script, and attach support for project support directories | Done |
| OTW-CTRL-003 | Add optional hook/subagent adapter scaffold | P2 | Adapter templates are opt-in, call `project_session.py`, avoid private wiki paths, and do not become a second source of truth | Done |
| OTW-CTRL-004 | Add project cockpit workflow | P2 | Users can rely on `开始工作` / `继续` / `收工`; natural-language attach runs strict checks before reporting success | Done |
| OTW-CTRL-005 | Harden natural-language project cockpit attach | P1 | `开始工作` on an existing project with an empty wiki root bootstraps required runtime templates/schema and `开始工作` / `继续` / `收工` pass on a disposable project | Done |
| OTW-INGEST-001 | Add structured source ingestion P0 | P1 | Document ingestion creates source note, document map, section notes, extracted text scratch file, and routing candidates | Done |
| OTW-INGEST-002 | Add structured ingestion quality fields and lint | P1 | Section notes include theme, concepts, facts, process, bounded excerpts, follow-up questions, promotion candidates, and lint reports missing/oversized structured ingestion outputs | Done |
| OTW-INGEST-003 | Add source promotion candidate workflow | P1 | Section notes can be scanned into a reviewable promotion candidate report with source refs, targets, rationale, next action, and lint backlog reporting | Done |
| OTW-INGEST-004 | Add explicit source section promotion | P1 | A selected section note can be promoted to project/personal/shared/output page with source refs, source section backlink, promoted_to status, and no automatic bulk writes | Done |
| OTW-RETR-001 | Add local Retrieval Core P0 | P1 | Markdown-backed SQLite FTS5 cache refreshes incrementally, filters remain compatible, JSON results preserve provenance, and bounded context packs are available to agents | Done |
| OTW-SYNC-001 | Protect private runtime state during scaffold sync | P0 | Default sync excludes root indexes, logs, project registry, private knowledge, and caches; identical files skip; exact managed paths are supported | Done |
| OTW-RETR-002 | Add repeatable retrieval evaluation gates | P1 | Fixed cases report path/heading/provenance hits, pass rate, MRR, and separate semantic probes | Done |
| OTW-RETR-003 | Add provider-neutral Skill/MCP retrieval adapters | P1 | Project Skills call the thin wrapper; MCP exposes structured search and bounded context over stdio without duplicating retrieval logic | Done |
| OTW-PROV-001 | Audit and migrate legacy provenance metadata | P1 | Only explicit source links/page refs are migrated; uncertain pages remain partial or unchanged; migration is idempotent | Done |
| OTW-RETR-004 | Add minimal hybrid topic-alias recall | P1 | Alias expansion is local and visible in JSON; all semantic probes pass without vector infrastructure | Done |

## Next

- Observe whether `project_session.py start/close` is enough in real AI coding sessions before adding hooks or subagents.
- Test optional hook/subagent adapters in one real project before enabling them as a recommended workflow.
- Observe Skill/MCP retrieval behavior in real Codex, Claude Code, and Cursor sessions before recommending automatic invocation more broadly.
- Upgrade `partial` source-derived pages to `complete` only by rebuilding document maps/section notes and verifying page references against originals.

## Blocked

- None.

## Done

- 2026-05-19: Added AI project control workflow assets and peer entrypoint wording.
- 2026-06-10: Added AI coding lifecycle protocol scaffold, project control templates, `project_session.py`, and attach-time support directories.
- 2026-06-10: Added opt-in hook/subagent adapter templates and `--install-ai-adapters`.
- Existing public/private bridge protocol established through `wiki.context.json`, `AGENTS.md`, and `CLAUDE.md`.
- 2026-06-11: Hardened natural-language project cockpit attach for empty wiki roots.
- 2026-06-11: Added structured source section quality fields and lint reporting.
- 2026-06-11: Added source promotion candidate reports from section notes.
- 2026-06-11: Added explicit source section promotion to formal knowledge pages.
- 2026-07-16: Added the first local Retrieval Core with incremental SQLite FTS5 indexing, stable JSON output, chunk localization, and context packs.
- 2026-07-16: Added protected/idempotent private sync, fixed retrieval evaluation gates, provider-neutral Skills/MCP adapters, conservative provenance migration, and local topic-alias hybrid recall.
