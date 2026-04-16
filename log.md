# 日志

## [2026-04-16T13:19:31] 更新 | 补充方法论来源并新增 v2 设计文档

- actor: agent
- details: 更新 README.md、README-zh.md，并新增 docs/plans/2026-04-16-obsidiantowiki-v2-design.md，纳入 llm-wiki 与 Hermes Agent 的改造设计。

## [2026-04-16T13:26:22] 更新 | 新增项目快速接入协议与跨项目主干页

- actor: agent
- details: 新增 attach_project 脚本、wiki.context.json、projects.json 注册表，并扩展项目骨架到关系/风险/时间线页面。

## [2026-04-16T13:32:00] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T13:32:41] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T13:32:52] 更新 | 新增 schema 校验与治理体检

- actor: agent
- details: wiki_lib 改为 YAML frontmatter 解析，新增 page_schemas.json 和 schema_lib.py，并扩展 lint_wiki.py 到 schema/死链/重复标题/未沉淀来源检查。

## [2026-04-16T13:40:36] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T13:40:46] 更新 | 来源状态机与私有 vault 默认接入

- actor: agent
- details: attach_project 默认优先接入同级 ObsidianToWiki-private；来源笔记新增 source_hash、ingest_status、derived_pages、review_due，并接入 schema 与治理检查。

## [2026-04-16T13:45:09] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T13:45:20] 更新 | 新增来源自动回填与项目运行记忆页

- actor: agent
- details: 新增 sync_source_notes.py 自动回填来源 derived_pages/ingest_status；项目骨架与接入协议新增 project.memory.md。

## [2026-04-16T13:52:48] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T13:52:59] 更新 | 新增跨项目关系索引与查询回写脚本

- actor: agent
- details: 项目索引 frontmatter 新增 depends_on/reuses/produces/related_to，自动生成 20_projects/关系索引.md，并新增 file_back_query.py 供问答结果沉淀回 wiki。

## [2026-04-16T13:57:03] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T13:57:18] 更新 | 新增项目关系同步与学习候选池

- actor: agent
- details: 新增 sync_project_relations.py 把关系.md 同步回项目索引 frontmatter；新增 40_outputs/reflections 与 record_learning_candidate.py 记录可审查的学习候选。

## [2026-04-16T14:01:49] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T14:02:01] 更新 | 新增关系增强检索与候选升级脚本

- actor: agent
- details: search_wiki.py 支持 --show-relations 输出项目依赖/复用/运行记忆；新增 promote_learning_candidate.py 将 reflection 候选提升到共享页或正式分析页。

## [2026-04-16T14:04:59] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T14:05:30] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T14:06:01] 更新 | 新增自动候选发现与检索排序增强

- actor: agent
- details: search_wiki 增加 status/updated/reflection 权重和 --show-relations 项目关系补充；新增 discover_learning_candidates.py 从体检报告与日志中自动发现学习候选。

## [2026-04-16T14:08:19] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T14:08:59] 更新 | 新增私有 vault 同步脚本与内容型候选发现

- actor: agent
- details: 新增 sync_private_vault.py 以显式清单同步脚手架层到 ObsidianToWiki-private；discover_learning_candidates.py 增加高频标签但共享层缺页的候选发现。

## [2026-04-16T14:11:29] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T14:11:41] 更新 | 执行私有 vault 同步并增强主题候选发现

- actor: agent
- details: 已实际执行 sync_private_vault.py 同步脚手架到 ObsidianToWiki-private；discover_learning_candidates.py 新增相似主题聚类发现逻辑。

## [2026-04-16T14:18:29] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T14:18:39] 更新 | 增强关系抽取与私有库精细同步

- actor: agent
- details: sync_project_relations.py 现在会扫描 关系/架构/决策/project.memory 页面；sync_private_vault.py 改为 manifest 驱动并支持 --only 分类同步。

## [2026-04-16T14:21:53] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T14:22:04] 更新 | 新增来源提升推荐与正文级主题发现

- actor: agent
- details: 来源页新增 recommended_targets，并接入 recommend_source_promotions.py；discover_learning_candidates.py 改为包含正文片段 token 的相似主题发现。

## [2026-04-16T14:24:46] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T14:24:56] 更新 | 新增候选评分去重与版本收口清单

- actor: agent
- details: 反思页新增 candidate_score/signature/source/promoted_to；discover_learning_candidates.py 改为按 signature 去重并写入候选分数，同时新增 docs/plans/2026-04-16-version-closure-checklist.md。

## [2026-04-16T14:26:40] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T14:26:54] 更新 | 新增候选阈值与版本状态报告

- actor: agent
- details: discover_learning_candidates.py 支持 --min-score；新增 version_status.py 生成公开仓库与私有 vault 的版本状态报告。

## [2026-04-16T14:37:27] 体检 | 知识库体检

- actor: agent
- details: 报告已写入 40_outputs/analyses/知识库体检-2026-04-16.md

## [2026-04-16T14:37:55] 更新 | 补正文义关系抽取并生成收官分组报告

- actor: agent
- details: sync_project_relations.py 增加句子级关键词推断；新增 version_closure_report.py 生成按 core/docs/generated/other 分组的收官报告。

