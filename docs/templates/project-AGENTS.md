# 项目 AGENTS 模板

这个文件放在单个项目仓库根目录，不放在公开 wiki 根目录。

它的作用是：作为 Codex 的项目入口，把当前项目仓库接到你的私有 wiki，并指向项目级控制文件。

```yaml
wiki_root: <private-wiki-root>
runtime_root: <obsidiantowiki-public-root>
project_repo_root: <current-project-repo-root>
project_slug: <project-slug>
project_scaffold_version: <managed-version>
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

## 最小规则

- 这是 Codex 项目入口；不要要求 Codex 先读 `CLAUDE.md`
- 把 wiki 当作项目记忆层
- 优先读取 `wiki.context.json`
- 从 `wiki.context.json` 使用公开 `runtime_root`，不要把私有库中的兼容脚本当作主运行时
- 用户日常只需要说 `开始工作`、`继续`、`收工`；Context 预算检查、候选生成、收据决议后的记忆编译和驾驶舱刷新由 agent 内部完成
- 动手前先打开对应项目页面
- 本地实现任务直接读取 `PRODUCT_SPEC.md`、`ARCHITECTURE.md`、`TASKS.md`、`TESTING.md`、`DEPLOYMENT.md`、`OPERATIONS.md`、`SECURITY.md`
- 稳定结论写回 wiki，不要只留在聊天窗口
- 项目交付物留在项目仓库，长期记忆留在 wiki
- AI coding 任务按生命周期执行：开始前确认任务边界、修改后验证、收工前更新控制文件并判断是否回写 wiki
- 用户面对 UI 的任务先按 U0/U1/U2/U3 分级；U1+ 使用 `docs/design/UI_CONTRACT.md` 和对应 UI task，U2/U3 未获视觉方向批准不得写生产页面
- 用户点名的 UI Skill 只是执行器，不能覆盖项目设计来源、Token、组件和视觉验收规则
- `收工` 会生成本地 `.obsidiantowiki/session-receipt.json`；agent 必须逐项执行或标记不适用，再用 `project_session.py resolve` 完成闭环。未决议不得编译记忆；维护失败保留任务结果并标记 `pending_memory_repair`
