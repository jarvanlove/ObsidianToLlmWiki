---
title: AI任务执行提示词
type: 提示词
domain: 共享
status: 常青
tags:
  - AI编程
  - 任务执行
  - Codex
  - ClaudeCode
updated: 2026-05-19
summary: 用于让 AI 在已有项目控制文件约束下执行单个任务，避免直接开写和越界修改。
---

# AI任务执行提示词

## 使用场景

当项目已经有 `CLAUDE.md`、`AGENTS.md`、`PRODUCT_SPEC.md`、`ARCHITECTURE.md`、`TASKS.md`、`TESTING.md` 后，用这个提示词执行单个任务。

## 提示词

```text
请处理 TASKS.md 中的任务：[任务ID或任务描述]

先不要改代码。

第一步：阅读并遵守：
1. CLAUDE.md
2. AGENTS.md（如果你是 Codex）
3. PRODUCT_SPEC.md
4. ARCHITECTURE.md
5. TESTING.md
6. TASKS.md

第二步：输出任务分析：
- 我对需求的理解
- 这个任务属于 P3/P2/P1/P0 哪个风险等级
- 会影响哪些用户路径
- 会影响哪些文件/模块
- 是否涉及数据库、权限、安全、支付、外部 API
- 最小实现方案
- 需要新增或修改的测试
- 预计修改文件列表
- 需要我确认的问题

第三步：
如果没有必须确认的问题，就按最小方案实现。
如果有高风险或需求不清，先停下来问我。

实现要求：
- 只改和任务直接相关的文件。
- 不做无关重构。
- 不新增依赖，除非说明原因并得到确认。
- 不改变旧行为，除非任务明确要求。
- 优先补测试或明确验收步骤。
- 完成后运行 TESTING.md 中最小相关验证。

最后输出：
- 修改了哪些文件
- 行为变化是什么
- 运行了哪些验证命令
- 验证结果
- 剩余风险
- 是否需要更新 PRODUCT_SPEC.md / ARCHITECTURE.md / CHANGELOG.md
```

