# Architecture

## System Shape

ObsidianToWiki is a local markdown-first wiki scaffold plus automation scripts.

The product boundary spans four cooperating local components: the public runtime, the private Markdown vault, one global Manager Skill per supported provider environment, and one ignored/versioned bridge per attached project. The Skill and project adapters are routing layers; they do not own knowledge or workflow logic.

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
| `ui_governance.py` | Create and validate project-local UI task records, Design Authority approvals, and visual close evidence |
| `otw.py` | Unified agent-facing runtime for natural language, lifecycle, retrieval, ingestion, doctor, and safe upgrade workflows |
| `runtime_manager.py` | Orchestrate one-command setup and Git-safe whole-product updates |
| `private_vault.py` | Seed private-only entry files and initialize a missing private vault |
| `project_scaffold.py` | Safely upgrade core bridges for every registered project independently from optional adapters |
| `doctor.py` | Diagnose Python dependencies, FTS5, wrappers, private policy, vault schema, and project context without modifying data |
| `vault_compat.py` | Report and apply metadata-only vault schema migrations |
| `project_adapter.py` | Upgrade opt-in project adapters only when managed hashes prove a file is safe to update |
| `shared_assets.py` | Record shared-asset baselines, apply safe updates, and stage conflicts |
| `source_quality.py` | Audit extraction coverage, OCR need, text corruption, and structured-unit quality without printing source content |
| `lint_wiki.py` | Governance and health checks |
| `sync_private_vault.py` | Sync only manifest-managed scaffold files; protect private runtime state |
| `rebuild_indexes.py` | Rebuild indexes |

## Template Boundaries

- `docs/templates/project-AGENTS.md` defines Codex project bridge behavior.
- `docs/templates/project-CLAUDE.md` defines Claude Code / compatible tool bridge behavior.
- `docs/templates/project-control/` defines project control file templates used during project attach.
- `docs/templates/project-ui/` defines UI Contract, Skill Registry, task evidence, QA, and RFC files created only on a project's first U1+ UI task.
- `docs/templates/project-adapters/` defines optional hook/subagent adapter templates; these are only installed with an explicit attach flag.
- `docs/templates/global-skills/obsidiantowiki-manager/` defines the once-per-provider natural-language manager Skill.
- `00_system/templates/` defines wiki page schemas, not project repo control files.
- `30_shared/` holds reusable prompts, patterns, tools, and architecture notes.

## Version Boundaries

- `runtime_release.json` declares the public runtime, private scaffold, and core project scaffold releases.
- `vault_schema.json` versions knowledge-vault metadata migrations.
- `private_scaffold_state.json` records hashes for manifest-managed private files.
- `.obsidiantowiki/project-scaffold-state.json` records an attached project's managed lifecycle baseline.
- Shared-asset and project-scaffold state may also record an explicit `merged` or `keep-local` resolution against both the current public template hash and reviewed local hash.
- `project_adapter_schema.json` versions optional hooks/subagents/Skills separately from the core bridge.
- `shared_assets.json` versions reusable private shared assets independently.

Normal update order is preflight -> matching-baseline capture -> Git fast-forward -> dependencies/Skill -> private seed/sync -> vault/shared migrations -> core project bridges -> already-installed optional adapters -> indexes/doctor -> receipt.

## Invariants

- Markdown remains source of truth.
- The SQLite retrieval index is derived cache only; it must be safe to delete and rebuild from Markdown.
- Agent/API integrations consume stable retrieval results instead of redefining vault scanning, filtering, provenance, or freshness rules.
- Topic aliases are an inspectable local hybrid-retrieval layer; vector retrieval is added only when evaluation probes prove it is needed.
- Private root indexes, logs, project registry, knowledge pages, and retrieval cache are protected from scaffold sync.
- `wiki.private.json` exclusions are enforced by ObsidianToWiki indexing and ingestion; this policy is not an OS sandbox for unrelated agent tools.
- Real machine paths live in ignored `wiki.context.json` or user config, never in public/project scaffold bridge text.
- `wiki.context.json` records both canonical public `runtime_root` and private `wiki_root`; copied private scripts are compatibility assets, not the primary runtime.
- Vault migrations update a metadata ledger only. Shared/project managed files use recorded hashes; local edits produce candidates instead of overwrite.
- A reviewed local resolution suppresses the same candidate only while both public and local hashes remain unchanged; either side changing invalidates the resolution and stages a fresh candidate.
- Public updates are clean-worktree, upstream-known, fast-forward-only operations. They never stash, reset, or force overwrite.
- Private root entry files and knowledge are seed-only/protected. Managed scaffold files update only from a recorded unchanged hash; otherwise a candidate and backup are required.
- Core project scaffold upgrades run for every registered project. Optional adapters remain opt-in and update only when already installed.
- Project Skills decide when to retrieve; the optional MCP server only exposes the existing retrieval contract.
- Public scaffold must not contain private project secrets or private raw sources.
- Private vault contains real user/project knowledge.
- ObsidianToWiki defines the AI coding lifecycle protocol; attached projects execute it through local control files.
- UI governance is a lifecycle subprotocol: the Agent classifies U0-U3 semantically, `ui_governance.py` validates only artifacts and approvals, and independent Visual QA/human Design Authority judge design quality.
- Figma, Stitch, hooks, subagents, and named third-party Skills are optional executors; they cannot override a project's Design Authority or silently modify user-global Skill configuration.
- Hook/subagent adapters are optional execution helpers and must call the lifecycle protocol instead of redefining workflow rules.
- Natural-language project attach must be followed by a strict project session check before reporting success.
- User-facing daily workflow should stay low-noise: normal path is `开始工作` -> `继续` -> `收工`; advanced commands remain available but secondary.
- A close workflow is not complete while `.obsidiantowiki/session-receipt.json` contains pending candidates.
- Source ingestion runs an extraction gate before derivatives; blocked sources cannot produce document maps or section notes.
- Long-document maps group front matter and TOC pages separately, accept only defensible chapter headings, and label size-based chapter continuations explicitly.
- Reingestion may delete only obsolete section files recorded by the previous generated document map; it must not delete hand-authored knowledge pages.
- Governance reports current maintained knowledge separately from generated reports, archived evidence, source sections, and historical snapshots.
- Retrieval keeps generated section notes searchable as evidence but ranks curated knowledge pages above partial keyword matches from generated sections.
- Script changes must preserve existing user content unless explicitly migrating it.
- High-risk learning candidates require review before promotion.
- Multimodal direction remains in-session parsing plus wiki file-back unless a future task changes it.

## Architecture Change Rule

Any change to project attachment, bridge files, private vault discovery, source ingestion, schema validation, sync, or promotion workflow must update this file and the relevant docs/templates.
