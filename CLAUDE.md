

<!-- OBSIDIANTOWIKI:PROJECT_CONTROL_START -->

# CLAUDE.md

This workspace is attached to an ObsidianToWiki project memory.
This file is the Claude Code / compatible-tools entrypoint for this project.

Read `wiki.context.json` first if it exists. Use the paths below as the human-readable bridge into the wiki.

- wiki_root: `<read-from-wiki.context.json>`
- runtime_root: `<read-from-wiki.context.json>`
- project_repo_root: `<current-project-root>`
- project_slug: `obsidiantowiki`
- project_scaffold_version: `<read-from-wiki.context.json>`
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
- Execute ObsidianToWiki through the public runtime_root from local context; private copied scripts are compatibility assets.
- Read the project index and core pages before making durable changes.
- Write reusable conclusions back into the wiki.
- Reuse shared patterns when similar problems have already been solved elsewhere.
- Do not treat `AGENTS.md` as this tool's parent instruction file.
- Daily user-facing project commands are `开始工作`, `继续`, and `收工`; file reading, strict checks, and file-back are agent responsibilities.
- Classify every ordinary request before acting: `read_only` creates no task; `code_change`, `external_mutation`, and `destructive` must enter the public runtime governance route before edits or external actions.
- Keep ambient P3/P2 governance to one status line. Interrupt only for an unknown root cause, scope drift, P1/P0 confirmation, insufficient evidence, or a required understanding gate.
- Optional adapters may report governance coverage, but ambient governance must not depend on a background daemon.
- Run AI coding tasks through the project lifecycle: task_start -> task_plan -> task_implement -> task_verify -> task_close -> memory_file_back.
- Classify user-facing work as U0/U1/U2/U3 UI impact. For U1+ tasks, create and follow `docs/design/UI_CONTRACT.md` and the matching `docs/design/ui-tasks/<id>.yaml` through the public runtime.
- A named UI Skill is an executor, not design authority. U2/U3 production implementation requires an approved visual direction; UI close requires browser screenshots, Visual QA, and accessibility evidence.
- Before closing a task, update relevant project control files and only file back durable conclusions to the wiki.
- For local implementation tasks, read project control files directly when they exist:
  - `PRODUCT_SPEC.md`
  - `ARCHITECTURE.md`
  - `TASKS.md`
  - `TESTING.md`
  - `SECURITY.md`
  - `DEPLOYMENT.md`
  - `OPERATIONS.md`
  - `CHANGELOG.md`

<!-- OBSIDIANTOWIKI:PROJECT_CONTROL_END -->
## Repository-Specific Rules

- Keep public scaffold changes in this repository and durable project memory in the private wiki project pages.
- When changing project attach, bootstrap, setup, or update behavior, update both project entry templates and the relevant product documentation.
