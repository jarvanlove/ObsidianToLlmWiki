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
├── UI_VISUAL_BASELINE.json
├── UI_SKILL_REGISTRY.yaml
├── ui-tasks/<task-id>.yaml
├── qa/<task-id>.md
├── decisions/UI-RFC-<task-id>.md
└── references/
```

`UI_CONTRACT.md` 保存长期项目规则；UI task 保存一次任务的等级、来源、被点名 Skill、批准和证据；RFC 仅用于 U3。截图、QA 与无障碍报告必须在项目仓库内可定位，不能只存在于聊天窗口。

## 低打扰的用户体验

治理机制不能要求普通用户学习色号、等级或审批术语。默认情况下，用户只描述页面和目标；Agent 静默沿用项目基线，首次无参考项目使用固定回退方向。

当用户说“太冷”“太花”“不够高级”等主观反馈时，Agent 先判断问题是否只是排版、层级、状态或文案；只有确属整体气质问题时，才基于色库的用户体验配置推荐 **恰好三个** 通俗方向，例如“温暖品质”“稳重专业”“清爽科技”。用户回复“第二个”或“就这个”即可，选择记录、方向批准和后续证据仍留在后台。

19 组色卡继续是治理资产：六组默认方向用于自动推荐；受控方向只在用户要求更多选择或主动点名时出现；参考方向不对用户呈现为可选生产主题。已有项目若要更换整体气质，Agent 必须作为全局风格调整处理，不能让每个页面各自换色。

## 视觉方向色库

当项目没有 Golden Screen、批准 Figma 或既有设计系统时，Agent 不能把“没有参考”理解为可以随机配色。公开运行时的 `00_system/registry/ui_visual_directions.json` 保存可审计的来源色卡、色名、色号、直接配对对比度、标签和使用限制。

色库分三层：

| 层级 | 规则 |
|---|---|
| 默认方向 | 六个经过基础对比度筛选的方向；没有项目基线时使用固定回退方向，不抽签。 |
| 受控方向 | 保留在完整色库中，但必须由用户按产品气质显式选择并记录。 |
| 参考方向 | 保留为活动视觉、插画或后续研究来源；不能直接成为生产 UI 基线。 |

首次 U1+ 任务把选定方向和共享中性色 token 固化到 `docs/design/UI_VISUAL_BASELINE.json`。U1/U2 复用该基线；只有获批 RFC 的 U3 任务能改基线。实现必须使用 canvas、surface、text、border、action、accent 和 focus 等语义 token，不能从色卡临时复制十六进制颜色。

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
- 没有批准参考时，运行时静默使用固定回退方向，不随机选择色库；用户不满意时只推荐三个通俗候选，受控方向必须留有用户选择记录。
- U1/U2 任务不得替换项目视觉基线；U3 只有在 RFC 获批后才能更新它。
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
