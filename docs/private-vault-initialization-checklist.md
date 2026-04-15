# Private Vault Initialization Checklist

Use this checklist to create `ObsidianToWiki-private` as your real working vault.

## 1. Create the private vault

Create a private repository or private folder named something like:

```text
ObsidianToWiki-private/
```

Keep it separate from the public scaffold repo.

## 2. Copy the scaffold structure

Mirror the public structure into the private vault:

```text
00_system/
01_inbox/
10_personal/
20_projects/
30_shared/
40_outputs/
90_archive/
Home.md
index.md
log.md
AGENTS.md
CLAUDE.md
README.md
README-zh.md
```

## 3. Copy only framework files

Copy from the public scaffold:

- scripts
- templates
- prompts
- README files
- startup checklists
- conventions and rules

Do not copy private content from the public repo.

## 4. Put the private bootstrap at the root

Create private root bootstrap files:

- `AGENTS.md`
- `CLAUDE.md`

These should point to the private vault root and the private project pages.

## 5. Create the first working indexes

At minimum, make sure these files exist:

- `Home.md`
- `index.md`
- `log.md`
- `10_personal/索引.md`
- `20_projects/索引.md`
- `30_shared/索引.md`
- `40_outputs/索引.md`

## 6. Create your first project workspace

For each real project, create:

- `20_projects/active/<project>/索引.md`
- `20_projects/active/<project>/概览.md`
- `20_projects/active/<project>/架构.md`
- `20_projects/active/<project>/决策.md`
- `20_projects/active/<project>/经验.md`
- `20_projects/active/<project>/来源.md`
- `20_projects/active/<project>/任务.md`
- `20_projects/active/<project>/notes/`
- `20_projects/active/<project>/source-notes/`
- `20_projects/active/<project>/sources/`

## 7. Wire agent startup

Make the project workspace bootstrap point back to the private vault.

The agent should read the workspace bootstrap before touching the project.

## 8. Start using it

From this point on:

- raw sources go into `01_inbox/raw/`
- project memory goes into `20_projects/active/<project>/`
- reusable knowledge goes into `30_shared/`
- analysis outputs go into `40_outputs/`
- every meaningful change gets logged

## 9. Keep the public scaffold separate

Only sync framework changes back from the public repository.

Never sync your private notes or project outputs into the public repo.
