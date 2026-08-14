# ObsidianToWiki

Help AI understand a project before changing code and leave verifiable memory after the work, instead of delivering code that nobody can safely maintain.

ObsidianToWiki is a local-first AI project-memory and engineering-control system. It connects a private Obsidian wiki, project control files, Git facts, and an AI coding lifecycle so knowledge survives beyond a chat session and every AI change has a scope, evidence, and responsibility boundary.

This project is informed by Andrej Karpathy's [Karpathy LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): preserve raw sources, maintain durable knowledge through Markdown, indexes, and traceable links, and let an LLM continuously organize, retrieve, and update it. ObsidianToWiki extends that idea with project attachment, engineering gates, risk levels, context receipts, memory compilation, and safe updates.

Attach once. Before a change, the system looks for the root cause and impact scope; after verification, it records traceable conclusions automatically. Users can describe normal work directly, while `start work` remains an optional inspection and recovery command.

[中文](README.md) | [English](README-EN.md)

## What It Solves

AI-assisted development commonly fails in three ways:

- Every conversation starts from scratch, so decisions, risks, and constraints disappear.
- AI optimizes for "it runs," while developers cannot explain what changed, why it changed, or whether it crossed a boundary.
- Documentation grows until people stop reading it and models cannot safely load it all at once.

ObsidianToWiki changes the workflow:

```text
The user describes a request in natural language
        ↓
AI reads current code, project controls, and bounded wiki context
        ↓
Risk determines scope, planning, approval, and verification requirements
        ↓
Implementation is proven with tests, Git diff, screenshots, or runtime evidence
        ↓
Only reusable and traceable conclusions are filed back to the private wiki
```

Git remains the authority for code. The private wiki provides durable memory. AI reasoning never becomes a project fact merely because a model said it.

## What Users Need To Do

Install once, attach each project once, and then speak normally:

```text
Fix the login timeout problem.
Continue.
What is the current project status?
Close work.
```

The agent handles file reading, context checks, task planning, verification, receipts, and wiki file-back. `start work`, `continue`, and `close work` are optional inspection and recovery commands, not a daily ritual.

`What is the current project status?` returns a direct text summary. It does not generate an HTML dashboard or another project database.

## Current Capabilities

### 1. Private Wiki and Durable Project Memory

- Create and maintain a private local Obsidian vault.
- Attach code projects through `wiki.context.json`, `AGENTS.md`, and `CLAUDE.md`.
- Maintain project overview, architecture, decisions, tasks, sources, risks, timeline, and long-term memory.
- Separate personal knowledge, project knowledge, shared methods, and outputs.

### 2. Source Ingestion, Retrieval, and File-Back

- Ingest Markdown, text, code, PDF, DOCX, PPTX, and other supported sources.
- Split long documents into source notes, document maps, and traceable chapter notes.
- Search through a local SQLite FTS5 index; the index is a rebuildable cache, not the source of truth.
- File useful answers back into the wiki so conclusions do not remain trapped in chat history.

### 3. Human-Controlled AI Engineering

- Run tasks through start, plan, implement, verify, close, and memory file-back stages.
- Prefer current code and runtime evidence over project documents, trusted memory over model guesses, and never treat guesses as facts.
- Classify risk from P3 to P0; higher risk requires stronger human confirmation and independent evidence.
- Use Context Receipts to record what a task actually read, what was missing, and what was untrusted.
- Compile only evidenced, stable conclusions into long-term memory; stale history leaves the default context without being deleted.
- Use human-understanding gates and capability-recovery opportunities so developers regain knowledge of code, impact, and risk instead of delegating judgment to AI.

### 4. UI Design Governance

- Classify UI impact from U0 to U3.
- Provide 19 traceable color directions, with 6 reliable defaults for work without a reference design.
- When users dislike a result, diagnose whether the issue is local or directional and offer three understandable alternatives.
- Require approved direction, browser screenshots, Visual QA, and accessibility evidence for material UI changes.
- Treat Figma, Stitch, and UI Skills as executors, not as authorities that can override approved project design facts.

### 5. Safe Installation and Updates

- Version the public runtime, private wiki, global Skill, and project bridge separately.
- Update the public repository only through a clean, fast-forward workflow without automatic stash, reset, or force overwrite.
- Preserve modified private files and generate candidates and backups for human review.
- Let `wiki.private.json` exclude paths that ObsidianToWiki must not index or ingest.
- Use the same core workflow on Windows, macOS, and Linux.

## Major Iterations

| Period | Iteration | Result |
|---|---|---|
| 2026-04 | LLM-Wiki foundation | Established the Markdown, source, index, log, and LLM-maintenance loop |
| 2026-05 to 06 | Project attachment and lifecycle | Added project controls, private-wiki memory, and start/verify/close workflows |
| 2026-06 | Structured source ingestion | Replaced thin long-document summaries with traceable chapters and sources |
| 2026-07 | Local retrieval and safe upgrades | Added FTS5 retrieval, quality evaluation, compatibility migration, and safe one-command updates |
| 2026-07 | UI design governance | Added U0-U3 classification, 19 color directions, 6 defaults, and visual acceptance rules |
| 2026-08 | Human-Controlled AI Engineering 2.0 | Added fact priority, context receipts, risk gates, memory compilation, human understanding, and capability recovery |
| 2026-08 | Simpler interaction | Removed the low-value local HTML dashboard and kept direct natural-language project status |

## Installation

### Windows

```powershell
git clone https://github.com/jarvanlove/ObsidianToLlmWiki.git
cd ObsidianToWiki
.\install.ps1
```

### macOS / Linux

```bash
git clone https://github.com/jarvanlove/ObsidianToLlmWiki.git
cd ObsidianToWiki
./install.sh
```

The installer creates an isolated Python environment, initializes or discovers the private wiki, installs the Manager Skill, migrates state, and runs checks. The private wiki remains local by default and is not uploaded to the public repository.

## Attach a Project to the Wiki

Inside the project, tell the AI:

```text
Attach the current project to my private wiki.
```

The system creates a project entrypoint and local context. Real local paths are written only to Git-ignored configuration; committed templates must not contain absolute paths from a user's machine.

After attachment, continue describing real work. The AI should read the project's `AGENTS.md` and relevant control files before deciding scope, risk, and verification.

## Where Data Lives

```text
Public ObsidianToWiki repository
├─ Reusable scripts, templates, protocols, and shared methods
└─ No real user project knowledge

User's private wiki
├─ Personal knowledge
├─ Durable project memory
├─ Reviewed shared methods
└─ Outputs and upgrade candidates

Attached code project
├─ Git-managed code and project control files
└─ .obsidiantowiki/ local task state and receipts (ignored by default)
```

`.obsidiantowiki/` is local execution state, not a knowledge base or a page for users to browse. It may contain machine-specific paths, so Git must ignore it by default. Durable conclusions belong in the private wiki; code facts belong in Git.

## Boundaries

- This is a local tool and engineering method, not a hosted knowledge platform.
- It does not replace developer understanding or guarantee that AI-generated code is correct.
- If wiki evidence is missing or damaged, the system must degrade explicitly or stop instead of filling gaps with model hallucinations.
- `wiki.private.json` limits ObsidianToWiki itself; AI tools with broader filesystem access still need workspace and permission restrictions in those tools.
- High-risk work requires a named human to confirm impact and remaining risk; AI cannot approve its own work.

## Documentation

- [Quick Start](快速开始.md)
- [User Manual](使用手册.md)
- [Product Specification](PRODUCT_SPEC.md)
- [Architecture](ARCHITECTURE.md)
- [Tasks](TASKS.md)
- [Testing](TESTING.md)
- [Security](SECURITY.md)
- [Deployment and Updates](DEPLOYMENT.md)
- [Operations](OPERATIONS.md)
- [Changelog](CHANGELOG.md)

## License

[MIT](LICENSE)
