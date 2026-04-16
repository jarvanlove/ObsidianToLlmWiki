# ObsidianToWiki

面向 Obsidian 的 LLM 持续维护型知识系统脚手架。

这份 README 负责讲清楚 4 件事：

1. 这套系统是干什么的
2. 架构设计是什么
3. 完整目录结构是什么
4. 每份入口文档分别负责什么

## 这套系统是干什么的

这套系统的目标不是做一次性问答，而是把：

- 原始资料
- 项目过程记忆
- 可复用经验
- 有价值的分析结论

持续沉淀成一个可长期维护的本地 wiki。

它同时服务两个方向：

- 个人长期知识
- 项目级现场记忆

## 公开仓库和私有仓库的关系

建议把系统拆成两部分：

1. `ObsidianToWiki`
   当前这个公开仓库，负责脚手架、脚本、模板、规则、文档。
2. `ObsidianToWiki-private`
   你的私有知识库，负责存放真实的个人知识、项目知识、原始资料和沉淀结果。

所以：

- 当前仓库负责“系统怎么工作”
- 私有仓库负责“你的真实内容”

它们不是自动双向同步。

当前支持的是：

- 公开脚手架同步到私有库
- 私有内容不自动回写到公开仓库

## 这套系统解决什么问题

它主要解决 4 个问题：

1. 资料收进来了，但没人持续整理
2. 项目上下文容易丢，换个会话就断
3. 有价值的问答只停留在聊天窗口
4. 一个项目里踩过的坑，另一个项目还会重踩

## 架构设计

这套系统可以理解成 3 层架构。

### 1. 输入层

这一层负责接住原始输入：

- 原始文件
- 剪藏
- 临时材料

它对应：

- `01_inbox/`
- 项目内 `sources/`
- 项目内 `source-notes/`

### 2. 记忆层

这一层负责长期沉淀结构化知识：

- `10_personal/` 个人知识
- `20_projects/` 项目知识
- `30_shared/` 共享知识
- `40_outputs/` 输出沉淀

这一层才是系统真正的“知识主体”。

### 3. 自动化层

这一层负责维护系统运转：

- 创建页面
- 摄入资料
- 接入项目
- 搜索召回
- 回写沉淀
- 体检治理
- 同步私有库

它对应：

- `00_system/scripts/`
- `00_system/templates/`
- `00_system/registry/`

整个系统的工作模型是：

- 人负责判断价值和边界
- agent 负责整理、链接、回写、维护
- Markdown 页面仍然是最终事实来源

## 完整目录结构

```text
ObsidianToWiki/
├─ .obsidian/                         Obsidian 本地配置
├─ 00_system/
│  ├─ registry/                      schema、注册表、同步清单
│  ├─ scripts/                       自动化脚本
│  └─ templates/                     页面模板
├─ 01_inbox/
│  ├─ clips/                         尚未完全沉淀的来源笔记
│  ├─ raw/                           原始资料
│  └─ scratch/                       临时材料
├─ 10_personal/
│  └─ 索引.md                         个人知识入口
├─ 20_projects/
│  ├─ active/                        进行中的项目子 wiki
│  ├─ archive/                       归档项目
│  ├─ 关系索引.md                     跨项目关系索引
│  └─ 索引.md                         项目知识入口
├─ 30_shared/
│  ├─ architectures/                 可复用架构
│  ├─ patterns/                      可复用模式
│  ├─ prompts/                       可复用提示词
│  ├─ tools/                         工具说明
│  └─ 索引.md                         共享知识入口
├─ 40_outputs/
│  ├─ analyses/                      分析沉淀
│  ├─ briefings/                     简报和摘要
│  ├─ reflections/                   学习候选和反思
│  └─ 索引.md                         输出入口
├─ 90_archive/                       低频但保留检索价值的内容
├─ docs/
│  ├─ plans/                         设计文档和背景方案
│  └─ templates/                     根入口和 bootstrap 模板
├─ AGENTS.md                         当前公开脚手架给 Codex 的规则
├─ CHANGELOG.md                      开源仓库版本记录
├─ CLAUDE.md                         当前公开脚手架给 Claude Code 的规则
├─ CONTRIBUTING.md                   开源协作说明
├─ Home.md                           人类入口页
├─ index.md                          总索引
├─ LICENSE                           开源许可证
├─ log.md                            追加式操作日志
├─ README.md                         英文说明
├─ README-zh.md                      中文说明
├─ SECURITY.md                       安全说明
├─ 会话启动页.md                      给 agent 复制用的模板
├─ 使用手册.md                        日常使用说明
└─ 快速开始.md                        第一次上手说明
```

## 各层目录分别负责什么

### `00_system/`

这是系统层，不是内容层。

主要放：

- 脚本
- 模板
- schema
- 注册表
- 同步清单

你平时主要“调用”这里，而不是往这里写知识。

### `01_inbox/`

这是输入层。

资料先收进来，再决定怎么沉淀。

### `10_personal/`

这是个人长期知识层。

适合放：

- 认知总结
- 长期方法论
- 工作流
- 个人稳定偏好

### `20_projects/`

这是项目知识层。

每个项目是一套子 wiki。

标准结构是：

```text
20_projects/active/<project-slug>/
├─ notes/
├─ source-notes/
├─ sources/
├─ project.memory.md
├─ 任务.md
├─ 关系.md
├─ 决策.md
├─ 时间线.md
├─ 架构.md
├─ 来源.md
├─ 概览.md
├─ 索引.md
└─ 风险.md
```

核心页面含义：

- `索引.md`：项目入口
- `概览.md`：项目是做什么的
- `架构.md`：系统结构
- `决策.md`：为什么这么做
- `任务.md`：当前推进什么
- `来源.md`：项目资料入口
- `project.memory.md`：给 agent 快速读取的运行记忆

### `30_shared/`

这是跨项目复用层。

一个项目里沉淀出来、其他项目也可能复用的知识，应该往这里提升。

### `40_outputs/`

这是输出沉淀层。

分析、问答、简报、复盘结果，先落在这里，再决定是否进一步提升。

### `90_archive/`

这是归档层。

低频访问，但保留检索价值的内容放这里。

## 这套系统平时怎么用

### 1. 接入项目

```powershell
python 00_system/scripts/attach_project.py --repo-root "C:\path\to\repo" --project "demo-saas"
```

作用：

- 在项目仓库生成 `wiki.context.json`、`AGENTS.md`、`CLAUDE.md`
- 在 wiki 里创建项目主干页

### 2. 摄入资料

```powershell
python 00_system/scripts/ingest_source.py --source "C:\path\to\prd.docx" --title "PRD v1" --project "demo-saas"
```

作用：

- 复制原始文件
- 生成来源笔记
- 更新日志和索引

### 3. 搜索

```powershell
python 00_system/scripts/search_wiki.py "权限 设计" --show-relations
```

### 4. 回写结论

```powershell
python 00_system/scripts/file_back_query.py --title "权限方案评估" --question "当前项目该用 RBAC 还是 ABAC？" --conclusion "先用 RBAC，保留 ABAC 扩展点。" --project "demo-saas"
```

## 任意窗口中的项目工作流

这套系统创建出来，核心就是为了让“项目在任意窗口里都能持续使用项目 wiki”，而不是只能在当前这个脚手架窗口里使用。

### 项目只接入一次

每个项目只需要正式接入一次：

```powershell
python 00_system/scripts/attach_project.py --repo-root "C:\path\to\repo" --project "demo-saas"
```

接入后，项目仓库根目录会生成：

- `wiki.context.json`
- `AGENTS.md`
- `CLAUDE.md`

这三个文件就是“项目仓库 -> 私有 wiki”的桥。

### 任意窗口如何使用项目 wiki

以后无论你从哪个窗口打开这个项目仓库，只要这个窗口能看到项目根目录，它就能通过上面的 3 个文件找到项目 wiki。

在任意项目窗口里，推荐 agent 的启动顺序是：

1. 先读项目仓库根目录的 `wiki.context.json`
2. 再读项目仓库根目录的 `AGENTS.md` 或 `CLAUDE.md`
3. 再打开项目 wiki 的：
   - `索引.md`
   - `project.memory.md`
   - `任务.md`
   - 必要时再读 `概览.md`、`架构.md`、`决策.md`、`来源.md`

### 开发过程中怎么持续积累知识

项目开发时，不要把“知识积累”理解成额外工作，而是把它理解成任务完成后的固定回写动作。

推荐工作方式：

1. 做任务前
   先读 `project.memory.md` 和 `任务.md`，知道当前上下文。
2. 做任务时
   如果遇到新资料、设计约束、架构说明、会议纪要，先摄入到项目来源层。
3. 做任务后
   把稳定结论写回项目 wiki，而不是只停留在聊天窗口或 commit 里。

对应的回写原则：

- 项目定位变化，更新 `概览.md`
- 系统结构变化，更新 `架构.md`
- 为什么这么做，更新 `决策.md`
- 当前推进状态，更新 `任务.md`
- 新资料和外部文档，进入 `来源.md` 和 `source-notes/`
- 临时分析但以后还会用，进入 `notes/` 或 `40_outputs/`
- 可跨项目复用的内容，提升到 `30_shared/`

### 项目窗口中的标准指令

如果你在任意项目窗口中想让 agent 正确使用项目 wiki，可以直接这样说：

```text
请按当前项目的 wiki 规则工作。

开始前先读：
1. 项目仓库根目录的 wiki.context.json
2. 项目仓库根目录的 AGENTS.md 或 CLAUDE.md
3. 对应项目 wiki 的 索引.md、project.memory.md、任务.md

要求：
- 完成当前任务
- 如有新资料，先摄入来源
- 如有稳定结论，写回项目 wiki
- 如有可复用内容，提升到共享层
```

### 项目 wiki 到底怎么用

项目 wiki 不是“项目文档备份区”，而是项目的长期记忆层。

它主要承担 4 个作用：

1. 让任意新窗口快速恢复上下文
2. 让设计决策和架构认知不只停留在代码里
3. 让资料、分析、任务、风险有统一入口
4. 让项目经验可以持续提升到共享层

一句话说：

- 代码仓库负责交付物
- 项目 wiki 负责记忆、解释、回写和复盘

## 旧知识库迁移策略

如果你以前已经在别的 Obsidian 或第二大脑里为某个项目写过笔记，例如：

- `C:\Work\note\ObsidianNoteBook\记忆库\语义记忆\ResearchClaw`

那么不要手工复制粘贴到新系统里。

正确做法是：

1. 把旧笔记当作项目来源材料
2. 优先选择高价值文档逐个摄入
3. 再把真正稳定的内容整理进当前项目 wiki 主干页

建议优先迁移的内容：

- 项目工作页
- 架构图与系统拓扑说明
- 功能实现总结
- 设计方案
- 来源页 / 任务页

也就是说，旧第二大脑不是废掉，而是作为“历史来源层”进入新系统。

## 顶层文档之间是什么关系

- `README.md` / `README-zh.md`
  负责讲系统全貌、架构设计、目录结构、运行方式。
- `Home.md`
  负责导航入口。
- `快速开始.md`
  负责第一次上手。
- `使用手册.md`
  负责日常操作说明。
- `会话启动页.md`
  负责给 agent 直接复制使用的模板。
- `index.md`
  负责导航，不承担完整说明职责。

## 私有库如何同步

先预览：

```powershell
python 00_system/scripts/sync_private_vault.py --dry-run
```

确认无误后执行：

```powershell
python 00_system/scripts/sync_private_vault.py
```

## 方法论来源

这套系统参考了 Andrej Karpathy 提出的 `llm-wiki` 思路，并结合了当前仓库自己的项目记忆、回写沉淀和本地脚手架实现。

- Karpathy 原文：https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
