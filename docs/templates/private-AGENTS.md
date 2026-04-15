# Private Vault AGENTS.md Template

This file belongs at the root of `ObsidianToWiki-private`.

It tells Codex how to start inside the private vault.

```yaml
vault_root: <private-vault-root>
scaffold_root: <public-scaffold-root>
current_project: <project-slug-or-empty>
default_project_index: 20_projects/索引.md
default_personal_index: 10_personal/索引.md
default_shared_index: 30_shared/索引.md
default_output_index: 40_outputs/索引.md
```

## Rules

- Treat this private vault as the source of truth for personal and project knowledge.
- Read `README-zh.md` and `使用手册.md` before making structural changes.
- Open `index.md` and the relevant project `索引.md` before writing.
- Keep durable project conclusions in the private vault.
- Promote reusable knowledge into `30_shared/`.
- Keep raw sources immutable in `01_inbox/raw/`.
