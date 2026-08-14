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

## Human-Controlled AI Engineering 2.0 Target

The approved 2.0 target adds a control and memory-compilation path without replacing the local Markdown-first architecture:

```text
L0 current code/runtime evidence
  > L1 current project controls
  > L2 trusted durable wiki memory
  > L3 AI inference

task state + Git diff + verification + human decisions
  -> context integrity gate and Context Receipt
  -> engineering governance gates
  -> resolved session receipt
  -> atomic memory compiler
  -> bounded current projections
  -> natural-language concierge / action feed / local static cockpit
```

Target components are `context_integrity.py`, `context_contract.py`, `engineering_governance.py`, `memory_compiler.py`, `migrate_project_memory.py`, and `project_cockpit.py`. They extend the existing `otw.py`, `project_session.py`, retrieval, attach, and compatibility paths; they do not introduce a hosted service, business database, background daemon, or second lifecycle.

Markdown remains the durable and auditable format, but it is no longer the default whole-context read unit or the only human interface. Atomic cards own durable facts and explicit lifecycle state. Core project pages become bounded current projections. SQLite remains a disposable retrieval cache. The local cockpit is a generated static projection and never becomes a second source of truth.

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
| Ordinary read-only request | Answer without creating engineering task state |
| Ordinary mutation request | Classify intent, start or resume the single engineering task, then apply P3–P0 gates |

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
| `memory_compiler.py` | Compile active atomic cards into seven budgeted current projections; refuse unmanaged-page overwrite |
| `migrate_project_memory.py` | Dry-run, back up, migrate, conflict-check, and restore legacy core memory pages |
| `project_cockpit.py` | Build one privacy-bounded action projection for both static HTML/JSON and natural-language project status answers |
| `file_back_query.py` | File answer/analysis back into wiki |
| `handle_nl_request.py` | Route explicit commands and ambient ordinary requests; classify read-only/code/external/destructive intent and enter the existing task lifecycle without a daemon |
| `project_session.py` | Generate AI coding task start/close checklists, schema-v2 structured-evidence receipts, seven-part explanation packages, human-understanding gates, evidence-based capability candidates, and control-file update candidates |
| `ui_governance.py` | Create and validate project-local UI task records, locked visual baselines, Design Authority approvals, and visual close evidence |
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
- `00_system/registry/ui_visual_directions.json` holds the auditable 19-palette visual-direction library, its six default directions, and controlled/reference-only selection boundaries.
- `docs/templates/project-adapters/` defines optional hook/subagent adapter templates; these are only installed with an explicit attach flag.
- `docs/templates/global-skills/obsidiantowiki-manager/` defines the once-per-provider natural-language manager Skill.
- `00_system/templates/` defines wiki page schemas, not project repo control files.
- `30_shared/` holds reusable prompts, patterns, tools, and architecture notes.

## Version Boundaries

- `runtime_release.json` declares the public runtime channel plus private scaffold, project scaffold, receipt, and task-state contract versions. During M5 acceptance, `2.0.0-rc.1` prevents the incomplete release from being treated as stable.
- `vault_schema.json` versions knowledge-vault metadata migrations.
- `private_scaffold_state.json` records hashes for manifest-managed private files.
- `.obsidiantowiki/project-scaffold-state.json` records an attached project's managed lifecycle baseline.
- Shared-asset and project-scaffold state may also record an explicit `merged` or `keep-local` resolution against both the current public template hash and reviewed local hash.
- `project_adapter_schema.json` versions optional hooks/subagents/Skills separately from the core bridge.
- `shared_assets.json` versions reusable private shared assets independently.

Normal update order is preflight -> matching-baseline capture -> Git fast-forward -> dependencies/Skill -> private seed/sync -> vault/shared migrations -> core project bridges -> already-installed optional adapters -> indexes/doctor -> receipt.

## Invariants

- Markdown remains source of truth.
- Markdown truth is qualified by fact precedence and health: damaged, disputed, stale, or quarantined pages cannot silently become current execution facts.
- Default model context is contract-driven and budgeted; no task may load the complete project wiki by default.
- Task evidence, not raw chat transcripts, drives durable memory candidates.
- Atomic memory cards preserve history; bounded current projections contain only active, relevant facts and links to evidence.
- Legacy core pages must pass migration dry-run before replacement. Apply preserves byte-exact originals and a manifest; uncertain content remains review-required, and later user customization blocks overwrite.
- Users are not responsible for manually maintaining generated cards or projections; natural language and the local cockpit are the normal human interface.
- Ambient governance is entrypoint-driven, not process-driven: managed project instructions and the global Manager Skill route ordinary mutations through the public runtime, while optional adapters may only report coverage and no background daemon is required.
- Static cockpit HTML/JSON and natural-language status answers must consume the same projection; cockpit output is local derived state under `.obsidiantowiki/`, never a second source of truth.
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
- Project scaffold v4 creates a missing governance guide for new or upgraded projects, updates managed content only when its recorded or legacy hash is unchanged, and stages user-modified conflicts for review. Adapter and task-state readers reject schemas newer than the runtime instead of guessing or downgrading them.
- Project Skills decide when to retrieve; the optional MCP server only exposes the existing retrieval contract.
- Public scaffold must not contain private project secrets or private raw sources.
- Private vault contains real user/project knowledge.
- ObsidianToWiki defines the AI coding lifecycle protocol; attached projects execute it through local control files.
- UI governance is a lifecycle subprotocol: the Agent classifies U0-U3 semantically, `ui_governance.py` validates only artifacts and approvals, and independent Visual QA/human Design Authority judge design quality.
- Visual direction is project-owned: no-reference UI tasks use a fixed fallback without prompting the user, controlled palettes need a user selection record, and `UI_VISUAL_BASELINE.json` remains fixed until an approved U3 RFC changes it. User dissatisfaction first produces local fixes or three plain-language recommendations; technical selection state remains internal.
- Figma, Stitch, hooks, subagents, and named third-party Skills are optional executors; they cannot override a project's Design Authority or silently modify user-global Skill configuration.
- Hook/subagent adapters are optional execution helpers and must call the lifecycle protocol instead of redefining workflow rules.
- Natural-language project attach must be followed by a strict project session check before reporting success.
- User-facing daily workflow should stay low-noise: normal path is `开始工作` -> `继续` -> `收工`; advanced commands remain available but secondary.
- A close workflow is not complete while `.obsidiantowiki/session-receipt.json` has a blocked verification gate or pending candidates. Schema v2 stores structured `evidence`, `gate_results`, `explanation_package`, and `knowledge_candidates`; v1 prose receipts load as `legacy_unstructured` and cannot silently close.
- Every new close receipt carries the same seven-part explanation package. P3 passes automatically, P2 displays without ritual, P1 requires hash-bound human understanding, and P0 also requires explicit authorization; AI-originated confirmation is rejected.
- Capability recovery is signal-based and non-blocking: one lightweight intervention per task, no aggregate score, and only auditable behavior becomes a pending candidate. Capability candidates enter receipts only after verification and understanding pass, never route directly to shared memory, and still require receipt resolution plus the existing memory compiler.
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
