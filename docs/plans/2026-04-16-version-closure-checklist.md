# Version Closure Checklist

## Goal

把当前一轮连续迭代形成的能力收口为一个可提交、可同步、可继续演进的版本快照。

## Implemented

- 项目快速接入协议与 `wiki.context.json`
- 项目主干页扩展：关系 / 风险 / 时间线 / 运行记忆
- 正式 YAML frontmatter 解析
- schema 校验与治理体检
- 来源状态机：`derived_pages` / `recommended_targets`
- 来源自动回填与来源提升推荐
- 项目关系同步与全局关系索引
- 查询回写脚本
- 学习候选记录、自动发现、候选升级
- 检索排序增强与项目关系增强检索
- 私有 vault 同步脚本与 manifest 分类同步

## Before Commit

- 检查公开仓库 `git status`
- 检查私有仓库 `git status`
- 确认 `40_outputs/analyses/知识库体检-日期.md` 是否应纳入版本
- 确认 `40_outputs/reflections/` 当前是否为空或是否包含应保留候选
- 决定是否要把私有 vault 的脚手架同步结果也单独提交

## Suggested Commit Groups

1. Core scripts and templates  
   `00_system/scripts/`  
   `00_system/templates/`  
   `00_system/registry/`

2. Docs and prompts  
   `README*.md`  
   `使用手册.md`  
   `docs/`  
   `30_shared/prompts/`

3. Generated indexes and reports  
   `index.md`  
   `10_personal/索引.md`  
   `20_projects/索引.md`  
   `20_projects/关系索引.md`  
   `30_shared/索引.md`  
   `40_outputs/索引.md`  
   `40_outputs/analyses/知识库体检-*.md`

## Open Decisions

- 是否将自动生成的体检报告长期纳入版本控制
- 是否让私有 vault 同步脚本默认只做 `--dry-run`
- 是否为候选池引入成熟度阈值，低分候选默认不写盘
