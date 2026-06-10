# Tasks

## Now

| ID | Task | Risk | Acceptance | Status |
|---|---|---|---|---|
| OTW-CTRL-001 | Integrate AI project control workflow into public scaffold | P2 | Public repo has control files, shared workflow assets, and updated project bridge templates without making Codex depend on CLAUDE.md | Done |
| OTW-CTRL-002 | Add AI coding lifecycle protocol scaffold | P2 | Public repo has lifecycle protocol docs, control-file templates, session checklist script, and attach support for project support directories | Done |
| OTW-CTRL-003 | Add optional hook/subagent adapter scaffold | P2 | Adapter templates are opt-in, call `project_session.py`, avoid private wiki paths, and do not become a second source of truth | Done |
| OTW-CTRL-004 | Add project cockpit workflow | P2 | Users can rely on `开始工作` / `继续` / `收工`; natural-language attach runs strict checks before reporting success | Done |
| OTW-INGEST-001 | Add structured source ingestion P0 | P1 | Document ingestion creates source note, document map, section notes, extracted text scratch file, and routing candidates | Done |

## Next

- Observe whether `project_session.py start/close` is enough in real AI coding sessions before adding hooks or subagents.
- Test optional hook/subagent adapters in one real project before enabling them as a recommended workflow.

## Blocked

- None.

## Done

- 2026-05-19: Added AI project control workflow assets and peer entrypoint wording.
- 2026-06-10: Added AI coding lifecycle protocol scaffold, project control templates, `project_session.py`, and attach-time support directories.
- 2026-06-10: Added opt-in hook/subagent adapter templates and `--install-ai-adapters`.
- Existing public/private bridge protocol established through `wiki.context.json`, `AGENTS.md`, and `CLAUDE.md`.
