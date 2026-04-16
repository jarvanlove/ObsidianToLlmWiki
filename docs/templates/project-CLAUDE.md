# Project CLAUDE.md Template

This file lives inside an individual project workspace, not in the public wiki repo.

Use it as the smallest possible bootstrap for Claude Code.

```yaml
wiki_root: <private-wiki-root>
project_repo_root: <current-project-repo-root>
project_slug: <project-slug>
project_index: 20_projects/active/<project-slug>/索引.md
project_overview: 20_projects/active/<project-slug>/概览.md
project_architecture: 20_projects/active/<project-slug>/架构.md
project_decisions: 20_projects/active/<project-slug>/决策.md
project_tasks: 20_projects/active/<project-slug>/任务.md
project_sources: 20_projects/active/<project-slug>/来源.md
project_relations: 20_projects/active/<project-slug>/关系.md
project_risks: 20_projects/active/<project-slug>/风险.md
project_timeline: 20_projects/active/<project-slug>/时间线.md
project_memory: 20_projects/active/<project-slug>/project.memory.md
```

## Minimum Instructions

- Treat the wiki as the project memory layer.
- Treat this file as the bridge from the project repo to the private wiki.
- Read `wiki.context.json` first when it exists, then use this file as the human-readable bootstrap.
- Open the project wiki pages before making changes.
- Write durable conclusions back into the wiki.
- Keep project deliverables in the project repository.
- Reuse shared knowledge when the same pattern appears in other projects.
