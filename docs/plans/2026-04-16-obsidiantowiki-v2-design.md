---
title: ObsidianToWiki v2 Design
status: draft
updated: 2026-04-16
summary: 基于 llm-wiki 与 Hermes Agent 思路，对 ObsidianToWiki 的自学习、自进化、快速接入和跨项目记忆能力进行升级设计。
---

# ObsidianToWiki v2 Design

## 1. Background

ObsidianToWiki 当前已经具备可用的本地 wiki 脚手架：

- 分层目录结构
- 原始资料摄入
- 页面模板与项目骨架
- 索引重建
- 简单搜索
- 基础 lint
- Codex / Claude Code 双入口

但它目前仍然偏“结构化仓库模板”，还不是一个真正持续运转的 agent memory system。当前缺口主要有四类：

1. 元数据与索引弱约束，长期会影响治理和自动化。
2. 接入依赖人工提示，无法保证任意项目快速接入。
3. 记忆停留在单 vault / 单项目层，跨项目复用与互动机制不足。
4. 缺少自学习与自进化闭环，agent 无法稳定从历史行为中改进自身。

这次 v2 设计同时吸收两条上游思路：

- `llm-wiki`：强调原始资料、wiki 页面、索引/日志、frontmatter、wikilinks、ingest/query/lint 的长期维护框架。
- `Hermes Agent`：强调上下文文件接入、长期记忆、技能生成、会话后学习、自我改进的闭环。

## 2. Design Goals

### Functional goals

- 任意 Codex / Claude Code 会话在打开任意项目时，能够快速发现并接入中心 wiki。
- 项目知识能沉淀为项目子 wiki，并与共享层、个人层形成双向回流。
- 多项目之间允许建立显式关系，例如依赖、复用、共用组件、历史演化、风险传播。
- 每次查询、执行、复盘、摄入都可以选择性回写为长期资产。
- 系统能根据历史结果持续改进模板、规则、检索和提示词。

### Non-functional goals

- 仍保持 Markdown 优先和本地优先。
- 对具体 agent 平台保持中立，不绑死在单一工具链。
- 可渐进演进，不要求一次性重构全部脚本。
- 失败时可人工审查和回退，不让自动化黑箱吞掉可解释性。

## 3. Core Principles

1. Human judgment stays upstream.  
   人负责判断价值与边界，agent 负责结构化整理与维护。

2. Local markdown is the system of record.  
   真实知识仍以 Markdown 页面、frontmatter 和双向链接为准。

3. Automation writes with state, not with guesswork.  
   自动化必须建立在可靠 schema、状态字段和可追踪日志上。

4. Retrieval is not enough; filing back is mandatory.  
   查询不是终点，复用价值高的结果必须可回写为长期资产。

5. Memory must work at three scopes.  
   个人、项目、跨项目三个层次都需要独立建模，同时能互相链接。

6. Self-improvement needs explicit loops.  
   自学习不是“多跑几次”，而是有输入、评估、沉淀、再应用的机制。

## 4. Target Architecture

### 4.1 Memory layers

保留现有目录，但从“文件分层”升级成“记忆分层”：

- `01_inbox`: 输入记忆。原始文件、剪藏、临时材料，只做收集与初步抽取。
- `20_projects`: 工作记忆。项目现场事实、任务、决策、风险、时间线、来源。
- `30_shared`: 语义记忆。跨项目可复用的方法、架构、模式、提示词、操作规范。
- `10_personal`: 稳定自我记忆。长期偏好、方法论、个人知识。
- `40_outputs`: 过程记忆。问答、分析、体检、简报、复盘，用于等待进一步提升或归档。

新增一个轻量系统层：

- `00_system/registry/`: 机器可读的 schema、索引缓存、项目注册表、能力注册表。

### 4.2 Agent integration model

为了解决“任意项目快速接入”，引入 agent-neutral bootstrap：

- 每个项目仓库根目录可放 `AGENTS.md`、`CLAUDE.md`，并允许共用同一份最小内容。
- 新增 `wiki.context.json` 作为机器可读入口。
- 新增 `project.memory.md` 作为项目级运行态摘要文件。

`wiki.context.json` 建议至少包含：

```json
{
  "wiki_root": "C:/path/to/private/wiki",
  "project_slug": "demo-saas",
  "project_root": "C:/path/to/repo",
  "project_index": "20_projects/active/demo-saas/索引.md",
  "project_overview": "20_projects/active/demo-saas/概览.md",
  "project_tasks": "20_projects/active/demo-saas/任务.md",
  "shared_indexes": [
    "30_shared/索引.md"
  ],
  "memory_policy": {
    "write_back_query_results": true,
    "promote_reusable_knowledge": true
  }
}
```

这使 Codex、Claude Code、未来其他 agent 都可以先读统一上下文文件，再进入 wiki。

### 4.3 Cross-project knowledge graph

项目与项目之间的交互不能只靠人工记忆，v2 需要引入显式关系：

- `depends_on`: 当前项目依赖哪些项目或共享能力
- `reuses`: 当前项目复用哪些架构 / 模式 / 工具
- `related_to`: 主题相关项目
- `supersedes`: 替代哪个旧项目或旧方案
- `produces`: 项目产出哪些共享资产

这些关系先保存在页面 frontmatter 和标准链接里，再由脚本聚合为项目注册表。这样既保持 Markdown 可读性，也能支持后续机器处理。

## 5. New Capabilities

### 5.1 Strong metadata and schemas

当前 frontmatter 解析过于宽松。v2 需要：

- 用正式 YAML 解析替换手写解析器
- 为不同页面类型定义 schema
- 在 lint 阶段校验字段完整性和合法值
- 引入统一字段：
  - `id`
  - `type`
  - `domain`
  - `project`
  - `status`
  - `updated`
  - `tags`
  - `source_path`
  - `source_hash`
  - `derived_from`
  - `derived_pages`
  - `review_due`
  - `relations`

这一步是后续检索、治理、自学习的基础。

### 5.2 Stateful ingest pipeline

资料摄入从“复制文件并生成来源笔记”升级成状态机：

- `registered`: 已登记
- `parsed`: 已抽取文本
- `summarized`: 已生成来源摘要
- `filed`: 已回写到结构化页面
- `promoted`: 已提升到共享层或个人层
- `archived`: 已归档

同一来源需要去重：

- 用 `source_hash` 标识内容
- 记录来源笔记与衍生页面之间的链路
- 在 `来源.md` 和项目索引里显示“未整理来源”

这样系统不会逐渐退化成素材坟场。

### 5.3 Task-oriented indexes

索引不再只是目录，而是工作台：

- 根索引显示活跃项目、最近重要决策、待整理来源、待复盘页面
- 项目索引显示当前任务、风险、最近来源、关键 ADR、依赖项目
- 共享索引显示最近新增的可复用资产和待推广候选

索引的目标从“方便浏览”升级为“直接驱动下一步行动”。

### 5.4 Governance and health checks

lint 扩展为 wiki governance：

- 缺 frontmatter 或 schema 不合法
- 死链接 / 模糊链接冲突
- 孤儿页面
- 长期未更新页面
- 重复主题页
- 来源已入库但未沉淀
- 项目经验已成熟但未提升到共享层
- 项目主干页面缺回链
- 跨项目依赖未声明

体检输出不只是报告，还要生成可执行修复建议，并允许安全自动修复。

### 5.5 Retrieval and memory recall

检索升级成分层召回：

- 结构化过滤：按 `project/type/tag/status/date` 检索
- 分层结果：来源、项目页、共享页、输出页分别展示
- 关系召回：当查询命中一个项目时，同时提示其依赖项目和共享资产
- 别名 / 同义词表：降低中文表达差异带来的漏召回

后续可选增加 embedding，但不作为 P0。

## 6. Self-Learning and Self-Evolution

这是 v2 的核心新增，也是对 Hermes Agent 最值得借鉴的部分。

### 6.1 Post-session learning loop

每次会话结束后，agent 不只更新页面，还要运行一次轻量学习流程：

1. 读取本次新增日志、修改页面、查询行为。
2. 提炼：
   - 哪些回答具有复用价值
   - 哪些操作反复出现
   - 哪些检索失败或命中不足
   - 哪些模板字段不够用
3. 将结果分类写入：
   - `30_shared/patterns/`
   - `30_shared/prompts/`
   - `10_personal/`
   - `40_outputs/analyses/`
4. 标记一个“学习候选”状态，等待后续体检或人工确认。

### 6.2 Skill and prompt evolution

借鉴 Hermes 的“agent can improve its capabilities”思路，但落地为可控版本：

- 新增 `00_system/registry/capabilities.yaml`
- 把高频成功工作流登记为 capability
- 把低质量提示词替换、合并、归档
- 允许从成功案例生成新模板或 prompt 草案
- 所有自动生成的能力资产先进入候选区，再由 lint 或人工确认发布

这样系统的“自进化”体现在模板、提示词、操作规程和索引逻辑逐步增强，而不是直接自改核心代码。

### 6.3 Reflection pages

新增两类页面：

- `项目复盘`: 对项目内策略和执行做反思
- `系统反思`: 对整个 wiki 系统的缺陷、误召回、维护问题做反思

建议新增目录：

- `40_outputs/reflections/`

反思页不是日志，它必须包含：

- 观察
- 原因分析
- 后续动作
- 是否应升级为模板 / 模式 / 规则

## 7. Project Fast-Connect Design

### 7.1 One-command project attach

新增一个接入命令，例如：

```bash
python 00_system/scripts/attach_project.py --repo-root /path/to/repo --project demo-saas
```

这个命令完成：

- 检测仓库根目录
- 在中心 wiki 创建项目骨架
- 在项目仓库写入 `AGENTS.md` / `CLAUDE.md` / `wiki.context.json`
- 注册项目到 `00_system/registry/projects.yaml`
- 初始化跨项目关系字段

### 7.2 Runtime memory file

每个项目增加 `project.memory.md`，记录高频运行态摘要：

- 当前目标
- 当前风险
- 当前假设
- 当前阻塞
- 关键依赖
- 近期变更

这类文件适合被 agent 在每次开始时快速读取，成本比全量读项目 wiki 更低。

### 7.3 Agent-neutral conventions

不要只假设 Codex / Claude Code。接入规范应以“文件协议”为核心：

- `wiki.context.json`: 机器可读
- `AGENTS.md`: 面向 Codex
- `CLAUDE.md`: 面向 Claude Code
- 未来如果有其他 agent，只要能读 `wiki.context.json` 就能接入

## 8. Cross-Project Interaction Model

跨项目交互至少要支持三种场景：

1. Shared architecture reuse  
   一个项目复用另一个项目沉淀出的架构、组件、规范。

2. Operational dependency  
   一个项目依赖另一个项目的系统、数据源、服务或团队约束。

3. Knowledge promotion  
   多个项目里反复出现的经验，被提升到 `30_shared` 并反链回项目。

建议为每个项目新增：

- `关系.md`
- `时间线.md`
- `风险.md`

其中 `关系.md` 专门维护跨项目互动，避免把这些信息散落在概览或架构页里。

## 9. Implementation Roadmap

### P0: make the system structurally reliable

- 正式 YAML/frontmatter 解析
- schema 校验
- `wiki.context.json` 设计与接入
- `attach_project.py`
- `projects.yaml` 注册表
- lint 扩展到死链、缺字段、未沉淀来源、重复主题
- README / 使用手册补充来源和接入规范

### P1: make the system operationally useful

- 来源状态机
- 任务型索引
- `project.memory.md`
- `关系.md` / `风险.md` / `时间线.md`
- 检索分层展示与结构化过滤
- 学习候选与反思页机制

### P2: make the system self-improving

- capability registry
- 提示词和模板演化流程
- 查询失败与命中质量分析
- 跨项目知识提升候选检测
- 半自动生成共享模式页

## 10. Key ADR-Level Decisions

### Decision A: Markdown remains source of truth

- Why: 可审查、可迁移、对 agent 与人都透明。
- Trade-off: 机器查询不如数据库直接。
- Conclusion: 接受，用 registry 和缓存层补足。

### Decision B: Self-evolution first targets prompts/templates/registries, not autonomous code mutation

- Why: 直接让系统自动改核心脚本风险太高。
- Trade-off: 进化速度更慢，但可控。
- Conclusion: 先从知识资产与规则资产的自进化做起。

### Decision C: Project onboarding is protocol-based, not agent-specific

- Why: 避免未来重复为每个 agent 重写接入方式。
- Trade-off: 需要同时维护人类可读和机器可读入口。
- Conclusion: 接受，统一以 `wiki.context.json` 为底座。

## 11. Risks

- schema 收紧后，旧页面需要迁移。
- 自动回写过强会污染知识库，需要候选区和审查机制。
- 跨项目关系建模过度会增加维护成本。
- embedding 检索如果过早引入，会抬高复杂度和依赖。

## 12. Recommended Next Steps

1. 先做 P0，不碰 embedding，不碰复杂数据库。
2. 把 `wiki.context.json` 和 `attach_project.py` 作为第一优先级。
3. 同步升级 `lint_wiki.py`，让系统先具备结构治理能力。
4. 为来源笔记增加状态字段和衍生页面字段。
5. 等 P0/P1 跑稳后，再加自学习和能力注册机制。

## References

- Karpathy `llm-wiki`: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Nous Research `Hermes Agent`: https://github.com/NousResearch/hermes-agent
