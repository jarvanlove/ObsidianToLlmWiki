# CLAUDE.md

This workspace is attached to an ObsidianToWiki project memory.

Read `wiki.context.json` first if it exists. Use the paths below as the human-readable bridge into the wiki.

- wiki_root: `C:\Work\note\ObsidianToWiki-private`
- project_repo_root: `C:\Work\note\ObsidianToWiki`
- project_slug: `obsidiantowiki`
- project_index: `20_projects/active/obsidiantowiki/索引.md`
- project_overview: `20_projects/active/obsidiantowiki/概览.md`
- project_architecture: `20_projects/active/obsidiantowiki/架构.md`
- project_decisions: `20_projects/active/obsidiantowiki/决策.md`
- project_tasks: `20_projects/active/obsidiantowiki/任务.md`
- project_sources: `20_projects/active/obsidiantowiki/来源.md`
- project_relations: `20_projects/active/obsidiantowiki/关系.md`
- project_risks: `20_projects/active/obsidiantowiki/风险.md`
- project_timeline: `20_projects/active/obsidiantowiki/时间线.md`
- project_memory: `20_projects/active/obsidiantowiki/project.memory.md`

## Working Rules

- Treat the wiki as the durable project memory layer.
- Read the project index and core pages before making durable changes.
- Write reusable conclusions back into the wiki.
- Reuse shared patterns when similar problems have already been solved elsewhere.
- This is the Claude Code / compatible tools entrypoint.
- Daily project workflow should use `开始工作`, `继续`, and `收工`; file reading, strict checks, and file-back are agent responsibilities.
- For local implementation tasks, read project control files directly: `PRODUCT_SPEC.md`, `ARCHITECTURE.md`, `TASKS.md`, `TESTING.md`, `DEPLOYMENT.md`, `OPERATIONS.md`, and `SECURITY.md`.
- Keep public scaffold changes in this repository and durable project memory in the private wiki project pages.
- When changing project attach/bootstrap behavior, update `docs/templates/project-AGENTS.md` and `docs/templates/project-CLAUDE.md` if the protocol changes.
