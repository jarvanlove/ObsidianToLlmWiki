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
- Governance/linting and index rebuild.
- Private vault sync.
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
- Steps: preserve original -> create source note -> extract text -> create document map and section notes for structured documents -> recommend project/personal/shared/output routing.
- Success: source is searchable, has provenance, and long documents are not reduced to a single vague summary.

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
- Long document ingestion must create a document map and section-level notes before any durable knowledge-page promotion.

## Change Log

| Date | Change | Reason | Impact |
|---|---|---|---|
| 2026-05-19 | Added AI project control workflow to public scaffold | Make production-grade AI coding workflow reusable across attached projects | Documentation/control-plane only |
| 2026-06-10 | Added AI coding lifecycle protocol scaffold | Make project control files update during AI coding instead of remaining static attach artifacts | Scaffold protocol and checklist tooling |
| 2026-06-10 | Added optional AI adapter layer | Allow projects to opt into hook/subagent helpers after the lifecycle protocol is stable | Source scaffold only; adapters are not installed by default |
| 2026-06-10 | Added project cockpit workflow | Reduce daily user burden to start / continue / close while keeping lifecycle checks internal | Product workflow and natural-language entry hardening |
| 2026-06-10 | Added structured source ingestion P0 | Prevent long documents from collapsing into one weak summary | Source note, document map, section notes, and routing candidates |
