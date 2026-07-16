This project is informed by Andrej Karpathy's [Karpathy LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) and adapted into a local Obsidian-first scaffold.

# ObsidianToWiki

Obsidian-first LLM-maintained knowledge system for durable personal knowledge and project memory.

This is not just a note template repository and not just a set of search scripts. It is designed to continuously turn raw material, project context, stable conclusions, and reusable patterns into a maintainable local wiki.

## TL;DR

- This is a local wiki system for both personal knowledge and project memory
- It supports project attachment, source ingestion, retrieval, answer file-back, shared promotion, and ongoing governance
- Users interact through natural language while scripts, indexing, sync, and maintenance stay inside the system
- For daily project work, remember only three cockpit phrases first: "start work", "continue", and "close work"
- It is meant for long-term use, not for leaving knowledge trapped in chat windows or scattered folders

## Is This Project Now A Skill?

Not by itself. The complete product has four cooperating parts:

1. this public repository provides the runtime, scaffold, validation, retrieval, ingestion, and upgrade tools
2. your private vault stores personal knowledge and durable project memory
3. the global `obsidiantowiki-manager` Skill translates natural-language requests into the correct operations
4. each attached project keeps a small local bridge so the agent can find the right private project memory

Install the Manager Skill once for each AI tool environment that should operate the wiki. Attach each project once. A normal ObsidianToWiki upgrade does not require rebuilding the private vault or attaching existing projects again. Project hooks and subagents are optional adapters, not a prerequisite for daily use.

Daily use remains natural language. In an attached project, say "start work", "continue", or "close work"; for knowledge work, ask the agent to ingest, find, compare, or write back material. The agent is responsible for invoking scripts and strict checks internally.

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

On first attach, the system now tries to find your private wiki automatically through project bridge files, user-level config, and standard vault naming conventions. If you need to confirm it once, later attaches reuse that result.

After that, use natural language requests such as:

- "start work"
- "continue"
- "close work"
- "attach the current project to the wiki"
- "ingest this into the current project"
- "distill this conclusion into personal knowledge"
- "answer based on the current project's wiki"
- "save this conclusion into the wiki"

## How To Use It Every Day

For project development, daily use starts with three cockpit phrases.

### 1. Start Work

Say: "start work".

The agent should attach the project if needed, run a strict attach check, or restore context if the project is already attached.

### 2. Continue

Say: "continue".

The agent should inspect project state, tasks, current diff, and wiki binding before choosing the next action.

### 3. Close Work

Say: "close work".

The agent should inspect the diff and verification, update relevant control files, and file back only durable conclusions.

### 4. While You Work

- When new material appears, say: "ingest this into the current project"
- When a conclusion is worth keeping, say: "save this conclusion into the wiki"
- If it is a long-term personal method, preference, or lesson, say: "distill this conclusion into personal knowledge"
- If it is reusable across projects, say: "promote this into shared knowledge"

### 5. When Organizing Personal Knowledge

- You can also work directly inside the private wiki
- Common requests are: "ingest this into personal knowledge"
- Or: "find what I already know about this topic"
- Or: "distill this conclusion into personal knowledge"

In short:

- project-specific material goes to the project layer
- long-lived personal knowledge goes to the personal layer
- reusable cross-project experience goes to the shared layer
- one-off analyses go to the outputs layer

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

Common file types that can be brought into the system include:

- text and code: `md`, `markdown`, `txt`, `py`, `js`, `ts`, `json`, `yaml`, `yml`, `html`, `css`, `java`, `go`, `rs`, `sql`
- document formats: `docx`, `pptx`, `pdf`
- image formats: `png`, `jpg`, `jpeg`, `webp`, `bmp`, `gif`, `tif`, `tiff`
- audio formats: `mp3`, `wav`, `m4a`, `aac`, `flac`, `ogg`, `opus`
- video formats: `mp4`, `mov`, `avi`, `mkv`, `webm`, `wmv`, `m4v`

Notes:

- text, `docx`, `pptx`, and `pdf` support direct extraction with pass/review/blocked quality gates
- blocked extraction preserves the original and source note but creates no weak derivatives; scanned PDFs are marked `needs_ocr`
- long documents create a document map before section notes, preserve page/slide/heading refs, and never auto-promote formal knowledge pages
- images, audio, and video can already be formally ingested and registered as media sources
- their semantic understanding should, by default, be delegated to the user's own multimodal LLM / API

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

Personal pages now begin to support a minimal relationship model:

- `related_to`
- `builds_on`

In the first stage, these fields are used only to express "topically related" and "built on prior knowledge" links without introducing a heavier graph layer.

### 5. Shared knowledge promotion

Promote cross-project reusable content into the shared layer, including patterns, prompts, architecture notes, and tool usage knowledge.

### 6. Search and answer file-back

The system not only retrieves knowledge, it can also file useful answers back into the wiki so knowledge does not remain trapped in chat sessions.

Retrieval now incrementally projects Markdown into a local SQLite FTS5 cache. Searches check created, changed, and deleted pages by default and can return human-readable text, stable JSON, or a bounded context pack with paths, headings, and `source_refs`. The cache is disposable and never replaces Markdown as source of truth.

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

For first-time setup, run `install.ps1` on Windows or `install.sh` on macOS/Linux. The installer creates a repository-local `.venv`, installs core dependencies, safely installs or upgrades the global manager Skill, and runs `doctor`. Users still operate through natural language afterward.

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

The current version can persist the first successfully discovered private wiki root into a user-level config so later project attaches can reuse it.

### 3. Do the first real usage

At first, do only two things:

1. attach one real project
2. ingest one real source

### 4. Use natural language from then on

Typical requests:

- "start work"
- "continue"
- "close work"
- "attach the current project to the wiki"
- "ingest this into the current project"
- "ingest this into personal knowledge"
- "answer based on the current project's wiki"
- "keep filing knowledge back while you work"
- "save this conclusion into the wiki"
- "promote this into shared knowledge"

### Existing User Upgrade

Existing users do not need to rebuild their private vault or detach projects.

Recommended order:

1. Pull the latest public scaffold.
2. Run the installer to update dependencies and the global manager Skill.
3. Dry-run, then apply manifest-managed private-vault sync.
4. Ask the agent to run one hash-safe upgrade and strict doctor. Existing projects do not need to be reattached.

Windows:

```powershell
cd <obsidiantowiki-public-root>
git pull origin main
./install.ps1
python .\00_system\scripts\sync_private_vault.py --private-root <private-wiki-root> --dry-run --format json
python .\00_system\scripts\sync_private_vault.py --private-root <private-wiki-root>
python .\00_system\scripts\otw.py upgrade --wiki-root <private-wiki-root> --apply --all-projects
python .\00_system\scripts\otw.py doctor --wiki-root <private-wiki-root> --strict
```

macOS / Linux:

```bash
cd <obsidiantowiki-public-root>
git pull origin main
./install.sh
./00_system/scripts/sync_private_vault.sh --private-root <private-wiki-root> --dry-run --format json
./00_system/scripts/sync_private_vault.sh --private-root <private-wiki-root>
./00_system/scripts/otw.sh upgrade --wiki-root <private-wiki-root> --apply --all-projects
./00_system/scripts/otw.sh doctor --wiki-root <private-wiki-root> --strict
```

The sync tool only updates manifest-managed scaffold files. Root indexes, logs, the project registry, personal/project/shared knowledge, outputs, and retrieval caches are protected; only `30_shared/prompts` is scaffold-managed inside the shared layer. Use `--dry-run --format json` before an upgrade and `--path <wiki-relative-path>` for a precise repair.

Do not mix project binding paths across operating systems. A project attached on Windows records `C:\...` paths in `wiki.context.json`; macOS / Linux should record paths that are reachable from that environment, such as `/Users/...`. Refresh the project attach once after moving across operating systems.

The commands are the executable path for agents and advanced users. Daily project work should still start with "start work", "continue", and "close work".

## How Projects Use The System

This is one of the most important use cases.

### Attach once

Each project only needs one formal attach step. After that, the project repo root will contain:

- AI tool entrypoints
- a local project control plane
- the matching project wiki area

Together, these form the bridge from the project repository to the project wiki and the local execution control plane.

Tool entrypoints are peers, not parent/child files. Shared project facts should live in the project control plane and project wiki, not only in one tool-specific entry file.

If the project already has entrypoint or control files, the attach script preserves existing content and only updates its managed block. Re-running attach is safe.

When attaching a completely new project for the first time, the system tries this order:

1. existing wiki binding information in the project
2. user-level wiki defaults in the local environment
3. a sibling `ObsidianToWiki-private` next to the scaffold

Only if all of those fail does the user need to specify the private wiki location explicitly.

### Work in any window

In any future coding window, just say:

```text
work according to the current project rules
```

The agent should automatically restore project context, read the required rules, locate the project wiki, and continue from the current task.

### Accumulate knowledge during development

Recommended pattern:

1. read project memory before work
2. ingest new source material during work
3. file stable conclusions back after work
4. if the outcome is a durable method, habit, preference, or workflow, say "distill this conclusion into personal knowledge" directly in the project window

The main write-back targets are usually:

- `概览.md`
- `架构.md`
- `决策.md`
- `任务.md`
- `来源.md`

If you explicitly route a conclusion to the personal layer, the system should write it into `10_personal/` while keeping a backlink to the originating project instead of forcing everything back into the project layer.

### Skill and MCP configuration

- The global manager Skill is installed once per agent configuration root and safely upgraded by the installer. It maps natural language to the unified `otw.py` runtime.
- Project retrieval Skills and hook/subagent helpers remain opt-in. Only `--install-ai-adapters` places them under `.agents/skills/`, `.claude/skills/`, and `scripts/ai/`; normal upgrades do not force-enable them.
- MCP belongs to the AI tool capability layer. Configure it once per Codex, Claude Code, Cursor, or compatible tool when the tool launches it from the active project.
- Without MCP or project adapters, the global manager Skill uses the public runtime directly.
- MCP exposes only read-only `search_wiki` and `get_wiki_context` tools.

See `docs/agent-retrieval.md` for the boundary and setup details.

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
2. connect the user's own multimodal LLM / API parsing
3. automatically distill them into project or personal pages

P0 first pass is now in place:

- images, audio, and video can be formally ingested
- source notes record `media_type` and `parse_status`
- governance can surface media sources that are still waiting for processing

Current directory conventions:

- personal images: `01_inbox/raw/personal/images/`
- personal audio: `01_inbox/raw/personal/audio/`
- personal video: `01_inbox/raw/personal/video/`
- OCR scratch: `01_inbox/scratch/ocr/`
- transcript scratch: `01_inbox/scratch/transcripts/`
- keyframe scratch: `01_inbox/scratch/keyframes/`
- summary scratch: `01_inbox/scratch/summaries/`

The recommended multimodal direction is now:

- use the user's own multimodal LLM / API for image, audio, and video understanding
- keep the wiki system responsible for intake, source registration, file-back, indexing, and governance
- do not require users to install local OCR / ASR / video-processing tools
- do not require extra provider / adapter configuration files for multimodal use

Multimodal use now keeps only one recommended route:

### In-session parsing, the default and only recommended path

Use this when:

- you are already inside Codex or Claude Code
- or tools such as Cursor, Trae, QClaw, WorkBuddy, Hermes Agent, or OpenClaw that already integrate third-party model access
- you give the current AI a file path
- you want the AI to understand the file and file the result back into the wiki

Characteristics:

- no extra API key setup
- no `~/.obsidiantowiki-multimodal.json`
- best fit for day-to-day usage
- directly reuses the multimodal ability that your current tool has already integrated

Related design plans for the current evolution:

- [2026-04-17-multimodal-support-plan.md](docs/plans/2026-04-17-multimodal-support-plan.md)
- [2026-04-22-user-wiki-discovery-design.md](docs/plans/2026-04-22-user-wiki-discovery-design.md)
- [2026-04-22-personal-knowledge-routing-design.md](docs/plans/2026-04-22-personal-knowledge-routing-design.md)

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

## Core Scripts

If you want to understand which scripts matter most, start with these.

### Attachment

- `attach_project.py`
  attaches a project to the wiki, writes safe bridge blocks, creates missing project control files, and creates the project memory area. Optional hook/subagent adapters are installed only with `--install-ai-adapters`

- `project_session.py`
  generates AI coding lifecycle `check/start/close` checklists and control-file update candidates. By default it only reports suggestions and does not write project files or sync the private wiki

### Ingestion

- `ingest_source.py`
  ingests material, stores the original file, and creates a source note

### Retrieval and file-back

- `search_wiki.py`
  refreshes the local retrieval cache, preserves page weighting and relation summaries, and returns text, JSON, or bounded context packs
- `build_retrieval_index.py`
  incrementally builds or fully refreshes the disposable SQLite FTS5 retrieval cache
- `evaluate_retrieval.py`
  gates path, heading, provenance, pass rate, MRR, and separate synonym probes
- `mcp_retrieval_server.py`
  exposes structured search and bounded context as read-only MCP stdio tools
- `migrate_provenance.py`
  audits legacy knowledge pages and migrates only explicit source links and page references
- `file_back_query.py`
  files an answer or analysis back into the wiki
- `handle_nl_request.py`
  natural-language request router

### Sync

- `sync_source_notes.py`
  backfills source status and derived-page links
- `sync_project_relations.py`
  syncs project relations
- `sync_personal_relations.py`
  syncs personal-page relation fields
- `sync_private_vault.py`
  syncs only manifest-managed public scaffold files and protects private runtime state

### Governance

- `lint_wiki.py`
  runs governance and health checks
- `schema_lib.py`
  validates page schema
- `wiki_lib.py`
  shared low-level utilities

### Learning and promotion

- `record_learning_candidate.py`
  records learning candidates
- `discover_learning_candidates.py`
  discovers candidates automatically
- `curate_learning_candidates.py`
  archives low-score stale learning candidates
- `review_learning_candidates.py`
  batch-approves, archives, or reopens learning candidates
- `promote_learning_candidate.py`
  promotes a candidate into a formal asset
- `recommend_source_promotions.py`
  recommends promotion targets for source notes

Learning candidates now begin to carry:

- `candidate_risk_level`
- `candidate_upgrade_mode`
- `candidate_repeat_count`
- `candidate_freshness`
- `candidate_domain`

This means the system is moving from simple candidate discovery toward controlled handling of:

- low-risk candidates that can be treated semi-automatically
- high-risk candidates that still require human review

This stage also adds:

- `40_outputs/学习候选审批视图.md`
- explicit approval before promoting high-risk or manual-review candidates

### Indexes and status

- `rebuild_indexes.py`
  rebuilds indexes
- `log_event.py`
  writes logs
- `version_status.py`
  reports version state
- `version_closure_report.py`
  generates a closure report

If you only remember six scripts, remember these:

- `attach_project.py`
- `project_session.py`
- `ingest_source.py`
- `handle_nl_request.py`
- `search_wiki.py`
- `file_back_query.py`

## Personal Knowledge Graph P0

The personal knowledge layer now supports a minimal first-step relationship model:

- `related_to`
- `builds_on`

Use them like this:

- `related_to`
  marks pages that are topically related and should be read together
- `builds_on`
  marks pages that build on prior concepts, methods, or knowledge pages

At this stage, the system only does:

- template support
- schema validation
- personal relation index generation
- personal relation summaries in retrieval results

At this stage, it does not yet do:

- automatic relation extraction
- deeper semantic relation inference

The first P2 pass now follows a conservative automation path:

- infer relations from explicit personal-page links
- use shared tags and shared source projects as low-risk supplements
- avoid heavier semantic graph inference for now

It is now concretely wired into:

- `10_personal/关系索引.md`
- personal relation summaries in retrieval results
- the `sync_personal_relations.py` sync script

## Retrieval Scaling P1

The current stage still stays on lightweight retrieval instead of heavier infrastructure.

What is already added:

- page-type weighting
- stronger downranking for stale output pages, reflection candidates, and source pages
- relation summaries for personal and shared pages
- failure logging for zero-result queries
- disposable local SQLite FTS5 derived index
- incremental freshness checks for created, changed, and deleted Markdown pages
- stable JSON result contract
- best matching heading and bounded snippet localization
- bounded context packs for agents
- query-coverage ranking and Chinese short-term chunk localization
- inspectable local topic-alias hybrid recall
- fixed retrieval gates with MRR and semantic probes
- project Agent Skills and optional read-only MCP stdio tools
- `source_notes` / `source_refs` output plus conservative legacy migration

What this stage still does not do:

- vector retrieval
- semantic reranking
- background file watching

The current fixed evaluation reports a `1.0` gate pass rate, `1.00` MRR, and `1.0` semantic-probe pass rate, so embeddings and vector infrastructure are not justified yet.
