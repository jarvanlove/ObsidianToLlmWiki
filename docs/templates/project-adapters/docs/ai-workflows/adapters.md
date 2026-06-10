# AI Adapter Layer

This project has optional ObsidianToWiki AI adapters installed.

Adapters are execution helpers, not a second source of truth.

The primary daily interface remains the project cockpit:

```text
开始工作
继续
收工
```

Hooks and subagents should support those moments; they should not become a separate workflow the user has to remember.

## Rules

- Project control files remain the local source of truth.
- Wiki pages are only for durable conclusions.
- Adapters call the ObsidianToWiki lifecycle protocol instead of defining their own workflow.
- Adapters generate checklists and candidates by default; they do not directly rewrite project documents.
- Adapters stay low-noise: remind, check, and propose candidates only when the lifecycle moment requires it.
- Hooks and subagents should be enabled only after the manual lifecycle works for this project.

## Required Environment

Set this environment variable to the public ObsidianToWiki scaffold root:

```powershell
$env:OBSIDIANTOWIKI_SCAFFOLD_ROOT = "C:\Work\note\ObsidianToWiki"
```

Do not store private wiki paths in adapter scripts.

## Commands

```powershell
.\scripts\ai\task-check.ps1
.\scripts\ai\task-start.ps1 -Task "Describe the task"
.\scripts\ai\task-close.ps1 -Verification "exact commands and results"
.\scripts\ai\task-close.ps1 -Verification "exact commands and results" -Output "docs\ai-workflows\last-close.md"
```

## Hook Integration

If your AI tool supports lifecycle hooks:

- pre-task hook: call `scripts/ai/task-start.ps1`
- post-task or stop hook: call `scripts/ai/task-close.ps1`

Keep hooks advisory until the output is stable. Do not configure hooks to auto-commit or auto-write wiki pages.

## Subagent Integration

Use the subagent prompt templates in `docs/ai-workflows/subagents/`.

Subagents may produce:

- task-close candidates
- architecture update candidates
- wiki file-back candidates

Subagents must not become the only source of truth and must not bypass project control files.
