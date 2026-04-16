# 私有库初始化清单

这份清单适合第一次把 `ObsidianToWiki-private` 搭起来时用。

## 1. 建立私有库

创建一个私有目录或私有仓库，例如：

```text
ObsidianToWiki-private/
```

它和公开脚手架仓库分开。

## 2. 同步脚手架

从公开仓库同步这些内容过去：

- 脚本
- 模板
- 提示词
- 根入口文档
- 规则文件

## 3. 确认最小入口文件存在

至少确认这些文件存在：

- `Home.md`
- `快速开始.md`
- `使用手册.md`
- `会话启动页.md`
- `index.md`
- `log.md`
- `README.md`
- `README-zh.md`
- `AGENTS.md`
- `CLAUDE.md`

## 4. 确认最小分区存在

至少确认这些目录或索引存在：

- `01_inbox/`
- `10_personal/索引.md`
- `20_projects/索引.md`
- `30_shared/索引.md`
- `40_outputs/索引.md`

## 5. 接入第一个真实项目

运行：

```powershell
python 00_system/scripts/attach_project.py --repo-root "C:\path\to\repo" --project "demo-saas"
```

## 6. 摄入第一份真实资料

运行：

```powershell
python 00_system/scripts/ingest_source.py --source "C:\path\to\prd.docx" --title "PRD v1" --project "demo-saas"
```

## 7. 开始日常使用

从这一刻开始：

- 新资料先入库
- 项目问题优先写回项目 wiki
- 可复用经验提升到 `30_shared/`
- 每次重要变更记到 `log.md`
