# ObsidianToWiki

LLM-maintained personal and project wiki scaffold for Obsidian.

中文说明见 [README-zh.md](README-zh.md)。

## What It Is

ObsidianToWiki is a repository structure for turning raw sources into a persistent markdown wiki maintained by an LLM agent.

It is designed around three layers:

- raw sources
- structured wiki pages
- agent rules and automation

It supports two complementary use cases:

- personal knowledge that compounds over time
- project-level memory for active software work

## Repository Layout

```text
ObsidianToWiki/
├─ .obsidian/
├─ 00_system/
│  ├─ scripts/
│  └─ templates/
├─ 01_inbox/
│  ├─ raw/
│  ├─ clips/
│  └─ scratch/
├─ 10_personal/
│  ├─ areas/
│  ├─ concepts/
│  ├─ entities/
│  ├─ syntheses/
│  └─ 索引.md
├─ 20_projects/
│  ├─ active/
│  │  └─ <project>/
│  │     ├─ notes/
│  │     ├─ source-notes/
│  │     ├─ sources/
│  │     ├─ 概览.md
│  │     ├─ 架构.md
│  │     ├─ 决策.md
│  │     ├─ 经验.md
│  │     ├─ 来源.md
│  │     ├─ 任务.md
│  │     └─ 索引.md
│  ├─ archive/
│  │  └─ <project>/
│  │     └─ ...
│  └─ 索引.md
├─ 30_shared/
│  ├─ architectures/
│  ├─ patterns/
│  ├─ prompts/
│  ├─ tools/
│  └─ 索引.md
├─ 40_outputs/
│  ├─ analyses/
│  ├─ briefings/
│  └─ 索引.md
├─ 90_archive/
├─ AGENTS.md
├─ CLAUDE.md
├─ Home.md
├─ index.md
├─ log.md
├─ README.md
├─ README-zh.md
├─ 会话启动页.md
└─ 使用手册.md
```

## Directory Roles

- `00_system/scripts/`: Python core logic plus `.ps1` and `.sh` wrappers
- `00_system/templates/`: page templates used by the automation scripts
- `01_inbox/raw/`: immutable raw source files
- `01_inbox/clips/`: source notes that belong to the inbox layer
- `01_inbox/scratch/`: temporary working material
- `10_personal/areas/`: long-lived personal domains
- `10_personal/concepts/`: concepts and abstractions
- `10_personal/entities/`: people, tools, systems, and named things
- `10_personal/syntheses/`: higher-level summaries and stitched views
- `20_projects/active/`: active project sub-wikis
- `20_projects/archive/`: archived project sub-wikis
- `30_shared/architectures/`: reusable architecture notes
- `30_shared/patterns/`: reusable patterns
- `30_shared/prompts/`: reusable agent prompts
- `30_shared/tools/`: reusable tool notes
- `40_outputs/analyses/`: analytical outputs that should be filed back
- `40_outputs/briefings/`: concise briefings and summaries
- `90_archive/`: low-frequency retained material

## Design Choice: English Paths, Chinese Reading

The repository uses English directory and script names for open-source readability and cross-team collaboration.

Daily Obsidian use does not need to become English-first:

- page titles can stay Chinese
- body content can stay Chinese
- Obsidian link labels can stay Chinese
- only filesystem paths and script filenames are standardized in English

That keeps GitHub cleaner without making the vault harder to read.

## Agent Entry Points

- `AGENTS.md` for Codex
- `CLAUDE.md` for Claude Code

Both files should stay aligned.

## Automation

Python scripts in `00_system/scripts/` are the cross-platform core.

- `.ps1` wrappers are for Windows
- `.sh` wrappers are for macOS/Linux

Common capabilities include:

- source ingest
- page creation
- search
- index rebuild
- wiki lint

## Obsidian Behavior

This repository is meant to be opened directly as an Obsidian vault.

The structure assumes:

- Obsidian wikilinks are the default internal reference format
- top-level docs and section indexes form the navigation spine
- project pages and shared pages should cross-link when relationships matter

## Project Linking

For each new project, the minimal useful loop is:

- `索引.md` as the project entry point
- `概览.md` as the top-level summary
- `架构.md` as the system structure page
- `决策.md` for important decisions
- `任务.md` for current work tracking
- `来源.md` for raw source registration

Recommended backlinks:

- `索引.md` should link to `概览`, `架构`, `决策`, `任务`, and `来源`
- `概览.md` should link to `架构`, `决策`, `任务`, and `来源`
- `架构.md` should link to `概览`, `决策`, and `来源`
- `决策.md` should link to `概览`, `架构`, and `来源`
- `任务.md` should link to `概览`, `决策`, and `来源`
- `来源.md` should link back to `索引`, and optionally to `概览` or `架构`

The goal is not maximal linking. The goal is that any page can lead back to the project spine without becoming isolated.

## Agent Bootstrapping

The wiki is not meant to depend on a manual reminder in every session.

The practical pattern is:

- each project workspace carries a tiny `AGENTS.md` / `CLAUDE.md` bootstrap
- that bootstrap points to the central wiki root and current project page
- the bootstrap must live in the project repository root and must name the private vault path explicitly
- the agent reads that bootstrap at task start
- the agent then opens the relevant project wiki pages automatically

This keeps the wiki discoverable without requiring the human to restate the same instruction repeatedly.

## Private Content Boundary

This public repository is only the scaffold.

It should not contain your private personal knowledge or private project knowledge.

Recommended setup:

- keep this repository public as the framework
- keep the actual personal/project wiki in a separate private vault or private repository
- copy the bootstrap templates into each private project workspace
- let the private vault point back to this scaffold for conventions and prompts

Framework changes happen here; private content stays in the private vault.

This is the cleanest way to open-source the system without open-sourcing the content.

See also: [docs/private-vault-setup.md](docs/private-vault-setup.md)

## Supported Ingest Formats

Direct text extraction is currently supported for:

- `md`
- `txt`
- common plain-text code/config files
- `docx`
- `pptx`
- `pdf`

Extraction quality may still be limited for scanned PDFs or binary-heavy formats.

## Start Here

- `Home.md`
- `README-zh.md`
- `使用手册.md`
- `会话启动页.md`

## Open-Source Hygiene

This repository should stay a reusable scaffold.

Do not commit:

- personal raw sources
- private notes
- local cache databases
- machine-specific absolute paths
- generated operational logs from personal use

See also:

- `CONTRIBUTING.md`
- `CHANGELOG.md`
- `SECURITY.md`

## License

MIT. See `LICENSE`.
