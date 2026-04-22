---
title: User Wiki Discovery Design
status: draft
updated: 2026-04-22
summary: 解决首次接入新项目时，不同 agent 无法自动发现用户私有 wiki 位置的问题。
---

# User Wiki Discovery Design

## 1. Problem

当前系统已经具备项目级接入协议：

- `wiki.context.json`
- `AGENTS.md`
- `CLAUDE.md`

但这套协议只在“项目已经接入之后”有效。

真实使用里暴露的问题是：

- 用户在一个尚未接入的新项目窗口里说“帮我接入 wiki”
- Claude Code CLI、Codex CLI、Cursor、Trae 等并不知道用户私有 wiki 在哪里
- 用户仍然需要再补一句“我的私有 wiki 在什么位置”

这意味着当前自动化只做到：

- 已接入项目：半自动
- 未接入项目：仍依赖人工告诉私有 wiki 路径

## 2. Root Cause

根因不是项目协议失效，而是系统缺少“用户级发现层”。

当前系统有：

- 项目级配置

当前系统没有：

- 用户级默认 wiki 根配置
- 标准发现顺序
- 首次接入的统一判定机制

## 3. Design Goal

目标不是让开源仓库预知每个用户的本地路径，而是让系统形成稳定的发现顺序：

1. 优先读用户级配置
2. 再尝试标准约定位置
3. 找不到时，再进入一次性人工确认
4. 一旦确认，就长期复用

换句话说，目标是把“每次人工说明路径”变成“第一次说明一次，后面自动发现”。

## 4. Target Design

## 4.1 Add a user-level config layer

新增“用户级 wiki 配置文件”概念。

建议名称：

- `user.wiki.context.json`
  或
- `.obsidiantowiki.json`

这个文件不属于项目仓库，而属于用户环境。

建议记录：

- `default_wiki_root`
- `default_private_vault_name`
- `known_wiki_roots`
- `preferred_project_area`

## 4.2 Standard discovery order

首次接入新项目时，agent 应按这个顺序找私有 wiki：

1. 当前环境中的用户级配置文件
2. 当前公开脚手架同级目录下的 `ObsidianToWiki-private`
3. 常见默认命名的私有库目录
4. 用户上次成功使用过的私有 wiki 路径
5. 如果都失败，再请求用户明确提供一次

## 4.3 First attach becomes guided, not fully blind

要接受一个现实：

开源系统不可能天然知道每个用户的私有 wiki 在哪里。

所以“完全零输入自动化”在首次使用时并不现实。

正确目标应该是：

- 第一次：引导式自动化
- 之后：稳定自动化

## 4.4 Persist discovery result

一旦用户确认了私有 wiki 路径，系统应把结果写入用户级配置层，而不是只存在一次对话里。

这样后续：

- 新项目首次接入
- 新窗口打开老项目
- 新 agent 接入同一用户环境

都可以复用这条信息。

## 5. Recommended Decisions

### Decision A

用户级发现层必须独立于项目级协议存在。

### Decision B

首次接入不追求绝对零输入，而追求“一次确认，长期复用”。

### Decision C

发现机制必须是跨 agent 的。

## 6. P0 Recommendation

如果后续实现，这件事应进入 P0，而不是拖后。

P0 目标：

- 定义用户级配置文件格式
- 定义标准发现顺序
- 首次成功接入后，将结果写入用户级配置

## 7. Success Criteria

成功标准是：

1. 新用户首次接入时，不需要每次重新说明私有 wiki 路径
2. 同一用户在不同项目窗口里，都能复用已知私有 wiki 位置
3. 不同 agent 可以围绕同一发现协议工作
