# Operations

## Routine Operations

- Attach project: `attach_project.py` / `.ps1`.
  Optional AI adapters are installed only with `--install-ai-adapters` or `-安装AI适配器`.
- Ingest source: `ingest_source.py` / `.ps1`.
- Search wiki: `search_wiki.py` / `.ps1`.
  Search refreshes the disposable SQLite retrieval cache by default. Use `build_retrieval_index.py --full` only for an explicit full refresh.
- File back answer: `file_back_query.py` / `.ps1`.
- Natural language routing: `handle_nl_request.py` / `.ps1`.
- Project AI session checklist: `project_session.py` / `.ps1`.
- Governance: `lint_wiki.py` / `.ps1`.
- Rebuild indexes: `rebuild_indexes.py` / `.ps1`.
- Sync private vault: `sync_private_vault.py` / `.ps1`.

## Common Incidents

| Symptom | Check | Likely fix |
|---|---|---|
| Project attach points to wrong vault | `wiki.context.json`, user-level defaults, sibling vault path | Correct context/default and rerun attach |
| Index missing new page | `rebuild_indexes.ps1` output | Rebuild indexes and inspect frontmatter |
| Retrieval misses a recent Markdown edit | JSON `retrieval.refresh`, index file under `00_system/.cache/` | Rerun search with refresh or run `build_retrieval_index.py --full`; deleting the cache is safe |
| Lint reports schema errors | page frontmatter and `00_system/registry/page_schemas.json` | Fix page schema or template |
| Shared asset missing in private vault | sync output and `30_shared/索引.md` | Sync scaffold or manually reconcile |
| Agent follows wrong entry file | `AGENTS.md`/`CLAUDE.md` wording | Keep entry files peer-level and point both to control files |

## Data Safety

- Public repo should not contain private raw sources, credentials, or private project notes.
- Private vault may contain sensitive data; treat sync operations as high attention.
- Do not run destructive file operations across public/private roots without verifying target paths.
- Retrieval databases are local derived cache and must not be committed or synced between public and private vaults.

## Maintenance Rules

- Keep public reusable assets and private durable memory balanced.
- If a method becomes generally reusable, place it in public `30_shared/`.
- If a conclusion is specific to the user's project history, place it in private `20_projects/active/...`.
