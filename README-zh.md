# ObsidianToWiki

面向 Obsidian 的 LLM 持续维护型个人与项目知识库脚手架。

英文版见 [README.md](README.md)。

## 这是什么

ObsidianToWiki 的目标不是做一次性问答，而是让 LLM 把原始资料逐步整理成一个持续维护的 Wiki。

它服务两类知识：

- 个人长期知识
- 项目级现场记忆

核心分层是：

- 原始资料层
- Wiki 页面层
- Agent 规则与自动化层

## 目录结构

```text
ObsidianToWiki/
├─ 00_system/
│  ├─ scripts/     Python 核心逻辑 + `.ps1` / `.sh` 包装脚本
│  └─ templates/   页面模板
├─ 01_inbox/
│  ├─ raw/         原始资料
│  ├─ clips/       收集箱来源笔记
│  └─ scratch/     临时工作材料
├─ 10_personal/
│  ├─ areas/       长期领域
│  ├─ concepts/    概念
│  ├─ entities/    实体
│  ├─ syntheses/   综合整理页
│  └─ 索引.md
├─ 20_projects/
│  ├─ active/      进行中的项目
│  │  └─ <project>/
│  │     ├─ notes/
│  │     ├─ source-notes/
│  │     ├─ sources/
│  │     ├─ 概览.md
│  │     ├─ 架构.md
│  │     ├─ 决策.md
│  │     ├─ 经验.md
│  │     ├─ 来源.md
│  │     ├─ 任务.md
│  │     └─ 索引.md
│  ├─ archive/     已归档项目
│  │  └─ <project>/...
│  └─ 索引.md
├─ 30_shared/
│  ├─ architectures/  可复用架构
│  ├─ patterns/       可复用模式
│  ├─ prompts/        可复用提示词
│  ├─ tools/          工具记录
│  └─ 索引.md
├─ 40_outputs/
│  ├─ analyses/      分析结果
│  ├─ briefings/     简报与摘要
│  └─ 索引.md
├─ 90_archive/       归档
├─ Home.md         人工入口页
├─ index.md        总索引
├─ log.md          操作日志
├─ AGENTS.md       Codex 规则
├─ CLAUDE.md       Claude Code 规则
├─ README.md       英文开源首页
├─ README-zh.md    中文说明
├─ 使用手册.md     日常使用说明
└─ 会话启动页.md   可直接复制给 Agent 的会话模板
```

## 为什么目录改成英文

如果仓库要开源，英文路径更稳定：

- GitHub 上更容易理解
- 不依赖中文文件系统习惯
- 脚本路径在多平台环境里更统一
- 其他人 fork 或协作时摩擦更小

## 改成英文后会不会更难用

不会，前提是区分“磁盘路径”和“阅读界面”。

这套仓库的处理方式是：

- 磁盘目录、脚本名、仓库结构用英文
- 页面标题继续可以用中文
- 页面正文继续可以用中文
- Obsidian 链接显示名继续可以用中文

也就是说：

- GitHub 看到的是干净的英文结构
- 你在 Obsidian 里看到的仍然是中文知识网络

真正需要记住的英文路径其实很少，主要只有：

- `00_system/scripts/`
- `01_inbox/raw/`
- `20_projects/active/`
- `30_shared/prompts/`

项目内部真正需要记住的，也只有这几类：

- `notes/`
- `source-notes/`
- `sources/`
- `概览.md`、`架构.md`、`决策.md`、`经验.md`、`来源.md`、`任务.md`、`索引.md`

日常大多数时候你不直接敲路径，而是从 `Home.md`、`index.md` 和 `会话启动页.md` 进入。

## 项目页面应该怎么互链

新项目建起来后，建议先把这几页连成一个小闭环：

- `索引.md` 作为项目入口和目录
- `概览.md` 作为项目总览
- `架构.md` 作为系统结构说明
- `决策.md` 作为关键决策记录
- `任务.md` 作为推进跟踪
- `来源.md` 作为原始资料登记

推荐的最小互链方式是：

- `索引.md` 链向 `概览`、`架构`、`决策`、`任务`、`来源`
- `概览.md` 链向 `架构`、`决策`、`任务`、`来源`
- `架构.md` 链向 `概览`、`决策`、`来源`
- `决策.md` 链向 `概览`、`架构`、`来源`
- `任务.md` 链向 `概览`、`决策`、`来源`
- `来源.md` 链向 `索引`，必要时再链向 `概览` 或 `架构`

这样做的目的不是“链接越多越好”，而是让你从任意一页都能顺着链接回到项目主干，不会陷在孤立页面里。

## 怎么让 Agent 自动找到 wiki

你担心的点是对的：如果每次都要手工提醒，wiki 就只是“辅助笔记”，还不是“项目记忆系统”。

正确做法是两层：

1. 在每个项目工作区放一个最小 bootstrap。
2. 让 agent 在任务开始时自动读取这个 bootstrap，再去打开中心 wiki。

bootstrap 至少要声明这些信息：

- `wiki_root`
- `project_slug`
- `project_index`
- `project_overview`
- `project_tasks`

这样一来，Codex / Claude Code 不需要你每次都口头提醒“记得用 wiki”，它们只要按工作区规则启动，就会自己找到对应项目页。

如果你愿意，我已经把标准模板整理成：

- `30_shared/prompts/项目接入提示词.md`

这个模板就是以后复制到新项目工作区的起点。

## 这套系统当前已经完成什么

已经完成：

- Obsidian 可直接打开的 vault 结构
- Codex / Claude Code 双入口规则
- 资料摄入
- 页面创建
- 搜索
- 索引重建
- 体检
- 项目子 wiki 脚手架
- Windows 与 macOS/Linux 包装脚本

还需要靠真实使用持续积累的部分：

- 真实资料摄入
- 真实项目沉淀
- 共享层知识回流

## 推荐入口

- `Home.md`
- `使用手册.md`
- `会话启动页.md`

## 开源注意事项

不要提交：

- 私人资料
- 本机绝对路径
- 本地缓存数据库
- 个人使用过程中生成的噪音日志

许可证：MIT。
