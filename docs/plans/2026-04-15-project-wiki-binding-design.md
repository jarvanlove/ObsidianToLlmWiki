# Project Wiki Binding Design

Date: 2026-04-15

## Problem

The current wiki is useful once a session has been pointed at it, but it is not yet a fully automatic project memory layer.

Pain points:

- Each new Codex / Claude Code session still needs a reminder to use the wiki.
- Multiple project workspaces need a consistent way to bind to the same wiki.
- Project outputs should flow back into the wiki without manual re-instruction every time.

## Goals

- Make the wiki discoverable from a project workspace with minimal prompting.
- Keep project knowledge first-class.
- Preserve cross-project reuse.
- Keep multi-window / multi-agent collaboration safe and predictable.

## Recommendation

Use a 3-layer binding model:

1. Workspace bootstrap
2. Central wiki registry
3. Output routing rules

### 1) Workspace Bootstrap

Every project workspace should contain a tiny bootstrap file for agents:

- `AGENTS.md`
- `CLAUDE.md`

Those files should point to:

- the central wiki root
- the current project slug
- the project wiki entry page
- the project output location

This is what removes the need to repeat the wiki reminder in every task.

### 2) Central Wiki Registry

The wiki keeps the canonical project memory:

- `20_projects/active/<project>/索引.md`
- `20_projects/active/<project>/概览.md`
- `20_projects/active/<project>/架构.md`
- `20_projects/active/<project>/决策.md`
- `20_projects/active/<project>/任务.md`
- `20_projects/active/<project>/来源.md`

The registry is the source of truth for the project’s accumulated knowledge.

### 3) Output Routing Rules

Project work should be routed as follows:

- project-specific deliverables stay in the project workspace / repo
- summaries, decisions, and reusable context are written back to the project wiki
- reusable cross-project knowledge is promoted to `30_shared`
- analysis/briefing artifacts that deserve persistence go to `40_outputs`

## Operating Model

### At task start

The agent should automatically:

1. read the workspace bootstrap
2. open the wiki entry points
3. open the current project `索引.md`
4. decide whether the task is project-local, reusable, or cross-project

### During work

The agent should keep the project wiki updated as decisions are made.

### On completion

The agent should:

1. write the final project artifact
2. file a summary into the wiki if it is durable
3. add backlinks
4. append `log.md`
5. rebuild indexes

## Collaboration Rule

When multiple windows are open:

- one window is the writer for a given project page
- other windows are readers or contributors
- do not let two windows freely rewrite the same page at the same time

## Future Enhancement

If stronger automation is needed later, add:

- a workspace manifest
- a project registry file
- optional file-watcher automation
- optional MCP/search integration

For now, the bootstrap + registry model is the best balance of reliability and simplicity.
