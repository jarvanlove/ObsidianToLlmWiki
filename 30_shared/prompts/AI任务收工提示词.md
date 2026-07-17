---
title: AI任务收工提示词
type: 提示词
domain: 共享
status: 常青
tags:
  - AI编程
  - 任务收工
  - 回写
updated: 2026-06-19
summary: 接入 ObsidianToWiki 的项目在完成 AI coding 任务后用于更新控制文件和生成 wiki 回写候选。
---

# AI任务收工提示词

## 用户说法

```text
收工。
```

```text
根据本次 diff 和验证结果，更新 TASKS.md，并判断是否需要回写 wiki。
```

## Agent 内部动作

1. 查看本次 diff。
2. 按 [[30_shared/architectures/AI模块测试验收证据协议|AI模块测试验收证据协议]] 汇总已完成内容和验证证据。
3. 更新 `TASKS.md` 的任务状态、剩余问题和 follow-up。
4. 判断是否需要更新：
   - `PRODUCT_SPEC.md`
   - `ARCHITECTURE.md`
   - `TESTING.md`
   - `SECURITY.md`
   - `DEPLOYMENT.md`
   - `OPERATIONS.md`
   - `CHANGELOG.md`
   - `docs/adr/`
5. 检查是否存在未验证风险、控制台错误、真实环境未跑、文档未同步等收工阻塞项。
6. 生成 wiki 回写候选，只写长期有效结论。

## 收工验收门禁

收工前必须检查：

- 本次 diff 是否只包含当前任务相关修改。
- 静态检查、构建或语言检查是否已运行；未运行时说明原因。
- 涉及 API/session 时是否跑过真实 HTTP smoke。
- 涉及数据库时是否跑过 migration、seed 或真实 DB 查询。
- 涉及 UI 时是否跑过浏览器 smoke，并检查控制台和 hydration。
- U1+ UI task 是否保留固定视口截图、Visual QA 和无障碍证据；U2/U3 是否已有方向批准，U3 是否已有 RFC 批准。
- 涉及权限时是否跑过未登录、无权限或失败路径。
- 涉及数据质量时是否检查来源、口径、置信度或人工确认状态。
- 项目控制文件是否需要更新。
- 是否有跨项目可复用经验需要回写 `30_shared`。

## 输出格式

```text
任务状态更新：
验证结果：
真实链路：
浏览器/控制台：
控制文件更新：
wiki 回写候选：
未处理风险：
下一步：
```

如果只做了普通代码修改，没有稳定结论，不需要写 wiki。

不能收工的情况：

- 核心路径没有跑通。
- UI 控制台仍有应用自身错误。
- 有真实环境问题但只用 mock 测试替代。
- 认证、权限、数据库、文件或外部服务风险未说明。
- 文档和实际行为明显不一致。
