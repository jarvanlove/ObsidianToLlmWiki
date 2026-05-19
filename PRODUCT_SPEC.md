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
- Project memory pages: overview, architecture, decisions, tasks, sources, relations, risks, timeline, runtime memory.
- Personal knowledge distillation and shared knowledge promotion.
- Search and answer file-back.
- Governance/linting and index rebuild.
- Private vault sync.
- AI project control workflow assets for production-grade AI-assisted development.

Explicitly not doing unless added to `TASKS.md`:

- Replacing markdown files as the source of truth.
- Requiring a hosted database or vector infrastructure for the baseline system.
- Making autonomous high-risk self-modification without human approval.
- Forcing Codex to read `CLAUDE.md` or Claude Code to read `AGENTS.md`.
- Storing private project knowledge in the public scaffold repository.

## Core User Flows

### Attach a project

- Entry: user asks to attach current project.
- Steps: discover private wiki root -> create/update bridge files -> create project wiki closure -> write context.
- Success: future AI sessions can recover project context.
- Failure states: private wiki not found, path ambiguity, existing bridge conflict.

### Ingest a source

- Entry: user provides file/material.
- Steps: preserve original -> create source note -> derive durable page if needed -> link to project/personal/shared layer.
- Success: source is searchable and has provenance.

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

## Change Log

| Date | Change | Reason | Impact |
|---|---|---|---|
| 2026-05-19 | Added AI project control workflow to public scaffold | Make production-grade AI coding workflow reusable across attached projects | Documentation/control-plane only |
