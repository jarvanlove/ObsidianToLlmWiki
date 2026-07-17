---
title: Figma与Stitch协作适配规范
type: 模式
domain: 共享
status: 常青
tags:
  - UI设计
  - Figma
  - Stitch
  - DesignSystem
updated: 2026-07-17
summary: 明确 Figma 和 Stitch 在 AI 产品 UI 生产中的不同职责，避免将生成工具输出直接当作生产设计或代码。
---

# Figma与Stitch协作适配规范

## 工具定位

| 工具 | 最适合做什么 | 不应做什么 |
|---|---|---|
| Stitch | 发散视觉方向、快速原型、比较不同构图与体验路线 | 自动决定最终设计或直接提交生成代码 |
| Figma | 已批准方向的精确画面、组件变量、设计交付与代码映射 | 仅因存在节点就自动成为设计事实 |
| 项目代码 | 真实交互、状态、响应式、性能和可访问性 | 重新发明一套脱离设计 Contract 的视觉体系 |

## Stitch：发散后收敛

Stitch 生成的页面默认是 `exploratory`，不是 `approved`。每个候选必须记录：

- 服务的用户任务与真实内容。
- 借鉴什么：例如信息密度、主次关系、导航组织。
- 不借鉴什么：例如第三方品牌色、无关装饰、演示数据结构。
- 适用的桌面/移动状态和已知风险。

只有用户明确批准后，候选才能在 UI task 中成为方向来源。Stitch 生成代码只能作为参考，必须经过项目组件、Token、无障碍和截图 QA 后重写为生产实现。

## Figma：批准后实施

Figma 节点只有在 UI task 中被记录为 `approved` 才具权威。Agent 读取节点时应同时读取项目 UI Contract，确认：

- 组件是否映射到代码真实组件。
- Variables/Token 是否有明确语义。
- 节点是否覆盖关键状态和响应式布局。
- 当前节点是否已被 superseded。

Figma MCP 和 Code Connect 是可选增强：它们可提供组件、变量和真实代码映射，但不能替代项目的批准记录或 Visual QA。

## 最小可追溯记录

项目不强制保存完整设计文件副本。每个被采用的来源至少记录在 UI task 中：

```yaml
design_authority:
  sources:
    - tool: figma | stitch | reference-image
      reference: URL-or-project-relative-path
      status: exploratory | approved | superseded
      borrow: what-to-reuse
      avoid: what-not-to-copy
```

外部工具不可用时，项目仍可用截图、项目内参考图和文字 Contract 完成同一流程。
