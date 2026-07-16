# 私有库初始化验收清单

初始化由公开仓库根安装器自动执行。这份清单用于验收，不要求用户逐项手工创建。

## 系统验收

- 仓库内 `.venv` 存在并安装核心依赖
- 用户级配置记录真实私有库位置
- `00_system/registry/vault_state.json` 与 `private_scaffold_state.json` 存在
- `runtime_update_receipt.json` 记录本次 setup
- 所选 Provider 下安装 `obsidiantowiki-manager` Skill
- 严格 doctor 通过

## 私有库验收

- `Home.md`、`index.md`、`log.md`、`README-zh.md` 存在
- `AGENTS.md` / `CLAUDE.md` 是私有库入口，不是公开项目入口副本
- `wiki.private.json` 存在且格式有效
- `01_inbox/`、`10_personal/`、`20_projects/`、`30_shared/`、`40_outputs/`、`90_archive/` 存在
- 私有知识目录不在公开同步托管范围

## 首次真实使用

1. 在一个真实项目里说 `开始工作`
2. 确认项目自动接入并通过严格检查
3. 摄入一份真实资料
4. 长文档应生成文档地图、章节索引、来源定位和质量状态；`review` 或 `blocked` 不得直接提升为正式知识页
