# Private Sync Safety

`sync_private_vault.py` copies only paths declared in `00_system/registry/private_sync_manifest.json`.

Protected private runtime state includes:

- `Home.md`, `index.md`, and `log.md`
- `00_system/registry/projects.json`
- `01_inbox/`, `10_personal/`, `20_projects/`, and `40_outputs/`
- shared architectures, patterns, tools, and indexes under `30_shared/`
- `00_system/.cache/` and SQLite files

Identical files are reported as `skip`. Existing managed scaffold files may be updated; private runtime files cannot be selected even with `--path`. Only `30_shared/prompts/` is scaffold-managed inside the shared layer.

```powershell
python .\00_system\scripts\sync_private_vault.py --private-root <private-wiki-root> --dry-run --format json
python .\00_system\scripts\sync_private_vault.py --private-root <private-wiki-root> --path 00_system/scripts/search_wiki.py
```

Always review a real-vault dry-run after changing the sync manifest.
