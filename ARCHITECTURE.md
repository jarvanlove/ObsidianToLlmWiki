# Architecture

## System Shape

ObsidianToWiki is a local markdown-first wiki scaffold plus automation scripts.

| Layer | Directories | Owns |
|---|---|---|
| Source layer | `01_inbox/`, project `sources/`, project `source-notes/` | raw material, clips, temporary intake |
| Memory layer | `10_personal/`, `20_projects/`, `30_shared/`, `40_outputs/` | durable personal/project/shared/output knowledge |
| Automation layer | `00_system/scripts/`, `00_system/templates/`, `00_system/registry/` | attach, ingest, search, file-back, governance, sync |
| Documentation layer | root docs, `docs/`, `Home.md`, `README*.md` | user-facing instructions and design plans |

## Entry Files

- `AGENTS.md`: Codex entrypoint for this repo.
- `CLAUDE.md`: Claude Code / compatible tools entrypoint.
- `wiki.context.json`: bridge to the private wiki project memory.

Important: `AGENTS.md` and `CLAUDE.md` are peer entrypoints. Shared project facts belong in `PRODUCT_SPEC.md`, `ARCHITECTURE.md`, `TASKS.md`, `TESTING.md`, `DEPLOYMENT.md`, `OPERATIONS.md`, `SECURITY.md`, and private wiki project pages.

## Core Scripts

| Script | Purpose |
|---|---|
| `attach_project.py` | Attach project to private wiki and write bridge files |
| `ingest_source.py` | Ingest source files and create source notes |
| `search_wiki.py` | Search wiki with weighting and relation summaries |
| `file_back_query.py` | File answer/analysis back into wiki |
| `handle_nl_request.py` | Route natural-language requests |
| `lint_wiki.py` | Governance and health checks |
| `sync_private_vault.py` | Sync public scaffold into private vault |
| `rebuild_indexes.py` | Rebuild indexes |

## Template Boundaries

- `docs/templates/project-AGENTS.md` defines Codex project bridge behavior.
- `docs/templates/project-CLAUDE.md` defines Claude Code / compatible tool bridge behavior.
- `00_system/templates/` defines wiki page schemas, not project repo control files.
- `30_shared/` holds reusable prompts, patterns, tools, and architecture notes.

## Invariants

- Markdown remains source of truth.
- Public scaffold must not contain private project secrets or private raw sources.
- Private vault contains real user/project knowledge.
- Script changes must preserve existing user content unless explicitly migrating it.
- High-risk learning candidates require review before promotion.
- Multimodal direction remains in-session parsing plus wiki file-back unless a future task changes it.

## Architecture Change Rule

Any change to project attachment, bridge files, private vault discovery, source ingestion, schema validation, sync, or promotion workflow must update this file and the relevant docs/templates.
