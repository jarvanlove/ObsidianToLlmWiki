# Private Sync Safety

`sync_private_vault.py` only considers paths declared in `00_system/registry/private_sync_manifest.json`. Normal users reach it through `otw update`; direct use is an advanced repair interface.

Hard-protected state includes private `AGENTS.md` / `CLAUDE.md`, root indexes and logs, privacy policy, project registry, vault/scaffold receipts, all personal and project knowledge, shared architectures/patterns/tools/indexes, outputs, and caches.

Managed files use a recorded SHA-256 baseline:

- destination equals source: `skip`
- destination equals recorded baseline: `update`
- destination is missing: `create`
- destination differs without a safe baseline: preserve it, stage `<path>.new` under `40_outputs/upgrade-candidates/private-scaffold/`, and back up the original under `40_outputs/update-backups/<timestamp>/`

Before a Git update, the runtime records baselines only for files that are byte-identical on both sides. It never adopts a differing private file as managed.

Advanced diagnostics:

```powershell
.\00_system\scripts\otw.ps1 update --check
python .\00_system\scripts\sync_private_vault.py --source-root . --private-root <private-wiki-root> --dry-run --format json
```
