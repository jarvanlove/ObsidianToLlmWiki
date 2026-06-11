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

### Changed

- Documentation tightened for open-source publication
- Project entrypoint wording clarified: Codex uses `AGENTS.md`, Claude Code/compatible tools use `CLAUDE.md`, and shared project facts live in project control files
- Source promotion sync now treats document maps and section notes as parsed source structure instead of final knowledge deposition
- Natural-language project attach now bootstraps missing wiki runtime templates and schema files before creating project pages

### Removed

- Local test artifacts and machine-specific cache outputs
