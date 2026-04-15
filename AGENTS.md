# ObsidianToWiki Agent Rules

## Entry Points

- [[Home|首页]]
- [[index|总索引]]
- [[README|README]]
- [[README-zh|中文说明]]
- [[使用手册|使用手册]]
- [[会话启动页|会话启动页]]
- [[log|操作日志]]

## Goal

这是一个由 LLM 持续维护的 Obsidian Wiki，服务两个方向：

- 个人长期知识积累
- 软件项目级记忆与复盘

人负责提供资料、提出问题、判断价值。代理负责整理、建页、链接、更新、索引、记录日志。

## Directory Conventions

- `Home.md`: 人工入口页
- `index.md`: 全局路由页，不承担全文检索职责
- `log.md`: 追加式操作日志
- `01_inbox/`: `raw`、`clips`、`scratch`
- `10_personal/`: 长期有效的个人知识
- `20_projects/`: 每个项目一个子 wiki
- `30_shared/`: 跨项目复用的模式、工具、架构、提示词
- `40_outputs/`: 分析、简报、问答沉淀
- `90_archive/`: 低频但保留检索价值的内容
- `00_system/`: 模板、脚本、维护规则

## Page Rules

- 只使用 Markdown。
- 一页尽量只表达一个主题。
- 内部引用统一使用 Obsidian 双向链接。
- `01_inbox/raw/` 中的原始文件不可直接改写。
- 持久页面必须带 frontmatter。

```yaml
---
title: 示例标题
type: 概念
domain: 个人
project:
status: 常青
tags: [示例]
updated: 2026-04-15
summary: 一句话摘要
---
```

## Workflow

### Ingest

1. 从 `01_inbox/raw/` 或项目资料目录读取新来源。
2. 如果内容有长期价值，生成独立知识页或来源笔记。
3. 更新相关的个人页、项目页、共享页。
4. 补充必要的双向链接。
5. 追加写入 `log.md`。
6. 重建索引。

### Query And File Back

1. 先读 `index.md` 判断应该进入哪个知识分区。
2. 开放式问题优先使用本地搜索，再缩小阅读范围。
3. 仅读取完成回答所需的最小页面集合。
4. 回答时优先引用 wiki 链接或具体文件路径。
5. 如果答案有复用价值，沉淀到 `40_outputs/` 或对应项目中。
6. 如有页面变更，更新日志并重建索引。

### Project Knowledge

- 每个进行中的项目位于 `20_projects/active/<project-slug>/`
- 核心页面至少维护：`概览.md`、`架构.md`、`决策.md`、`经验.md`、`来源.md`、`任务.md`
- 项目过程性笔记放在 `notes/`
- 来源摘要放在 `source-notes/`
- 原始文件放在 `sources/`
- 可复用的项目经验要提升到 `30_shared/` 或 `10_personal/`

### Lint

定期检查：

- 孤儿页面
- 过期页面
- 重要页面缺少回链
- 应从项目中提升到共享层的经验
- 重复或应该合并的页面

## Retrieval Strategy

- `index.md` 只负责路由
- 各分区 `索引.md` 负责目录导航
- 项目自己的 `索引.md` 负责项目局部导航
- `00_system/scripts/search_wiki.py` 负责中大规模召回
- `rg` 适合做精确文本排查

## Automation Commands

- New page: `python 00_system/scripts/create_page.py --title "事件溯源" --type 模式`
- New project: `python 00_system/scripts/create_page.py --title "my-app" --type 项目`
- Log event: `python 00_system/scripts/log_event.py --kind 摄入 --title "新增文章"`
- Rebuild index: `python 00_system/scripts/rebuild_indexes.py`
- Search wiki: `python 00_system/scripts/search_wiki.py "权限 设计"`
- Lint wiki: `python 00_system/scripts/lint_wiki.py`

## Naming Strategy

- 仓库路径与脚本名统一使用英文。
- 页面标题、正文和链接显示名优先保持中文可读性。
- 常青主题尽量使用稳定标题，避免频繁改名。
- 只属于某一个项目的知识，优先留在项目目录中。
- 跨项目可复用的知识，提升到 `30_shared/` 并从项目页回链。
