---
title: Personal Knowledge Routing Design
status: draft
updated: 2026-04-22
summary: 解决项目实施过程中产生的高价值知识，如何自然沉淀到个人层而不是默认只回到项目层。
---

# Personal Knowledge Routing Design

## 1. Problem

当前系统对“项目知识”路径已经比较清晰，但真实使用里还有另一类场景：

- 用户在某个项目里干活
- 中途产生了一条长期有效的认知、方法、经验或偏好
- 这条知识更适合进入个人层
- 但当前系统默认把它继续写回项目层

于是用户就只能：

1. 退出当前项目流
2. 单独打开私有 wiki
3. 再手动沉淀成个人知识

这会让体验变得割裂。

## 2. Root Cause

当前系统的默认假设是：

- 当前在哪个项目窗口
- 当前知识就优先属于哪个项目

这个假设对“项目事实”成立，但对“项目过程中顺手产生的个人知识”不成立。

当前缺失的是：

- 明确的知识目的地模型
- 项目层到个人层的流转规则
- 用户可以直接表达“这条沉淀为个人知识”的自然语言语义

## 3. Design Goal

目标是让系统具备一个清晰的分流框架：

- 项目层
- 个人层
- 共享层
- outputs

并允许用户在项目上下文中直接触发其中任意一层。

## 4. Target Design

## 4.1 Introduce destination-aware write-back

后续所有沉淀动作都应带一个隐含问题：

这条知识应该写到哪里？

建议标准目的地为四类：

1. `project`
2. `personal`
3. `shared`
4. `outputs`

## 4.2 Personal routing must be allowed inside project context

系统必须支持下面这类表达：

- `把这条沉淀成个人知识`
- `这不是项目事实，记到个人知识库`
- `把这个方法总结进我的个人 wiki`

项目窗口只是当前上下文，不是最终知识目的地。

## 4.3 Keep backlinks to the originating project

即使一条知识最终进入个人层，也不代表它要和当前项目断开。

更合理的方式是：

- 个人知识页记录来源项目
- 当前项目页保留回链

## 4.4 Routing rules

### Write to `project`

当内容是：

- 当前项目特有决策
- 当前项目任务状态
- 当前项目架构事实
- 当前项目来源材料

### Write to `personal`

当内容是：

- 用户长期有效的方法
- 用户个人工作流
- 用户长期偏好
- 对多个项目都适用但更偏个人实践的总结

### Write to `shared`

当内容是：

- 明确跨项目复用
- 可抽象成模式、架构、提示词、工具经验

### Write to `outputs`

当内容是：

- 阶段性分析
- 临时问答
- 还没完全成熟但值得保留

## 5. Recommended Decisions

### Decision A

项目上下文不应锁定最终目的地。

### Decision B

个人知识沉淀必须保留来源项目回链。

### Decision C

知识目的地应该成为正式模型，而不是靠临时语言猜测。

## 6. P0 Recommendation

这件事也应该进入 P0 设计，不应延后。

P0 目标：

- 定义四类写回目的地
- 允许在项目窗口中显式写到个人层
- 保留项目回链

## 7. Success Criteria

成功标准是：

1. 用户在项目窗口里能直接说“沉淀成个人知识”
2. 系统不会再默认把所有高价值内容都塞回项目层
3. 个人知识页和来源项目之间能保持可追溯关系
