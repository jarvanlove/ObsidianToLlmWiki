# Changelog

## 2026-07-20

- Added low-noise visual feedback: users can describe dissatisfaction naturally, receive three plain-language direction recommendations, and confirm with a simple reply while governance records remain internal.

All notable changes to this repository should be documented in this file.

## Unreleased

### Removed

- Removed the local HTML/JSON project dashboard, its command surface, templates, screenshots, QA records, and browser-oriented tests. `项目现在怎么样` remains available as a direct, read-only natural-language answer over bounded project state.

## 2.0.0 - 2026-08-14

### Added

- Stable runtime `2.0.0` with A-J Human-Controlled AI end-to-end acceptance and three isolated pilots covering a clean project, pre-existing uncommitted work, and a simulated P1 authentication boundary; receipt/state summaries contain no credentials or business code.
- Product-owner acceptance of M5 closes the M0-M5 Human-Controlled AI Engineering System 2.0 iteration; main integration was later explicitly authorized behind the release-documentation, private-Wiki, and final-verification gates.
- Project scaffold v4 and runtime compatibility contracts: newly attached projects receive the governance guide, user-modified project files remain untouched or stage review candidates, v1 receipts and active tasks remain usable, JavaScript UTC `Z` evidence timestamps validate consistently, and newer task/adapter state schemas fail closed.
- Ambient governance for ordinary coding language: deterministic read-only/code/external/destructive intent routing, transparent single-task start/resume, one-line P3/P2 status, P1 responsibility confirmation, P0 explicit authorization, fail-closed unattached mutations, managed project-entry rules, and no background daemon dependency.
- M4 machine-acceptance evidence for the seven-part explanation package, P2 low-noise display, hash-bound P1 human confirmation, separate P0 authorization, five bounded capability triggers, three fixed choices, receipt-before-memory ordering, pending review, and no direct personal/shared write; M4 is approved and M5 is authorized to begin from Task 10.
- Evidence-based capability recovery with five bounded triggers, one low-noise intervention per task, three fixed user choices, allowlisted observable events, no aggregate scoring, and pending receipt-backed candidates that cannot write directly to personal or shared memory.
- Seven-part critical-change explanation packages and human-understanding gates with secret/path-safe summaries, low-noise P3/P2 behavior, hash-bound P1 confirmation, explicit P0 authorization, and rejection of AI-originated confirmation.
- M3 machine-acceptance evidence for explainable risk, Bug root-cause, scope-drift, patch-loop, responsibility, and structured-verification gates, including PowerShell seven-digit ISO timestamp compatibility; M3 is accepted and M4 Tasks 8-9 are complete.
- Schema-v2 task close receipts with structured verification evidence, source allowlisting, non-zero exit/result consistency, P1/P0 independent-evidence gates, and fail-closed v1 prose receipt compatibility.
- Human-first natural-language “项目现在怎么样” routing over bounded project state and Context Receipt evidence.
- Seven bounded current-memory projections, a 90-day/30-event timeline, active-only fact filtering, and public `otw memory compile` commands.
- Dry-run-first legacy memory migration with byte-exact backups, source backlinks, review-required snapshots, idempotent manifests, customization conflict protection, and restoration support.
- Deterministic atomic-memory compiler for resolved task receipts, with stable card identity, idempotent compilation, explicit supersede/dispute states, high-risk and cross-layer review, sensitive-content rejection, and cards that pass the existing context-integrity gate.
- Bounded Context Contracts and persisted Context Receipts with L0 Git state, L1 control hashes, trusted project memory, whole-card budgets, explicit missing/conflict states, and deterministic content hashes.
- Read-only context integrity gate with deterministic trusted/review/degraded/quarantined states, strict fail-closed handling for damaged or missing required context, unified `otw context check`, and doctor integration.
- Approved and delivered the Human-Controlled AI Engineering System 2.0 baseline: L0-L3 fact precedence, context integrity and receipts, bounded context, atomic evidence-backed memory, bounded current projections, passive engineering gates, human understanding, capability recovery, and human-first natural-language status.

- Initial ObsidianToWiki scaffold
- Dual agent entrypoints for Codex and Claude Code
- AI project control workflow assets for production-grade AI-assisted development
- Cross-platform script wrappers
- Source ingest, search, index rebuild, and lint tooling
- Shared prompt templates
- Session start page
- AI coding lifecycle protocol, control-file templates, and project session checklist script
- Optional hook/subagent adapter templates for projects that explicitly opt in
- Structured source ingestion with document maps, section notes, extracted text scratch files, and source reference schemas
- Structured source section quality fields for theme, concepts, facts, process, bounded excerpts, follow-up questions, and promotion candidates
- Source promotion candidate reports generated from section notes
- Explicit source section promotion into project, personal, shared, or output pages
- Local SQLite FTS5 retrieval cache with incremental freshness checks
- Stable retrieval JSON contract and bounded agent context-pack output
- Protected, idempotent private scaffold sync with precise managed-path support
- Fixed retrieval evaluation gates with MRR and separate semantic probes
- Project Agent Skills and read-only MCP stdio retrieval tools
- Conservative legacy provenance audit/migration and `source_notes` retrieval output
- Inspectable topic-alias hybrid recall; current evaluation does not justify vector infrastructure
- Retrieval core regression tests for filters, provenance, update, deletion, and context budgets
- Unified `otw.py` agent runtime and safely upgradeable global manager Skill
- Vault schema ledger, shared-asset baselines, project-adapter versions, and historical compatibility tests
- `wiki.private.json` AI-access exclusions for retrieval and ingestion
- Session close receipts with explicit candidate resolution
- Reproducible dependencies, cross-platform installers, doctor diagnostics, and Windows/macOS/Linux CI
- PDF/DOCX/PPTX/text extraction quality gates, CJK PDF normalization, OCR detection, chapter-aware maps, and golden-corpus tests
- Wiki governance regression tests for local link resolution, generated/archive boundaries, freshness semantics, and schema exceptions
- One-command private-vault setup through the root Windows/macOS/Linux installers
- Machine-readable runtime and core project-scaffold release manifests
- Natural-language whole-product update with clean fast-forward Git preflight and update receipts
- Hash-baselined private scaffold sync with staged candidates and timestamped backups
- Safe all-project core bridge upgrades independent from optional hooks/subagents
- Hash-bound `merged`/`keep-local` decisions for reviewed shared-asset and project-lifecycle candidates
- Project-local UI governance runtime with U0-U3 task classification, UI Contract, Skill Registry, direction/RFC approval, and visual evidence gates
- Optional Figma/Stitch workflow rules that keep design tools and named Skills below project Design Authority
- Governed 19-palette visual-direction registry, six stable defaults, controlled palette selection, and locked project UI baselines

### Changed

- Retrieval context output now excludes quarantined evidence, keeps raw source material searchable but below governed knowledge, and routes natural-language project answers through the receipt-producing context contract.
- `README.md` is now the Chinese GitHub landing page; the English guide is `README-EN.md`, while `README-zh.md` remains a compatibility redirect
- Documentation tightened for open-source publication
- Project entrypoint wording clarified: Codex uses `AGENTS.md`, Claude Code/compatible tools use `CLAUDE.md`, and shared project facts live in project control files
- Source promotion sync now treats document maps and section notes as parsed source structure instead of final knowledge deposition
- Natural-language project attach now bootstraps missing wiki runtime templates and schema files before creating project pages
- Wiki lint now reports malformed structured ingestion outputs, including missing section links, missing source references, and oversized section excerpts
- Wiki lint now reports generated section notes that still need promotion review after the backlog threshold
- Promoted source pages preserve source section backlinks and source refs, while the section note records `promoted_to`
- Wiki search now reads a disposable local index, refreshes changed Markdown before querying, and returns the best matching heading and snippet without replacing Markdown as source of truth
- Project bridge text no longer embeds machine paths; ignored local context/config files own real paths
- First-time attach now bootstraps the complete missing wiki runtime and locally excludes context/receipt state from Git
- Structured ingestion creates the document map before section notes and blocks weak derivatives when extraction quality fails
- Long-document ingestion groups cover/TOC pages, rejects body facts and code comments as chapter headings, labels continued chapters, and removes only obsolete generated sections during reingestion
- Wiki lint resolves sibling and nearest project links, ignores links inside fenced code, and separates current maintained pages from generated reports, source sections, and historical archives
- Retrieval downranks generated document maps and section notes so curated knowledge remains the default answer surface while source evidence stays searchable
- `wiki.context.json` now records canonical public `runtime_root` and core project-scaffold version
- Manager and optional project adapters prefer the repository-managed `.venv`
- Existing projects no longer require `scripts/ai` unless optional adapters are explicitly installed
- Onboarding and update documentation now presents one installer followed by natural-language operation
- Reviewed local customizations no longer restage the same `.new` candidate until either the public template or local file changes

### Removed

- Local test artifacts and machine-specific cache outputs
- The tracked empty `scripts/ai` placeholder from the default project scaffold
