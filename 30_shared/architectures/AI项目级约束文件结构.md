---
title: AI项目级约束文件结构
type: 架构
domain: 共享
status: 常青
tags:
  - AI编程
  - 项目结构
  - 约束文件
  - CLAUDE.md
  - AGENTS.md
updated: 2026-05-19
summary: 项目级 AI 约束文件的职责分工和最小模板。用于把全局 AI 原则落到具体项目，避免 AI 每次重新理解项目、越界修改或忽略验证。
---

# AI项目级约束文件结构

## 1. 原则

全局文件解决通用原则，项目文件解决具体事实。

```text
全局 AGENTS.md / CLAUDE.md：所有项目都遵守的价值观和工作原则。
项目 CLAUDE.md：当前项目的主 AI 手册。
项目 AGENTS.md：Codex 对当前项目的适配说明。
项目 docs/*：详细规格、流程、决策和运行手册。
```

不要把所有内容都塞进 `CLAUDE.md` 或 `AGENTS.md`。入口文件只放高频、关键、可执行信息。

## 2. 推荐目录

```text
<project>/
  CLAUDE.md
  AGENTS.md
  PRODUCT_SPEC.md
  ARCHITECTURE.md
  TASKS.md
  TESTING.md
  SECURITY.md
  DEPLOYMENT.md
  OPERATIONS.md
  CHANGELOG.md
  docs/
    adr/
    design/
    product/
    runbooks/
    growth/
    ai-workflows/
  scripts/
    verify/
    deploy/
    db/
```

## 3. CLAUDE.md 最小模板

```markdown
# Project AI Guide

## Project Snapshot

- Name:
- One-line purpose:
- Target users:
- Current stage:
- Tech stack:

## Read First

Before changing code, read:

1. PRODUCT_SPEC.md
2. ARCHITECTURE.md
3. TESTING.md
4. TASKS.md

## Non-Negotiable Rules

- Do not implement features not listed in PRODUCT_SPEC.md or TASKS.md.
- Do not refactor unrelated code.
- Do not change architecture boundaries without updating ARCHITECTURE.md.
- Do not change API behavior without tests.
- Do not change database schema without migration notes.
- Do not mark work complete without running TESTING.md verification.

## Architecture Boundaries

- UI:
- API:
- Domain/service:
- Data access:
- External integrations:

## Common Commands

- Install:
- Dev:
- Typecheck:
- Lint:
- Test:
- Build:
- Verify:

## Task Workflow

For non-trivial tasks:

1. Analyze impact first.
2. Propose minimal plan.
3. Add or identify tests.
4. Implement only confirmed scope.
5. Run verification.
6. Summarize changed files, validation, and residual risks.

## Change Request Workflow

For requirement changes:

1. Update or quote the relevant PRODUCT_SPEC.md section.
2. Identify affected user flows, API, data model, and tests.
3. Preserve old behavior unless explicitly changed.
4. Keep the modification local.

## Completion Report Format

- Changed files:
- Behavior changed:
- Verification run:
- Risks:
- Follow-up tasks:
```

## 4. AGENTS.md 最小模板

```markdown
# Codex Project Instructions

This file adapts the project for Codex. The main project AI guide is CLAUDE.md.

## Required Reading

Before edits:

1. CLAUDE.md
2. PRODUCT_SPEC.md
3. ARCHITECTURE.md
4. TESTING.md
5. TASKS.md

## Codex Execution Rules

- Use `rg` for search.
- Before editing, state the files you expect to touch.
- Use minimal patches.
- Prefer existing project patterns.
- Do not perform unrelated cleanup.
- After editing, run the smallest relevant verification from TESTING.md.
- If verification cannot run, explain why.

## Default Task Loop

1. Inspect relevant files.
2. Report impact and plan.
3. Implement only approved or clearly scoped change.
4. Run verification.
5. Report changed files, command results, and risks.

## Stop Conditions

Stop and ask if:

- The requirement conflicts with PRODUCT_SPEC.md.
- The change requires architecture modification.
- The change touches authentication, payment, data deletion, or migrations without explicit scope.
- The correct behavior is ambiguous and no test or spec resolves it.
```

## 5. PRODUCT_SPEC.md 最小模板

```markdown
# Product Spec

## Product

- Name:
- Target user:
- Core problem:
- Promise:

## MVP Scope

Must have:

- 

Nice to have later:

- 

Explicitly not doing:

- 

## User Flows

### Flow 1

- Entry:
- Steps:
- Success:
- Failure/empty states:

## Acceptance Criteria

- 

## Change Log

| Date | Change | Reason | Impact |
|---|---|---|---|
```

## 6. ARCHITECTURE.md 最小模板

```markdown
# Architecture

## System Shape

- App type:
- Frontend:
- Backend:
- Database:
- Deployment:

## Module Boundaries

| Module | Owns | Must not do |
|---|---|---|

## Data Model

| Entity | Purpose | Key fields |
|---|---|---|

## API Contract

| Endpoint | Purpose | Auth | Notes |
|---|---|---|---|

## Rules

- Controllers/routes do not contain core business logic.
- Domain/service layer owns business rules.
- Data access is centralized.
- External services go through adapters.
- Auth checks are centralized.

## Architecture Decisions

See `docs/adr/`.
```

## 7. TASKS.md 最小模板

```markdown
# Tasks

## Now

| ID | Task | Risk | Acceptance | Status |
|---|---|---|---|---|

## Next

- 

## Blocked

- 

## Done

- 
```

## 8. TESTING.md 最小模板

```markdown
# Testing

## Commands

- Typecheck:
- Lint:
- Unit:
- Integration:
- E2E:
- Build:
- Verify:

## Minimum Verification

| Change type | Required checks |
|---|---|
| UI copy/style | lint, typecheck, visual/manual check |
| Normal feature | unit/integration, typecheck, lint |
| Core flow | integration, E2E, regression |
| Auth/payment/data/migration | full verify, manual review, rollback plan |

## Manual Smoke Test

- 
```

## 9. DEPLOYMENT.md 最小模板

```markdown
# Deployment

## Environments

- Local:
- Staging:
- Production:

## Environment Variables

| Name | Required | Notes |
|---|---|---|

## Deploy Steps

1. 

## Database Migration

- 

## Rollback

- 
```

## 10. OPERATIONS.md 最小模板

```markdown
# Operations

## Logs

- App logs:
- Error logs:
- Access logs:

## Monitoring

- Availability:
- Error rate:
- Latency:
- Cost:

## Common Incidents

| Symptom | Check | Fix |
|---|---|---|

## Backup and Restore

- 
```

## 11. 使用方式

新项目启动时：

```text
1. 复制这些模板到项目根目录。
2. 先填 PRODUCT_SPEC.md 和 ARCHITECTURE.md。
3. 再生成 CLAUDE.md 和 AGENTS.md。
4. 最后补 TESTING.md、DEPLOYMENT.md、OPERATIONS.md。
5. 每次任务都从 TASKS.md 进入。
```

如果文件写了但 AI 不读，等于没有文件。必须在 `CLAUDE.md` 和 `AGENTS.md` 明确“Required Reading”。

