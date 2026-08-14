# Product Spec

## Product

- Name: ObsidianToWiki.
- Target users: individuals and developers who need durable personal knowledge and project memory across AI coding sessions.
- Core problem: knowledge created in chats, project work, raw files, and repeated decisions gets trapped in sessions or scattered folders.
- Promise: provide an Obsidian-first, markdown-based, LLM-maintained knowledge system for project attachment, source ingestion, retrieval, answer file-back, shared promotion, governance, and private vault sync.

## Current Scope

Must have:

- Public scaffold repository plus private vault operating model.
- One-command first setup that creates the private vault, installs an isolated runtime and provider Skills, migrates state, and verifies the result.
- One natural-language update that safely advances the public runtime, private scaffold, Skills, and every registered project bridge without reattachment.
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
- Passive project operation after one-time attachment: users describe normal work directly; `开始工作`, `继续`, and `收工` remain optional inspection and recovery controls.
- Provider-neutral global manager Skill and `otw.py` runtime so agents, rather than users, invoke lifecycle scripts.
- UI governance for AI coding: U0-U3 task classification, project-local Design Authority, a 19-source visual-direction registry, locked project baselines, direction/RFC gates, visual evidence before UI-task close, and a low-noise feedback flow that turns dissatisfaction into three plain-language recommendations.
- Optional Figma and Stitch workflow adapters that preserve project-owned design facts without requiring either tool for every project.
- Versioned vault, project-adapter, and shared-asset compatibility with hash-safe upgrades and staged conflicts.
- Separate runtime, private-scaffold, core project-scaffold, and optional adapter versions.
- Local `wiki.private.json` AI-access exclusions that remove protected paths from ObsidianToWiki indexing and ingestion without deleting the user's files.
- Extraction quality gates for PDF, DOCX, PPTX, and text sources, including unit coverage, OCR detection, chapter mapping, page references, and bounded excerpts.
- Human-controlled AI engineering with passive task governance, L0-L3 fact precedence, bounded trusted context, evidence-backed memory compilation, human understanding gates, and capability-recovery opportunities.
- Engineering risk classification from P3 documentation and low-impact work through P2 normal changes, P1 critical-flow changes, and P0 destructive, security, payment, or migration work, with progressively stronger human approval.
- Automatic durable-memory maintenance: task evidence becomes reviewable atomic memory cards, current project projections stay within explicit budgets, and obsolete history leaves default context without being deleted.
- Human-first access through natural-language project answers, a low-noise action feed, and a local static project cockpit; opening or manually maintaining Markdown is not required for normal use.

Explicitly not doing unless added to `TASKS.md`:

- Replacing markdown files as the source of truth.
- Requiring a hosted database or vector infrastructure for the baseline system.
- Making autonomous high-risk self-modification without human approval.
- Forcing Codex to read `CLAUDE.md` or Claude Code to read `AGENTS.md`.
- Storing private project knowledge in the public scaffold repository.
- Loading all project control files, all wiki core pages, or complete project history into every model context.
- Treating Markdown page count, Markdown opens, or unbounded knowledge accumulation as product success.
- Requiring users to manually maintain generated memory cards or current projections.

## Core User Flows

### Install or update the product

- Entry: user runs one root installer once, then later says `更新 ObsidianToWiki`.
- Steps: create managed Python environment -> initialize/discover private vault -> install Skills -> migrate/sync -> upgrade registered project bridges -> verify -> write receipt.
- Success: no manual private directory construction, script chain, or project reattachment is required.
- Failure states: dirty/diverged public Git, invalid private policy/state, customized managed file requiring a staged candidate.

### Attach a project

- Entry: user asks to attach current project.
- Steps: discover private wiki root -> create/update bridge files -> create project wiki closure -> write context -> run project session check.
- Success: future AI sessions can recover project context, and the attach report proves required files exist.
- Failure states: private wiki not found, path ambiguity, existing bridge conflict.

### Project cockpit

- Entry: normal coding intent is routed automatically after one-time attachment; explicit cockpit phrases remain available for inspection and recovery.
- Steps: infer project state -> run the matching lifecycle check -> execute or report the next safe action.
- Success: users do not need to remember script names, hook names, or wiki update rules.
- Failure states: missing project context, missing control files, ambiguous task, unverified changes.

### Govern a coding task and maintain memory passively

- Entry: the user asks normally for an explanation, fix, feature, refactor, release, migration, or operational action.
- Steps: classify read/write intent -> capture current facts and Git baseline -> apply risk/root-cause/scope/evidence gates -> build a bounded trusted Context Receipt -> close the verified task -> compile only durable evidence into atomic memory -> rebuild bounded current projections and the human cockpit.
- Success: low-risk work stays low-noise; high-risk or insufficiently understood work stops for human judgment; model context does not grow with project age; the user can understand project state without opening Obsidian.
- Failure states: required context missing, damaged or conflicting memory, unproven root cause, scope drift, insufficient evidence, unresolved human approval, memory compilation conflict.

### Deliver a UI task

- Entry: user describes a page or flow in natural language, optionally naming a Skill, Stitch, or an approved Figma node.
- Steps: Agent classifies U0-U3 -> creates project UI task only when U1+ -> selects the existing visual baseline or a fixed fallback when no reference exists -> records requested Skill and design sources -> obtains direction/RFC approval when required -> implements under the UI Contract -> records browser, Visual QA, and accessibility evidence -> closes through the normal cockpit.
- Success: a named Skill cannot override project design facts; color direction is never randomized; controlled colors require explicit user selection; U2/U3 cannot write production UI before approval; UI release evidence remains in the project repository.
- Failure states: missing selected direction, unapproved controlled direction, baseline change without U3 RFC, missing RFC, absent project design contract, missing screenshot/QA/accessibility evidence.

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
- Generated project bridge files must not contain machine-specific absolute paths; real paths belong only in ignored local context/config files.
- `收工` must create a local receipt and remain incomplete until every control-file/wiki candidate is resolved.
- U1+ UI tasks create project-local design controls only on first use. A fixed default visual direction is used only when no reference or existing baseline exists, without prompting the user. When the user is dissatisfied, the Agent first distinguishes local design defects from a direction issue, then recommends exactly three plain-language default directions and accepts a simple confirmation. Controlled directions require an explicit user choice, and only U3 RFC approval can change a project baseline. UI close validates evidence without pretending that a script can judge aesthetics.
- Long document ingestion must create a document map and section-level notes before any durable knowledge-page promotion.
- A blocked extraction must preserve the original and source note but must not create weak document derivatives.
- Vault and scaffold upgrades must preserve modified private/project files and stage `.new` conflict candidates.
- Public Git updates must be fast-forward only and must stop on uncommitted changes; no automatic stash, reset, or force overwrite is allowed.
- Private root entry files are seed-only assets. Existing customized entries are preserved; an exact legacy public-project entry may be migrated to the private template.
- Core project bridges upgrade independently from optional hooks/subagents: managed entry blocks and ignored local context may update, missing control files may be created, and modified lifecycle files must stage candidates.
- Section-level source notes must expose reviewable quality fields: theme, concepts, facts, process, bounded excerpt, follow-up questions, and promotion candidates.
- Source promotion candidates must be review reports, not automatic formal knowledge pages; each candidate must include source section, source refs, target layer, rationale, and next action.
- Source section promotion must be explicit per section; promoted pages must preserve source section backlinks and source refs, and the source section must record `promoted_to`.
- Retrieval indexes must remain disposable derived data: Markdown is the source of truth, manual edits are visible after incremental refresh, and JSON/context results preserve page paths and source references.
- Retrieval changes must pass fixed path, heading, provenance, pass-rate, and MRR gates before release; semantic infrastructure is justified by failed semantic probes, not trend pressure.
- Legacy provenance migration may only write source notes and page references already explicit in the page; uncertain pages remain `partial` or unchanged.
- Current code/runtime evidence outranks project control files; current project controls outrank trusted durable memory; trusted memory outranks AI inference. Missing facts must remain missing rather than being inferred as project truth.
- Task close receipts use structured verification evidence. Prose-only success claims and passing results with non-zero exit codes cannot close; P1/P0 tasks cannot rely only on AI self-check evidence.
- Every default context pack has a hard budget and Context Receipt. Damaged, stale, conflicting, or quarantined memory must be excluded or explicitly degraded according to task risk.
- Core project wiki pages are bounded current projections, not permanent append-only logs. Historical evidence remains recoverable through atomic cards, task receipts, archives, and Git history.
- A project that has completed real work must not remain an unexplained empty wiki shell; first snapshots derived from local facts remain `review_required` until confirmed.

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
| 2026-07-16 | Added Compatibility and Manager Runtime P2 | Let existing users upgrade safely and operate through natural language | Version ledgers, hash-safe candidates, global Skill, doctor, and unified runtime |
| 2026-07-16 | Added Ingestion Quality Gate P2 | Prevent long or unreadable documents from producing weak knowledge pages | Coverage/OCR checks, chapter-aware maps, exact references, and golden-corpus tests |
| 2026-07-16 | Added product setup and safe update lifecycle | Remove manual onboarding and per-project reattachment while preserving local customization | One-command setup, natural-language update, versioned project bridges, hash-safe private sync, and update receipts |
| 2026-07-17 | Added UI governance runtime | Make AI-generated product UI direction, Skill use, and visual acceptance controllable | U0-U3 UI tasks, project UI Contract/Registry, visual evidence gates, optional Figma/Stitch workflow rules |
| 2026-07-20 | Added governed visual-direction library | Prevent reference-free UI work from becoming a random color choice | 19 auditable source palettes, six stable defaults, controlled selection, locked project baseline, and token constraints |
| 2026-07-20 | Added low-noise visual feedback | Keep visual governance useful to non-specialists without exposing its mechanics | Natural-language dissatisfaction maps to three plain-language choices; simple confirmation is recorded internally |
| 2026-08-13 | Approved Human-Controlled AI Engineering System 2.0 baseline | Prevent AI coding governance from depending on unbounded or untrusted Markdown and make durable memory useful without manual maintenance | Adds trusted context, memory compilation, bounded projections, human cockpit, engineering gates, and phased M0-M5 delivery |
