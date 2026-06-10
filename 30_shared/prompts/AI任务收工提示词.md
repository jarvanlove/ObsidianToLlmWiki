---
title: AI任务收工提示词
type: 提示词
domain: 共享
status: 常青
tags:
  - AI编程
  - 任务收工
  - 回写
updated: 2026-06-10
summary: 接入 ObsidianToWiki 的项目在完成 AI coding 任务后用于更新控制文件和生成 wiki 回写候选。
---

# AI任务收工提示词

## 用户说法

```text
请按当前项目规则收工，更新该更新的文件。
```

```text
根据本次 diff 和验证结果，更新 TASKS.md，并判断是否需要回写 wiki。
```

## Agent 内部动作

1. 查看本次 diff。
2. 汇总已完成内容和验证结果。
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
5. 生成 wiki 回写候选，只写长期有效结论。

## 输出格式

```text
任务状态更新：
验证结果：
控制文件更新：
wiki 回写候选：
未处理风险：
下一步：
```

如果只做了普通代码修改，没有稳定结论，不需要写 wiki。
