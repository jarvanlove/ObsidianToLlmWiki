# 私有库接入说明

这份文档只讲一件事：怎么把 `ObsidianToWiki-private` 变成你真正使用的知识库。

## 先说清楚公开仓库和私有库的关系

- `ObsidianToWiki`
  公开脚手架，放脚本、模板、规则、说明
- `ObsidianToWiki-private`
  私有知识库，放你的真实项目、个人知识、原始资料和沉淀结果

这两个仓库不是自动双向同步。

当前支持的是：

- 用公开仓库的脚手架去同步私有库
- 不把私有内容同步回公开仓库

## 私有库第一次应该长什么样

至少要有这些顶层目录和文件：

```text
ObsidianToWiki-private/
├─ 00_system/
├─ 01_inbox/
├─ 10_personal/
├─ 20_projects/
├─ 30_shared/
├─ 40_outputs/
├─ 90_archive/
├─ Home.md
├─ 快速开始.md
├─ 使用手册.md
├─ 会话启动页.md
├─ index.md
├─ log.md
├─ AGENTS.md
├─ CLAUDE.md
├─ README.md
└─ README-zh.md
```

## 个人知识怎么接

个人知识不是“先建复杂结构”，而是先从最小沉淀开始。

建议你先这样用：

1. 新资料先放 `01_inbox/raw/`
2. 有长期价值的内容整理进 `10_personal/`
3. 跨项目可复用的内容提升到 `30_shared/`
4. 一次问答或分析有长期价值时，先落到 `40_outputs/`

最开始你只需要保证：

- `10_personal/索引.md` 存在
- `30_shared/索引.md` 存在
- `40_outputs/索引.md` 存在

## 项目怎么接

如果你有一个现成项目仓库，要把它接入私有库：

```powershell
python 00_system/scripts/attach_project.py --repo-root "C:\path\to\repo" --project "demo-saas"
```

默认情况下，这个脚本会优先找当前公开仓库同级目录里的 `ObsidianToWiki-private`。

接入后会发生两件事：

1. 项目仓库里生成：
   - `wiki.context.json`
   - `AGENTS.md`
   - `CLAUDE.md`
2. 私有库里生成项目主干页：
   - `索引.md`
   - `概览.md`
   - `架构.md`
   - `决策.md`
   - `任务.md`
   - `来源.md`
   - `关系.md`
   - `风险.md`
   - `时间线.md`
   - `project.memory.md`

## 资料怎么接进私有库

把资料摄入某个项目：

```powershell
python 00_system/scripts/ingest_source.py --source "C:\path\to\prd.docx" --title "PRD v1" --project "demo-saas" --tags "prd,需求"
```

把资料先收进全局知识库，再决定后续归类，也可以先放到：

- `01_inbox/raw/`

## 私有库和公开仓库怎么同步

先预览：

```powershell
python 00_system/scripts/sync_private_vault.py --dry-run
```

确认没问题再执行：

```powershell
python 00_system/scripts/sync_private_vault.py
```

这个同步只复制脚手架层内容，比如：

- `00_system/`
- `docs/`
- 根入口文件
- `30_shared/prompts/`

不会覆盖你的私有项目内容、个人知识和原始资料。
