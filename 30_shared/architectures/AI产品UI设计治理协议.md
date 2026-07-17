---
title: AI产品UI设计治理协议
type: 架构
domain: 共享
status: 常青
tags:
  - AI编程
  - UI设计
  - DesignAuthority
  - VisualQA
  - Skill治理
updated: 2026-07-17
summary: 定义 AI coding 项目中 UI 设计事实来源、任务分级、Skill 权限、视觉证据和发布门禁，避免通用 UI Skill 直接决定产品审美。
---

# AI产品UI设计治理协议

## 目标

目标不是让模型偶然生成一张“好看”的页面，而是让产品 UI 的方向、实现和验收有稳定边界：

```text
用户任务与真实内容
-> Design Authority
-> 项目 Token、组件和模式
-> 受限 AI 实现
-> 浏览器证据和独立 Visual QA
-> 人类批准
```

ObsidianToWiki 定义协议、模板和验证；项目仓库保存项目自己的视觉事实和证据；私有 wiki 保存长期决策、偏好与来源。Skill、Figma、Stitch、hooks 和 subagents 都是执行器，不是协议来源。

## Design Authority

项目必须在 `docs/design/UI_CONTRACT.md` 定义视觉事实来源。默认优先级：

1. 已批准的 Golden Screen 或明确标记为批准的 Figma 节点。
2. 产品目标、用户任务、真实内容与可访问性需求。
3. 项目 Token、组件和交互模式。
4. 已批准的 Design RFC 和设计决策。
5. 项目 UI Skill Registry。
6. 通用/第三方 UI Skill、组件库默认样式和模型偏好。

低优先级来源不得覆盖高优先级来源。AI 不能授予自己批准权。

## UI 任务分级

| 等级 | 适用范围 | 进入实现前 | 收工前 |
|---|---|---|---|
| U0 | 无用户界面影响 | 正常生命周期 | 正常验证 |
| U1 | 在既有系统内的局部 UI 修改或 UI Bug | 读取 UI Contract | 浏览器截图、Visual QA、无障碍证据 |
| U2 | 新页面、核心流程重构、明显布局/体验改变 | 视觉方向获批准 | U1 证据 + 方向批准 |
| U3 | Token、字体、组件体系、全局布局、品牌方向改变 | 方向与 Design RFC 获批准 | U2 证据 + RFC 批准 |

等级由 Agent 在读取项目事实后判定，不由文件名关键词或用户记忆决定。用户只描述目标；Agent 负责运行内部检查。

## 项目本地控制面

第一次 U1+ 任务才创建以下文件，非 UI 项目不增加空目录：

```text
docs/design/
├── UI_CONTRACT.md
├── UI_SKILL_REGISTRY.yaml
├── ui-tasks/<task-id>.yaml
├── qa/<task-id>.md
├── decisions/UI-RFC-<task-id>.md
└── references/
```

`UI_CONTRACT.md` 保存长期项目规则；UI task 保存一次任务的等级、来源、被点名 Skill、批准和证据；RFC 仅用于 U3。截图、QA 与无障碍报告必须在项目仓库内可定位，不能只存在于聊天窗口。

## Skill 权限模型

| Skill 类别 | 默认调用 | 最大权限 |
|---|---|---|
| Token/组件查询、可访问性、截图和静态规则检查 | 自动可用 | 报告或项目规则内局部修复 |
| 视觉方向、Stitch 探索、品牌重构 | 显式或编排调用 | 仅生成候选，不写生产代码 |
| UI 实现 | 方向批准后 | 按 Contract 实现，不更新基准 |
| Visual QA | 实现后 | 只生成独立报告，不改实现 |
| 发布、基准图更新、组件库迁移 | 显式调用 | 必须人工批准 |
| “美化/高级/现代化”泛化 Skill | 默认关闭或候选模式 | 不得改变项目事实来源 |

用户点名某个 Skill 时，Agent 必须把它记录到 UI task。点名表示选择执行能力，不表示该 Skill 获得设计裁决权。未知第三方 Skill 在登记前只能用于候选探索。

## 状态机与硬门禁

```text
U1: implementation -> verification -> closed
U2: direction -> direction_approved -> implementation -> verification -> closed
U3: direction -> direction_approved + RFC approved -> implementation -> verification -> closed
```

`ui_governance.py` 只验证状态、文件和证据：

- U2/U3 未批准方向时拒绝进入实现。
- U3 未批准 RFC 时拒绝关闭。
- U1+ 缺浏览器截图、Visual QA 或无障碍证据时拒绝关闭。
- 证据路径必须在项目仓库内存在。

它不根据像素或描述宣称“设计好看”。构图、信息层级、品牌感和克制程度由独立 Visual QA 与 Design Authority 判断。

## 视觉验收

UI 变更至少覆盖适用的默认、加载、空、错误、成功、权限、长内容、响应式和焦点状态。证据至少包含：

- 固定视口的真实浏览器截图。
- 独立 Visual QA 报告，列出 P0/P1/P2 和结论。
- 无障碍检查或可复现的手工证据。
- U2/U3 的方向批准记录；U3 的 RFC 批准记录。

视觉评分可用于趋势观察，但在没有多个真实流程校准前，不使用虚假的统一分数替代人工判断。

## 适配器边界

- hooks/subagents 可执行截图、阻止未批准基准图更新或生成 QA 报告，但不得重定义状态机。
- Figma 与 Stitch 适配是可选的项目能力，不写入核心项目接入，也不要求用户配置 API 或 MCP。
- 不得静默修改用户级 Codex、Claude Code 或第三方 Skill 配置。项目 Registry 只约束项目拥有的执行路径；全局配置变更必须由用户明确批准。

## 与生命周期的关系

UI 治理是 [[30_shared/architectures/AI-coding生命周期控制协议|AI coding 生命周期控制协议]] 的子协议。用户仍然只说“开始工作 / 继续 / 收工”；Agent 内部执行 UI 分级、任务创建、证据检查和回写判断。
