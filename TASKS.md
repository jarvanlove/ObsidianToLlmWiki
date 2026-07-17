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
| OTW-COMPAT-001 | Add non-destructive vault and scaffold compatibility | P0 | Historical pages remain byte-identical; shared/project modifications stage conflicts; migrations are idempotent | Done |
| OTW-MGR-001 | Add unified runtime and global manager Skill | P1 | Users can speak naturally; agent calls one runtime; Skill upgrades preserve customization | Done |
| OTW-PRIV-001 | Add local AI-access exclusion policy | P0 | Excluded pages leave retrieval, excluded sources cannot be ingested, and files remain available to the user | Done |
| OTW-LIFE-001 | Close lifecycle with session receipts | P1 | `收工` emits a local receipt and every candidate must be resolved | Done |
| OTW-INGEST-005 | Add source extraction quality gate | P0 | Empty/scanned sources are blocked, long sources retain map/sections/refs, and OpenClaw 114-page validation covers every page | Done |
| OTW-INGEST-006 | Harden long-document chapter maps and reingestion | P0 | TOC pages are grouped, body/code lines do not become headings, split chapters retain continuation labels, and obsolete generated sections are removed safely | Done |
| OTW-GOV-001 | Distinguish current health from historical and generated content | P0 | Schema, dead-link, orphan, and stale checks resolve local links correctly, ignore generated/archive evidence where appropriate, and retain a truthful review queue | Done |
| OTW-XPLAT-001 | Add reproducible install, doctor, and three-platform CI | P1 | Python 3.10/3.12 test matrix covers Windows, macOS, Linux; local doctor validates runtime prerequisites | Done |
| OTW-UX-001 | Add one-command product setup | P0 | Root installer creates managed Python, initializes a missing private vault, installs selected provider Skills, migrates/indexes, and passes strict doctor | Done |
| OTW-UX-002 | Add safe whole-product update | P0 | Natural-language update enforces clean fast-forward Git, hash-safe private sync, all-project core bridge upgrades, installed-adapter upgrades, and a receipt | Done |
| OTW-UX-003 | Version core project bridges separately from optional adapters | P0 | Existing projects update managed entry blocks/context/missing controls without reattachment; customized lifecycle files stage candidates | Done |
| OTW-UX-004 | Align onboarding and maintenance documentation | P1 | README/manual/quick start/templates/operations/deployment/security/testing describe one setup and natural-language update contract | Done |
| OTW-UI-001 | Add UI governance runtime | P1 | U0-U3 project UI tasks enforce Design Authority, named-Skill boundaries, approval gates, and visual close evidence without adding UI files to non-UI projects | Done |
| OTW-COMPAT-002 | Persist reviewed local candidate resolutions | P0 | Shared assets and customized lifecycle files accept explicit `merged` or `keep-local`, stop restaging unchanged candidates, and reopen review when public or local content changes | Done |

## Next

- Observe session-receipt candidate quality in real coding sessions and tune recommendations without weakening explicit resolution.
- Test optional hook/subagent adapters in one real project; keep them opt-in even when the base manager Skill is installed globally.
- Observe Skill/MCP retrieval behavior in real Codex, Claude Code, and Cursor sessions before recommending automatic invocation more broadly.
- Observe first-release `.new` conflict volume for existing users without a historical private baseline and refine migration evidence without weakening preservation.
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
- 2026-07-16: Added safe compatibility ledgers, global manager runtime, privacy exclusions, close receipts, cross-platform install/doctor/CI, and source extraction quality gates.
- 2026-07-16: Added one-command setup, natural-language whole-product update, private seed migration, hash-safe private backups/candidates, and versioned all-project core bridge upgrades.
- 2026-07-17: Added hash-bound `merged`/`keep-local` resolutions for shared assets and customized project lifecycle files.
