# ObsidianToWiki

Obsidian-first wiki scaffold for building a durable LLM-maintained knowledge system.

Chinese guide: [README-zh.md](README-zh.md)

## What This System Is For

This system is built for one practical goal:

turn scattered raw material, project context, and useful conclusions into a maintainable local wiki that keeps getting better over time.

It serves two scopes at the same time:

- personal knowledge
- project memory

The repository itself is the scaffold, not the final working vault.

Recommended split:

- `ObsidianToWiki`: public scaffold, scripts, templates, rules, docs
- `ObsidianToWiki-private`: private vault with real personal knowledge, project knowledge, and raw sources

## What Problems It Solves

The system is meant to solve four recurring problems:

1. raw files get collected but never organized
2. project context disappears across coding sessions
3. useful answers stay in chat windows instead of becoming assets
4. reusable knowledge does not flow from one project to the next

## Architecture

The design has three layers:

1. source layer
   Raw files, clips, and temporary materials waiting to be processed.
2. memory layer
   Personal notes, project sub-wikis, shared reusable knowledge, and filed-back outputs.
3. automation layer
   Scripts, templates, schemas, sync rules, and agent bootstrap files.

The operating model is:

- humans decide value and boundaries
- agents ingest, summarize, link, file back, and maintain structure
- markdown files remain the source of truth

## Full Repository Structure

```text
ObsidianToWiki/
├─ .obsidian/                         Obsidian local settings
├─ 00_system/
│  ├─ registry/                      machine-readable schemas and sync manifests
│  ├─ scripts/                       automation scripts and shell wrappers
│  └─ templates/                     page templates
├─ 01_inbox/
│  ├─ clips/                         source notes that are not yet fully distilled
│  ├─ raw/                           immutable raw source files
│  └─ scratch/                       temporary working material
├─ 10_personal/
│  └─ 索引.md                         personal knowledge entry
├─ 20_projects/
│  ├─ active/                        active project sub-wikis
│  ├─ archive/                       archived project sub-wikis
│  ├─ 关系索引.md                     cross-project relation index
│  └─ 索引.md                         project knowledge entry
├─ 30_shared/
│  ├─ architectures/                 reusable architecture notes
│  ├─ patterns/                      reusable patterns
│  ├─ prompts/                       reusable prompts
│  ├─ tools/                         reusable tool notes
│  └─ 索引.md                         shared knowledge entry
├─ 40_outputs/
│  ├─ analyses/                      filed-back analyses
│  ├─ briefings/                     summaries and briefings
│  ├─ reflections/                   learning candidates and reflections
│  └─ 索引.md                         output entry
├─ 90_archive/                       low-frequency retained material
├─ docs/
│  ├─ plans/                         design docs kept as background context
│  └─ templates/                     root/bootstrap template files
├─ AGENTS.md                         Codex rules for this scaffold
├─ CHANGELOG.md                      release history for the public scaffold
├─ CLAUDE.md                         Claude Code rules for this scaffold
├─ CONTRIBUTING.md                   contribution guide for open-source use
├─ Home.md                           human entry page
├─ index.md                          top-level index
├─ LICENSE                           open-source license
├─ log.md                            append-only maintenance log
├─ README.md                         English overview
├─ README-zh.md                      Chinese overview
├─ SECURITY.md                       security policy
├─ 会话启动页.md                      copyable agent session templates
├─ 使用手册.md                        day-to-day usage guide
└─ 快速开始.md                        minimal onboarding guide
```

## What Each Main Area Means

- `00_system/`
  System internals. Scripts, templates, schema definitions, and sync manifests live here.
- `01_inbox/`
  Intake area. New material enters here before it becomes durable knowledge.
- `10_personal/`
  Long-lived personal knowledge.
- `20_projects/`
  One sub-wiki per project. This is the working memory layer.
- `30_shared/`
  Reusable knowledge across projects.
- `40_outputs/`
  Analyses, summaries, and other results that should be filed back.
- `90_archive/`
  Retained but low-frequency content.

## Project Sub-Wiki Structure

Each active project is expected to look like this:

```text
20_projects/active/<project-slug>/
├─ notes/
├─ source-notes/
├─ sources/
├─ project.memory.md
├─ 任务.md
├─ 关系.md
├─ 决策.md
├─ 时间线.md
├─ 架构.md
├─ 来源.md
├─ 概览.md
├─ 索引.md
└─ 风险.md
```

Core pages:

- `索引.md`: project entry point
- `概览.md`: what the project is
- `架构.md`: structure and modules
- `决策.md`: why important choices were made
- `任务.md`: what is being worked on now
- `来源.md`: registered sources
- `project.memory.md`: short runtime memory for agents

## Main Workflows

### 1. Attach a project

```powershell
python 00_system/scripts/attach_project.py --repo-root "C:\path\to\repo" --project "demo-saas"
```

This creates bootstrap files in the project repo and creates or updates the project pages in the wiki.

### 2. Ingest a source

```powershell
python 00_system/scripts/ingest_source.py --source "C:\path\to\prd.docx" --title "PRD v1" --project "demo-saas"
```

This copies the source file, creates a source note, updates the log, and rebuilds indexes.

### 3. Search

```powershell
python 00_system/scripts/search_wiki.py "permissions design" --show-relations
```

### 4. File back a conclusion

```powershell
python 00_system/scripts/file_back_query.py --title "Access model decision" --question "RBAC or ABAC?" --conclusion "Use RBAC first." --project "demo-saas"
```

## Project Workflow In Any Window

The main point of this system is that a project should keep using its project wiki from any coding window, not only from the scaffold repository.

### Attach once

Each project only needs one formal attach step:

```powershell
python 00_system/scripts/attach_project.py --repo-root "C:\path\to\repo" --project "demo-saas"
```

That creates these files in the project repo root:

- `wiki.context.json`
- `AGENTS.md`
- `CLAUDE.md`

These files are the bridge from the project repo to the private wiki.

### How any project window should start

In any future window opened on that project repo, the agent should:

1. read `wiki.context.json`
2. read `AGENTS.md` or `CLAUDE.md`
3. open the project wiki pages:
   - `索引.md`
   - `project.memory.md`
   - `任务.md`
   - and then `概览.md` / `架构.md` / `决策.md` / `来源.md` when needed

### How knowledge accumulation should work during development

The project wiki should be treated as the durable memory layer for the project.

Recommended pattern:

1. before work
   read `project.memory.md` and `任务.md`
2. during work
   ingest new documents, notes, constraints, or meeting material into project sources
3. after work
   write stable conclusions back into the project wiki

Write-back rules:

- update `概览.md` when project scope or positioning changes
- update `架构.md` when structure or modules change
- update `决策.md` when a durable decision is made
- update `任务.md` to reflect current progress
- place new external material in `来源.md` and `source-notes/`
- place temporary but reusable analysis in `notes/` or `40_outputs/`
- promote reusable patterns into `30_shared/`

### Standard instruction for a project window

Use this instruction in any attached project window:

```text
Work with the current project's wiki.

Start by reading:
1. wiki.context.json at the project repo root
2. AGENTS.md or CLAUDE.md at the project repo root
3. the project wiki's 索引.md, project.memory.md, and 任务.md

Requirements:
- complete the task
- ingest new source material when it appears
- write stable conclusions back into the project wiki
- promote reusable knowledge into the shared layer
```

### What the project wiki is for

The project wiki is not a backup folder for docs.

It is the project's durable memory layer.

It exists to:

1. restore context quickly in any new window
2. preserve decisions and architecture outside raw code
3. give sources, tasks, risks, and analyses one place to land
4. let project experience flow into shared knowledge

In short:

- the code repo holds deliverables
- the project wiki holds memory, explanation, write-back, and review

## Legacy Notes Migration

If you already have older project notes in another notebook or second-brain location, treat them as historical source material instead of copying them manually into the new system.

Recommended process:

1. treat old notes as project sources
2. ingest the highest-value notes first
3. distill stable conclusions into the current project wiki

Good migration candidates include:

- project work pages
- architecture notes and topology diagrams
- implementation summaries
- design proposals
- old task and source pages

## Public Scaffold vs Private Vault

The sync model is intentionally one-way for scaffold files.

Use:

```powershell
python 00_system/scripts/sync_private_vault.py --dry-run
python 00_system/scripts/sync_private_vault.py
```

This syncs scaffold-layer files from the public repo into `ObsidianToWiki-private`.

It does not sync your private content back.

## Document Roles

- `README.md` / `README-zh.md`
  system overview, architecture, directory structure, and operating model
- `Home.md`
  the first page to open when navigating inside the vault
- `快速开始.md`
  the shortest path to first use
- `使用手册.md`
  day-to-day operating guide
- `会话启动页.md`
  copyable prompts for agents
- `index.md`
  navigation hub, not the main explanation document

## Methodology

This project is informed by Andrej Karpathy's `llm-wiki` idea and adapted into a local Obsidian-first scaffold.

- Karpathy note: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
