---
title: AI coding 生命周期控制协议
type: 架构
domain: 共享
status: 常青
tags:
  - AI编程
  - 项目控制文件
  - 生命周期
  - 回写
updated: 2026-06-10
summary: 定义接入 ObsidianToWiki 的项目在 AI coding 过程中如何开始任务、收工、更新项目控制文件和回写 wiki。
---

# AI coding 生命周期控制协议

## 目标

让 AI coding 不再只产生代码 diff，而是稳定维护项目控制面：

```text
用户请求 -> 项目控制文件 -> 实现与验证 -> 控制文件更新 -> wiki 长期记忆
```

ObsidianToWiki 负责定义协议、模板和脚本；接入项目负责在本地执行协议；wiki 负责沉淀长期结论。

## 项目驾驶舱

日常使用不应该要求用户记住所有命令。主路径收敛为三句话：

| 用户说法 | 系统内部动作 |
|---|---|
| `开始工作` | 判断项目是否接入；未接入则执行接入并检查；已接入则恢复上下文和当前任务 |
| `继续` | 判断当前任务和工作区状态；继续当前任务或提示先收工 |
| `收工` | 查看 diff 和验证结果；生成控制文件更新候选和 wiki 回写候选 |

高级话术仍然可用，但不作为日常主入口。

## 项目状态机

| 状态 | 识别方式 | 默认动作 |
|---|---|---|
| `not_attached` | 缺少 `wiki.context.json` 或核心入口 | 运行项目接入并执行严格检查 |
| `attached_idle` | 已接入，无明显未收工 diff | 读取任务和 wiki 上下文，给出下一步 |
| `in_progress` | 有任务上下文或代码变更 | 继续任务，验证后进入收工 |
| `needs_close` | 有 diff，缺少验证或任务状态未整理 | 运行收工检查，更新控制文件候选 |

## 分层

| 层 | 职责 |
|---|---|
| ObsidianToWiki scaffold | 定义生命周期、控制文件模板、更新规则、回写策略 |
| 项目仓库 | 保存当前项目事实、任务状态、验证命令和交付物 |
| 私有 wiki | 保存长期项目记忆、决策、风险、时间线、共享模式 |
| hooks / subagents | 可选执行器，只调用协议，不自定义协议 |

## 生命周期节点

| 节点 | 触发 | 必读输入 | 输出 |
|---|---|---|---|
| `task_start` | 开始一个任务 | `wiki.context.json`, `TASKS.md`, `PRODUCT_SPEC.md`, `ARCHITECTURE.md`, `TESTING.md` | 任务边界、风险等级、预计触碰文件、验证方式 |
| `task_plan` | 非平凡修改前 | 相关源码、控制文件、项目 wiki 核心页 | 最小计划和验收标准 |
| `task_implement` | 范围明确后 | 计划、源码、测试 | 最小 diff |
| `task_verify` | 修改后 | `TESTING.md`, 本次 diff | 验证命令、结果、未验证风险 |
| `task_close` | 收工前 | git diff、验证结果、`TASKS.md` | 任务状态更新、后续项、CHANGELOG/ADR/wiki 候选 |
| `memory_file_back` | 产生长期结论时 | 本次结论、证据、目标层 | 项目 wiki / shared / personal 回写 |

接入也属于生命周期节点：

| 节点 | 触发 | 必读输入 | 输出 |
|---|---|---|---|
| `project_attach` | 项目未接入或用户要求重新接入 | 当前 repo root、wiki root、项目名 | `wiki.context.json`、入口文件、控制文件、support dirs、项目 wiki 页、严格检查报告 |

## 更新规则矩阵

| 事件 | 必须更新 | 可选更新 |
|---|---|---|
| 新任务开始 | `TASKS.md` | 项目 wiki 任务页 |
| 任务完成 | `TASKS.md` | `CHANGELOG.md` |
| 用户需求变更 | `PRODUCT_SPEC.md`, `TASKS.md` | 项目 wiki 决策页 |
| 架构边界变化 | `ARCHITECTURE.md` 或 `docs/adr/` | 项目 wiki 架构页 |
| 测试命令变化 | `TESTING.md` | 项目 wiki 经验页 |
| 部署方式变化 | `DEPLOYMENT.md` | 项目 wiki 风险页 |
| 运维事故或排障 | `OPERATIONS.md` | 项目 wiki 时间线/风险页 |
| 安全、权限、数据删除变化 | `SECURITY.md`, `TASKS.md` | 项目 wiki 风险页 |
| 版本级用户可见变化 | `CHANGELOG.md` | 项目时间线 |
| 跨项目可复用经验 | 无固定项目文件 | `30_shared/` |
| 个人偏好或工作方法 | 无固定项目文件 | `10_personal/` |

## 回写边界

不要把每个代码修改都写入 wiki。按三级处理：

| 级别 | 目标 | 说明 |
|---|---|---|
| L1 | 项目控制文件 | 当前任务、验证、范围、部署、运维等实时事实 |
| L2 | 项目 wiki | 稳定决策、架构解释、风险、复盘、里程碑 |
| L3 | shared / personal | 跨项目复用模式、个人偏好、重复出现的方法 |

## hooks / subagents 位置

hooks 和 subagents 是可选执行器，不是协议源头。

可行用法：

- `pre-task`：检查控制文件是否存在，输出任务上下文。
- `post-task`：基于 diff 和验证结果生成控制文件更新候选。
- `wiki-memory-agent`：判断哪些结论值得写回 wiki。
- `architecture-review-agent`：判断是否需要 ADR 或 `ARCHITECTURE.md` 更新。

约束：

- hooks 不应直接大范围改文档。
- subagents 不应成为唯一事实源。
- 每个项目可以配置触发方式，但更新规则由 ObsidianToWiki scaffold 统一定义。

## 适配层安装策略

适配层默认不安装。只有用户显式要求时，项目接入才写入 adapter 模板：

```powershell
python <obsidiantowiki-root>\00_system\scripts\attach_project.py --repo-root <project> --project <name> --install-ai-adapters
```

adapter 模板只放在项目仓库中：

```text
scripts/ai/
docs/ai-workflows/adapters.md
docs/ai-workflows/subagents/
```

adapter 通过 `OBSIDIANTOWIKI_SCAFFOLD_ROOT` 找到公开 scaffold，不写死个人 wiki 路径，不直接同步 private vault。

## 最小执行版

第一版只要求 agent 在自然语言任务中执行：

```text
1. 用户说“开始工作”时，先判断项目状态；未接入就接入并严格检查。
2. 用户说“继续”时，恢复项目上下文，确认任务边界、风险等级和验证方式。
3. 修改后运行最小相关验证。
4. 用户说“收工”时，检查 diff、验证结果和控制文件更新候选。
5. 只有长期有效结论才回写 wiki。
```
