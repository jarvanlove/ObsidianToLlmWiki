# Operations

## Routine Operations

- Normal agent entry: `otw.py`; users should continue speaking naturally instead of memorizing commands.
- Environment diagnosis: `doctor.py --strict` after install/upgrade.
- Runtime install: `install.ps1` on Windows or `install.sh` on macOS/Linux; installs an isolated `.venv` and safely installs/updates the global manager Skill.
- Attach project: `attach_project.py` / `.ps1`.
  Optional AI adapters are installed only with `--install-ai-adapters` or `-安装AI适配器`.
- Ingest source: `ingest_source.py` / `.ps1`.
- Search wiki: `search_wiki.py` / `.ps1`.
  Search refreshes the disposable SQLite retrieval cache by default. Use `build_retrieval_index.py --full` only for an explicit full refresh.
- File back answer: `file_back_query.py` / `.ps1`.
- Natural language routing: `handle_nl_request.py` / `.ps1`.
- Project AI session checklist: `project_session.py` / `.ps1`.
  `close` writes `.obsidiantowiki/session-receipt.json`; resolve every candidate before completion.
- Governance: `lint_wiki.py` / `.ps1`.
- Rebuild indexes: `rebuild_indexes.py` / `.ps1`.
- Sync private vault: `sync_private_vault.py` / `.ps1`.
  Sync is manifest-managed and content-aware. Use `--dry-run --format json` before applying and `--path` for a precise repair. Protected runtime paths cannot be selected.
- Retrieval evaluation: `evaluate_retrieval.py --cases 00_system/registry/retrieval_eval_cases.json`.
- Optional agent MCP: install `00_system/requirements-mcp.txt`, then run `mcp_retrieval_server.py` over stdio or the attached project's `scripts/ai/wiki-mcp.py` launcher.
- Legacy provenance: run `migrate_provenance.py` without `--apply` first. A `partial` result requires original-source review before page refs can be completed.
- Compatibility: run `otw.py upgrade` for report-only, then `otw.py upgrade --apply --all-projects` for metadata/hash-safe updates. Uninstalled optional project adapters remain uninstalled.
- Extraction audit: run `source_quality.py --source <file> --format json`; it never prints source content.

## Common Incidents

| Symptom | Check | Likely fix |
|---|---|---|
| Project attach points to wrong vault | `wiki.context.json`, user-level defaults, sibling vault path | Correct context/default and rerun attach |
| Index missing new page | `rebuild_indexes.ps1` output | Rebuild indexes and inspect frontmatter |
| Retrieval misses a recent Markdown edit | JSON `retrieval.refresh`, index file under `00_system/.cache/` | Rerun search with refresh or run `build_retrieval_index.py --full`; deleting the cache is safe |
| Private sync proposes a protected runtime file | JSON sync actions and `private_sync_manifest.json` | Stop; do not force-copy. Fix the manifest/protected globs and rerun dry-run |
| MCP server fails before initialization | Python stderr and optional dependency versions | Install `00_system/requirements-mcp.txt` in an isolated environment; do not upgrade unrelated global projects blindly |
| Retrieval gate passes but semantic probes fail | `semantic_retrieval_recommended=true` | Add or revise inspectable topic aliases first; add embeddings only if probes still fail |
| Lint reports schema errors | page frontmatter and `00_system/registry/page_schemas.json` | Fix page schema or template |
| Shared asset missing in private vault | sync output and `30_shared/索引.md` | Sync scaffold or manually reconcile |
| Upgrade reports shared/project conflicts | `upgrade-candidates/**` and compatibility report | Review `.new` candidates; do not overwrite the local version blindly |
| PDF produces no derivatives | source note `quality_status`, `needs_ocr`, coverage | Run OCR or provide a text-layer PDF; blocked sources intentionally create no weak pages |
| Project remains in `needs_receipt_resolution` | `.obsidiantowiki/session-receipt.json` | Apply, skip, or mark every candidate not applicable, then run `project_session.py resolve` |
| Agent follows wrong entry file | `AGENTS.md`/`CLAUDE.md` wording | Keep entry files peer-level and point both to control files |

## Data Safety

- Public repo should not contain private raw sources, credentials, or private project notes.
- Private vault may contain sensitive data; treat sync operations as high attention.
- Do not run destructive file operations across public/private roots without verifying target paths.
- Retrieval databases are local derived cache and must not be committed or synced between public and private vaults.
- A private policy protects ObsidianToWiki access only; use external-tool/workspace permissions for broader model isolation.

## Maintenance Rules

- Keep public reusable assets and private durable memory balanced.
- If a method becomes generally reusable, place it in public `30_shared/`.
- If a conclusion is specific to the user's project history, place it in private `20_projects/active/...`.
