# Private Vault Setup

This public repository is the scaffold. Your personal knowledge and project knowledge should live in your own private vault or private repository.

## Recommended Layout

Create your own private vault with the same high-level structure:

```text
PrivateVault/
├─ 00_system/
├─ 01_inbox/
├─ 10_personal/
├─ 20_projects/
├─ 30_shared/
├─ 40_outputs/
├─ 90_archive/
├─ Home.md
├─ index.md
├─ log.md
├─ AGENTS.md
├─ CLAUDE.md
├─ README.md
└─ README-zh.md
```

## Setup Steps

1. Create your own private repo or private folder for the real content.
2. Copy the public scaffold structure into it.
3. Keep the public repo as the source of conventions, prompts, and templates.
4. Put your actual personal notes and project notes only in your private vault.
5. For each project workspace, add a minimal `AGENTS.md` and `CLAUDE.md` bootstrap.
6. Point those bootstrap files at your private vault root.
7. Let Codex / Claude Code read the bootstrap first, then open the project wiki pages.
8. Use [docs/private-vault-initialization-checklist.md](docs/private-vault-initialization-checklist.md) as the exact build order.

## What to Copy

Copy these from the public scaffold:

- directory structure
- scripts
- templates
- prompts
- conventions
- startup checklists

For root bootstrap files, use:

- [docs/templates/private-AGENTS.md](docs/templates/private-AGENTS.md)
- [docs/templates/private-CLAUDE.md](docs/templates/private-CLAUDE.md)

## What Not to Copy

Do not copy these into the public repo:

- private personal notes
- private project notes
- raw sources you do not want public
- local operational logs from private use

## Operational Rule

The public scaffold should define the system.
Your private vault should hold your knowledge.

That split keeps the system open-sourceable without exposing your content.
