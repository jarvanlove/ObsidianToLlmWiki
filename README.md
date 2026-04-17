# ObsidianToWiki

Obsidian-first LLM-maintained knowledge system for durable personal knowledge and project memory.

This is not just a note template repository and not just a set of search scripts. It is designed to continuously turn raw material, project context, stable conclusions, and reusable patterns into a maintainable local wiki.

## TL;DR

- This is a local wiki system for both personal knowledge and project memory
- It supports project attachment, source ingestion, retrieval, answer file-back, shared promotion, and ongoing governance
- Users interact through natural language while scripts, indexing, sync, and maintenance stay inside the system
- It is meant for long-term use, not for leaving knowledge trapped in chat windows or scattered folders

## Who This Is For

This system is especially useful for:

- individual users who want durable long-term knowledge
- developers who work across multiple projects and lose context between sessions
- people who want project experience to become reusable shared knowledge
- teams or individuals who want Codex, Claude Code, or other agents to keep using the same project memory

## 5-Minute Start

For a first run, do only these four things:

1. download `ObsidianToWiki`
2. prepare a private vault named `ObsidianToWiki-private`
3. initialize the private vault with scaffold files, templates, scripts, and entry pages
4. do one real usage cycle:
   - attach one project
   - ingest one source

After that, use natural language requests such as:

- "attach the current project to the wiki"
- "ingest this into the current project"
- "answer based on the current project's wiki"
- "save this conclusion into the wiki"

## Core Capability Overview

```text
Source Layer
raw files / temporary material / project sources
    ->
Memory Layer
personal knowledge / project knowledge / shared knowledge / filed-back outputs
    ->
Automation Layer
project attachment / source ingestion / retrieval / answer file-back / governance / private vault sync
    ->
Outcome
context recovery in any window / durable knowledge accumulation / reusable cross-project experience
```

You can think of it as a continuous loop:

- new material enters the system
- the agent helps structure and link it
- stable conclusions are filed back into the wiki
- reusable experience is promoted into the shared layer
- future projects keep benefiting from that knowledge

## Product Positioning

ObsidianToWiki serves two practical scopes:

1. long-term personal knowledge
2. long-term software project memory

It is built to capture and maintain:

- raw files
- temporary material
- project context
- architecture notes
- decision records
- task state
- analyses and retrospectives
- reusable prompts, tools, and patterns

In short:

the code repository holds deliverables, while the wiki holds memory, explanation, write-back, and review.

## Design Principles

The system is built around six principles.

### 1. Markdown is the source of truth

Knowledge should end up in files that humans can read, edit, diff, and maintain over time.

### 2. Intake and knowledge should be separated

Raw material should enter an intake layer first, then be distilled into durable knowledge. This prevents the wiki from becoming an unstructured dump.

### 3. Personal and project knowledge should coexist

The system supports both long-term personal knowledge and project-specific memory without flattening them into a single note pile.

### 4. Users express needs, not low-level commands

The intended user interface is natural language. Scripts, indexing, sync, and governance are implementation details.

### 5. Any coding window should recover project context

A project only needs one attach step. After that, any future coding window can recover the right project wiki context.

### 6. Knowledge should be promotable and reusable

Useful experience discovered in one project should be able to move into the shared layer and help future projects.

## Functional Modules

From a product perspective, the system consists of eight functional modules.

### 1. Project attachment

Attach an existing project to the wiki and establish a stable bridge between the code repository and its project sub-wiki.

### 2. Source ingestion

Ingest documents, PDFs, meeting notes, design files, screenshots, and other material while preserving originals and generating source notes.

### 3. Project memory maintenance

Maintain project pages for:

- overview
- architecture
- decisions
- tasks
- sources
- risks
- timeline
- runtime memory

### 4. Personal knowledge distillation

Distill long-lived personal insights, methods, workflows, and preferences into a durable personal layer.

### 5. Shared knowledge promotion

Promote cross-project reusable content into the shared layer, including patterns, prompts, architecture notes, and tool usage knowledge.

### 6. Search and answer file-back

The system not only retrieves knowledge, it can also file useful answers back into the wiki so knowledge does not remain trapped in chat sessions.

### 7. Governance and linting

The system continuously checks for issues such as:

- orphan pages
- stale pages
- duplicate topics
- undistilled sources
- structural gaps

### 8. Private vault sync

Scaffold updates can be synced into the private vault so the real working environment stays aligned with the public system.

## Architecture

The system can be understood as a three-layer architecture.

### 1. Source layer

This layer receives raw input:

- raw files
- clips
- temporary working artifacts
- project source files

Primary locations:

- `01_inbox/`
- project `sources/`
- project `source-notes/`

### 2. Memory layer

This layer contains durable structured knowledge:

- `10_personal/`
- `20_projects/`
- `30_shared/`
- `40_outputs/`

This is the actual knowledge body of the system.

### 3. Automation layer

This layer keeps the system operational:

- page creation
- source ingestion
- project attachment
- retrieval
- answer file-back
- relation sync
- source sync
- governance
- private vault sync

Primary locations:

- `00_system/scripts/`
- `00_system/templates/`
- `00_system/registry/`

## Repository Structure

```text
ObsidianToWiki/
├─ .obsidian/
├─ 00_system/
│  ├─ registry/
│  ├─ scripts/
│  └─ templates/
├─ 01_inbox/
│  ├─ clips/
│  ├─ raw/
│  └─ scratch/
├─ 10_personal/
├─ 20_projects/
│  ├─ active/
│  ├─ archive/
│  ├─ 关系索引.md
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
│  ├─ reflections/
│  └─ 索引.md
├─ 90_archive/
├─ docs/
├─ Home.md
├─ README.md
├─ README-zh.md
├─ 快速开始.md
├─ 使用手册.md
├─ 标准自然语言话术清单.md
└─ 会话启动页.md
```

## Installation And Usage

After downloading from GitHub, use the system in this order.

### 1. Prepare two repositories

You need:

- `ObsidianToWiki`
  the public scaffold with rules, templates, scripts, and documentation
- `ObsidianToWiki-private`
  the private vault with real project knowledge, personal knowledge, and raw sources

### 2. Initialize the private vault

Sync scaffold-layer content into the private vault so it has:

- entry pages
- rule pages
- prompts
- scripts
- templates
- a minimal directory structure

### 3. Do the first real usage

At first, do only two things:

1. attach one real project
2. ingest one real source

### 4. Use natural language from then on

Typical requests:

- "attach the current project to the wiki"
- "ingest this into the current project"
- "ingest this into personal knowledge"
- "answer based on the current project's wiki"
- "keep filing knowledge back while you work"
- "save this conclusion into the wiki"
- "promote this into shared knowledge"

## How Projects Use The System

This is one of the most important use cases.

### Attach once

Each project only needs one formal attach step. After that, the project repo root will contain:

- `wiki.context.json`
- `AGENTS.md`
- `CLAUDE.md`

These files form the bridge from the project repository to the project wiki.

### Work in any window

In any future coding window, the agent should read:

1. `wiki.context.json`
2. `AGENTS.md` or `CLAUDE.md`
3. the project's `索引.md`
4. the project's `project.memory.md`
5. the project's `任务.md`

### Accumulate knowledge during development

Recommended pattern:

1. read project memory before work
2. ingest new source material during work
3. file stable conclusions back after work

The main write-back targets are usually:

- `概览.md`
- `架构.md`
- `决策.md`
- `任务.md`
- `来源.md`

## Multimodal Support

Current stable support includes:

- text
- markdown
- code
- `docx`
- `pptx`
- `pdf`

Images, audio, and video should be added in stages:

1. ingest and register them as sources
2. add OCR, transcription, and keyframe extraction
3. automatically distill them into project or personal pages

## Inbox Policy

Keep the inbox role-based:

- `raw`: original files
- `clips`: source notes not yet fully distilled
- `scratch`: temporary working artifacts

## Documentation Entry Points

If you are new to the system, start here:

1. [Home.md](Home.md)
2. [快速开始.md](快速开始.md)
3. [使用手册.md](使用手册.md)
4. [标准自然语言话术清单.md](标准自然语言话术清单.md)

Document roles:

- `README.md` / `README-zh.md`
  product overview, design principles, architecture, and usage
- `Home.md`
  main entry page
- `快速开始.md`
  shortest onboarding path
- `使用手册.md`
  day-to-day usage guide
- `标准自然语言话术清单.md`
  fixed list of common user requests
- `会话启动页.md`
  copyable prompts for agents

## Methodology

This project is informed by Andrej Karpathy's [Karpathy LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) and adapted into a local Obsidian-first scaffold.
