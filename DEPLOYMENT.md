# Deployment

## Delivery Model

ObsidianToWiki is not deployed as a server. It is distributed as a local scaffold repository and synced into a private vault.

Primary delivery paths:

- Public scaffold repository: `<obsidiantowiki-public-root>`
- Private working vault: `<private-wiki-root>`
- Attached project repositories via `wiki.context.json`, `AGENTS.md`, and `CLAUDE.md`

## Update Flow

1. Modify scaffold assets in the public repo.
2. Run local checks from `TESTING.md`.
3. Run the global Skill installer and `doctor.py` in report mode.
4. Dry-run and then apply manifest-managed private sync.
5. Run `otw.py upgrade --apply --all-projects`; migrations are metadata-only and conflicts are staged.
6. Run private vault lint/index rebuild and strict doctor.
7. Update private project memory for durable conclusions.

## Sync

Use existing sync scripts. Before running sync, inspect changed paths so private-only content is not overwritten unintentionally.

```powershell
.\00_system\scripts\sync_private_vault.ps1
```

Sync and upgrade are separate operations: sync distributes public runtime files; upgrade records vault state and reconciles versioned shared/project assets by hash.

## Rollback

- Revert public scaffold files.
- If sync already ran, restore affected private vault scaffold files from git or backup.
- Re-run lint/index rebuild after rollback.

## Release Notes

Version-level changes should update `CHANGELOG.md` and private project memory.
