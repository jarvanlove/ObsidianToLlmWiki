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

Daily project work is exposed through the project cockpit:

| User phrase | Internal lifecycle |
|---|---|
| `开始工作` | Detect attach state, attach if needed, run project session check, summarize next safe action |
| `继续` | Restore context, inspect task/diff state, run task start guidance |
| `收工` | Inspect diff and verification, generate control-file and wiki file-back candidates |

## Core Scripts

| Script | Purpose |
|---|---|
| `attach_project.py` | Attach project to private wiki and write bridge files |
| `ingest_source.py` | Ingest source files and create source notes |
| `search_wiki.py` | Search wiki with weighting and relation summaries |
| `retrieval_index.py` | Maintain the disposable SQLite FTS5 retrieval cache and Markdown freshness state |
| `build_retrieval_index.py` | Explicitly build or fully refresh the local retrieval cache |
| `evaluate_retrieval.py` | Run fixed path/heading/provenance/MRR retrieval gates and semantic probes |
| `mcp_retrieval_server.py` | Expose the stable retrieval contract as two read-only MCP stdio tools |
| `migrate_provenance.py` | Audit and conservatively recover explicit source metadata from legacy knowledge pages |
| `file_back_query.py` | File answer/analysis back into wiki |
| `handle_nl_request.py` | Route natural-language requests |
| `project_session.py` | Generate AI coding task start/close checklists and control-file update candidates |
| `lint_wiki.py` | Governance and health checks |
| `sync_private_vault.py` | Sync only manifest-managed scaffold files; protect private runtime state |
| `rebuild_indexes.py` | Rebuild indexes |

## Template Boundaries

- `docs/templates/project-AGENTS.md` defines Codex project bridge behavior.
- `docs/templates/project-CLAUDE.md` defines Claude Code / compatible tool bridge behavior.
- `docs/templates/project-control/` defines project control file templates used during project attach.
- `docs/templates/project-adapters/` defines optional hook/subagent adapter templates; these are only installed with an explicit attach flag.
- `00_system/templates/` defines wiki page schemas, not project repo control files.
- `30_shared/` holds reusable prompts, patterns, tools, and architecture notes.

## Invariants

- Markdown remains source of truth.
- The SQLite retrieval index is derived cache only; it must be safe to delete and rebuild from Markdown.
- Agent/API integrations consume stable retrieval results instead of redefining vault scanning, filtering, provenance, or freshness rules.
- Topic aliases are an inspectable local hybrid-retrieval layer; vector retrieval is added only when evaluation probes prove it is needed.
- Private root indexes, logs, project registry, knowledge pages, and retrieval cache are protected from scaffold sync.
- Project Skills decide when to retrieve; the optional MCP server only exposes the existing retrieval contract.
- Public scaffold must not contain private project secrets or private raw sources.
- Private vault contains real user/project knowledge.
- ObsidianToWiki defines the AI coding lifecycle protocol; attached projects execute it through local control files.
- Hook/subagent adapters are optional execution helpers and must call the lifecycle protocol instead of redefining workflow rules.
- Natural-language project attach must be followed by a strict project session check before reporting success.
- User-facing daily workflow should stay low-noise: normal path is `开始工作` -> `继续` -> `收工`; advanced commands remain available but secondary.
- Script changes must preserve existing user content unless explicitly migrating it.
- High-risk learning candidates require review before promotion.
- Multimodal direction remains in-session parsing plus wiki file-back unless a future task changes it.

## Architecture Change Rule

Any change to project attachment, bridge files, private vault discovery, source ingestion, schema validation, sync, or promotion workflow must update this file and the relevant docs/templates.
