# Deployment

## Delivery Model

ObsidianToWiki is not deployed as a server. It is distributed as a local public runtime, initialized into a private vault, and connected to local projects through ignored context files.

Primary delivery paths:

- Public scaffold repository: `<obsidiantowiki-public-root>`
- Private working vault: `<private-wiki-root>`
- Attached project repositories via `wiki.context.json`, `AGENTS.md`, and `CLAUDE.md`

## Update Flow

1. Maintainer changes public runtime and version manifests.
2. Run local checks from `TESTING.md`, then commit and push the public repository.
3. Users say `更新 ObsidianToWiki`; advanced users run the unified `otw update` wrapper.
4. Update preflight requires a clean public worktree, configured origin/upstream, and fast-forward history.
5. Record matching private baselines before pull, update dependencies and Skills, safely sync private managed files, run migrations, upgrade registered project bridges and installed optional adapters, rebuild indexes, then run strict doctor.
6. Write `00_system/registry/runtime_update_receipt.json` with old/new commits and component results.

## Sync

The update orchestrator owns normal sync. Direct sync is an advanced repair interface. Manifest scope and protected globs define eligible paths; recorded hashes decide whether an existing managed file can be replaced.

## Rollback

- Restore the public runtime to the previous receipt commit with an explicit maintainer-approved Git operation.
- Restore private scaffold files from `40_outputs/update-backups/<timestamp>/`; private knowledge is never a managed rollback target.
- Restore project candidates manually only after comparing local customization with staged `.new` files.
- Re-run migrations only in supported direction, then rebuild indexes and run strict doctor.

## Release Notes

Version-level changes should update `CHANGELOG.md` and private project memory.
