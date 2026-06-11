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

### Changed

- Documentation tightened for open-source publication
- Project entrypoint wording clarified: Codex uses `AGENTS.md`, Claude Code/compatible tools use `CLAUDE.md`, and shared project facts live in project control files
- Source promotion sync now treats document maps and section notes as parsed source structure instead of final knowledge deposition
- Natural-language project attach now bootstraps missing wiki runtime templates and schema files before creating project pages
- Wiki lint now reports malformed structured ingestion outputs, including missing section links, missing source references, and oversized section excerpts
- Wiki lint now reports generated section notes that still need promotion review after the backlog threshold

### Removed

- Local test artifacts and machine-specific cache outputs
