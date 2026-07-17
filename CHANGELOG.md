# Changelog

All notable changes to this repository should be documented in this file.

## Unreleased

### Added

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

### Changed

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
