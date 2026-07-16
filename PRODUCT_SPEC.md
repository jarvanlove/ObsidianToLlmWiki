# Product Spec

## Product

- Name: ObsidianToWiki.
- Target users: individuals and developers who need durable personal knowledge and project memory across AI coding sessions.
- Core problem: knowledge created in chats, project work, raw files, and repeated decisions gets trapped in sessions or scattered folders.
- Promise: provide an Obsidian-first, markdown-based, LLM-maintained knowledge system for project attachment, source ingestion, retrieval, answer file-back, shared promotion, governance, and private vault sync.

## Current Scope

Must have:

- Public scaffold repository plus private vault operating model.
- Project attachment through `wiki.context.json`, `AGENTS.md`, and `CLAUDE.md`.
- Source ingestion for text, documents, code, and registered media sources.
- Structured source ingestion for long documents with source notes, document maps, section notes, and provenance references.
- Project memory pages: overview, architecture, decisions, tasks, sources, relations, risks, timeline, runtime memory.
- Personal knowledge distillation and shared knowledge promotion.
- Search and answer file-back.
- Local rebuildable retrieval index with automatic freshness checks, stable JSON results, and bounded context packs for agent consumption.
- Fixed retrieval evaluation gates, inspectable topic-alias expansion, and optional read-only Skills/MCP adapters.
- Governance/linting and index rebuild.
- Private vault sync that cannot overwrite root indexes, logs, project registry, private knowledge, or derived caches.
- AI project control workflow assets for production-grade AI-assisted development.
- AI coding lifecycle protocol for task start, verification, close, control-file updates, and wiki file-back candidates.
- Optional hook/subagent adapter templates that call the lifecycle protocol without becoming a separate source of truth.
- Project cockpit workflow that lets users operate daily work through only three phrases: `开始工作`, `继续`, and `收工`.

Explicitly not doing unless added to `TASKS.md`:

- Replacing markdown files as the source of truth.
- Requiring a hosted database or vector infrastructure for the baseline system.
- Making autonomous high-risk self-modification without human approval.
- Forcing Codex to read `CLAUDE.md` or Claude Code to read `AGENTS.md`.
- Storing private project knowledge in the public scaffold repository.

## Core User Flows

### Attach a project

- Entry: user asks to attach current project.
- Steps: discover private wiki root -> create/update bridge files -> create project wiki closure -> write context -> run project session check.
- Success: future AI sessions can recover project context, and the attach report proves required files exist.
- Failure states: private wiki not found, path ambiguity, existing bridge conflict.

### Project cockpit

- Entry: user says `开始工作`, `继续`, or `收工`.
- Steps: infer project state -> run the matching lifecycle check -> execute or report the next safe action.
- Success: users do not need to remember script names, hook names, or wiki update rules.
- Failure states: missing project context, missing control files, ambiguous task, unverified changes.

### Ingest a source

- Entry: user provides file/material.
- Steps: preserve original -> create source note -> extract text -> create document map and section notes for structured documents -> recommend project/personal/shared/output routing -> generate reviewable promotion candidates.
- Success: source is searchable, has provenance, can be reviewed as promotion candidates, and selected sections can be explicitly promoted to formal knowledge pages.

### File back an answer

- Entry: useful answer or conclusion appears in chat.
- Steps: determine destination layer -> write markdown page or update existing page -> rebuild indexes if needed.
- Success: knowledge is no longer trapped in the chat.

### Promote reusable workflow

- Entry: repeated pattern or approved learning candidate.
- Steps: record candidate -> review risk -> promote into `30_shared/`.
- Success: future projects can reuse the asset.

## Acceptance Criteria

- Tool entry files remain independent: Codex uses `AGENTS.md`; Claude Code/compatible tools use `CLAUDE.md`.
- Shared project facts live in project control files and wiki pages, not only in one tool entry file.
- Public scaffold and private vault stay balanced: reusable scaffold assets in public, real project memory in private.
- Scripts are conservative with existing user files and avoid overwriting project-specific rules without preserving them.
- Natural-language project attach must end with a machine-checkable report; missing required files means the attach is not complete.
- Natural-language project attach must bootstrap missing wiki runtime templates and schema files when the selected wiki root is otherwise usable.
- Long document ingestion must create a document map and section-level notes before any durable knowledge-page promotion.
- Section-level source notes must expose reviewable quality fields: theme, concepts, facts, process, bounded excerpt, follow-up questions, and promotion candidates.
- Source promotion candidates must be review reports, not automatic formal knowledge pages; each candidate must include source section, source refs, target layer, rationale, and next action.
- Source section promotion must be explicit per section; promoted pages must preserve source section backlinks and source refs, and the source section must record `promoted_to`.
- Retrieval indexes must remain disposable derived data: Markdown is the source of truth, manual edits are visible after incremental refresh, and JSON/context results preserve page paths and source references.
- Retrieval changes must pass fixed path, heading, provenance, pass-rate, and MRR gates before release; semantic infrastructure is justified by failed semantic probes, not trend pressure.
- Legacy provenance migration may only write source notes and page references already explicit in the page; uncertain pages remain `partial` or unchanged.

## Change Log

| Date | Change | Reason | Impact |
|---|---|---|---|
| 2026-05-19 | Added AI project control workflow to public scaffold | Make production-grade AI coding workflow reusable across attached projects | Documentation/control-plane only |
| 2026-06-10 | Added AI coding lifecycle protocol scaffold | Make project control files update during AI coding instead of remaining static attach artifacts | Scaffold protocol and checklist tooling |
| 2026-06-10 | Added optional AI adapter layer | Allow projects to opt into hook/subagent helpers after the lifecycle protocol is stable | Source scaffold only; adapters are not installed by default |
| 2026-06-10 | Added project cockpit workflow | Reduce daily user burden to start / continue / close while keeping lifecycle checks internal | Product workflow and natural-language entry hardening |
| 2026-06-10 | Added structured source ingestion P0 | Prevent long documents from collapsing into one weak summary | Source note, document map, section notes, and routing candidates |
| 2026-06-11 | Hardened natural-language project attach | Make `开始工作` stable for empty but valid wiki roots | Missing runtime templates/schema are bootstrapped before project page creation |
| 2026-06-11 | Added structured source section quality checks | Make source ingestion outputs reviewable before promotion | Section notes gain quality fields and lint reports malformed structured ingestion outputs |
| 2026-06-11 | Added source promotion candidate workflow | Prevent section notes from becoming a dead end | Candidate report lists source refs, targets, rationale, and next actions |
| 2026-06-11 | Added explicit source section promotion | Turn selected section notes into formal knowledge pages without bulk auto-writing | Promoted pages preserve backlinks and source refs |
| 2026-07-16 | Added local Retrieval Core P0 | Give agents a stable, fresh, provider-neutral knowledge retrieval contract | SQLite FTS5 derived index, JSON output, chunk localization, and bounded context packs |
| 2026-07-16 | Completed Retrieval Integration P1 | Make retrieval safe to distribute and directly consumable by coding agents | Protected private sync, evaluation gates, topic aliases, Skills/MCP adapters, and provenance migration |
