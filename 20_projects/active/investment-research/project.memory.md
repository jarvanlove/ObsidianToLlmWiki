---
title: investment-research 运行记忆
type: 项目运行记忆
domain: 项目
project: investment-research
status: 活跃
tags: [investment, research]
updated: 2026-06-22
summary: investment-research 的会话启动摘要与运行态记忆。
---

# investment-research 运行记忆

## 当前目标

- v4 方向已获老板确认：第一阶段聚焦半导体全产业链，以设备、材料、设计、制造、封测为主框架，先用材料国产替代、专题深度研究、上市公司完整版投研报告和高管校友图谱做样板；以内容质量、数据准确度、判断精准性、图表可校验、履历可溯源和专家审稿为核心壁垒；商业化分为知识星球收益、ToC 会员/定制化、ToB 产品/SaaS/定制输出三类；半导体跑通后再复制到其它行业。

## 当前风险

- 当前只有原始 Word 文档登记，尚未解析正文或建立结构化研究笔记。
- 老板需求仍处于口头模糊阶段：上市公司投研系统、创业项目评价系统、知识星球内容生意、付费服务和 SaaS 可能是不同产品，不能直接混成一个大系统。
- 深度报告质量不能依赖智能体自动完成，必须建立行业专家审稿、数据来源核验和图表口径管理机制。
- PRD_v2 已形成并获得老板认可；工程计划已拆为总纲、公共契约和 Slice 工程说明书，但不能直接进入大而全 SaaS，应先做内部研究内容工作台 MVP。
- 技术口径已明确：核心业务模型、报告资产、数据溯源、图表校验和审稿流由自研系统承载，智能体工作流采用 code-first 方式接入。
- 当前工程执行口径：`docs/product/02-planning/半导体智能研究与服务平台_垂直切片开发计划.md` 是轻量总纲；`docs/product/02-planning/contracts/` 承载数据模型、API、页面交互、权限安全、AI 工作流、种子数据和数据源评估等公共契约；`docs/product/02-planning/slices/` 承载每个垂直切片的可执行工程说明书。后续 AI 应按“总纲 -> 相关公共契约 -> 当前 Slice -> PRD/汇报背景”的顺序读取，避免单文件过大导致遗漏。
- `PRODUCT_SPEC.md`、`ARCHITECTURE.md`、`TESTING.md`、`SECURITY.md` 已从 TODO 空壳更新为当前项目基准；后续仍需在技术栈确认后补入真实 install/lint/test/build/migration/seed 命令。
- GitHub private 仓库已通过 SSH 成功 push；当前远端为 `git@github.com:jarvanlove/investment-research.git`。原始资料、归档、第三方截图、老板内部材料、Token、付费数据和本地 Wiki 上下文默认不得公开。
- 技术栈方向已确认：Next.js + TypeScript + Tailwind + shadcn/ui + TanStack Table + ECharts；FastAPI + Pydantic + SQLAlchemy + Alembic；PostgreSQL + pgvector；MinIO；Redis 可用但 MVP 不强制引入复杂队列；AI 采用自研 Provider Adapter，不默认接入 Dify。
- 数据/API 策略已确认：开发阶段采用“手工种子数据 -> 免费/公开数据源 -> 后续付费 API 替换”的三层策略，暂不购买数据 API。
- 开发约定已确认：PostgreSQL schema `investment_research`，前端端口 `3001`，后端端口 `8002`，MinIO bucket `investment-research`，Redis DB `0`，前端包管理 `pnpm`，Python 管理 `uv`，后端检查 `ruff + mypy + pytest`，前端检查 `eslint + prettier + tsc`，首个管理员邮箱 `jarvanlovehhz@gmail.com`。
- Slice 0 范围已确认：只做工程脚手架、登录、Dashboard、导航、health API；不做资料库、报告、图表、审稿、AI 或数据源。AI Slice 0-5 关闭，Slice 6 再接入。
- AI 前端设计工作流已确认：正式设计/实现前端页面时，AI 主用 `product-design:index`，次用 `design-taste-frontend`；这两个是后续 AI 前端设计/页面开发用的 skill/工作方法，不是前端运行时依赖，不写入 `package.json`。页面中不允许 emoji 图标，统一使用 Lucide 图标。
- Slice 0 开发前准备已进一步细化：根目录 README 已重写为项目入口，新增 `docs/product/02-planning/slices/Slice_0_开发执行计划.md`，明确 monorepo 目录、`.env.example`、后端、前端、数据库迁移、seed、测试和验收顺序；`scripts/` 空目录通过 `.gitkeep` 保留。
- Slice 0 已完成基础代码开发：FastAPI 后端、Next.js 前端、健康检查、真实登录、退出登录、当前用户、受保护 Dashboard、左侧导航、简体中文/英文 i18n、Lucide 图标、Alembic 迁移和首个管理员种子脚本均已落地。
- Slice 0 认证策略：密码使用 Argon2 哈希；登录后签发 JWT 并写入 HttpOnly Cookie；本地开发建议前后端都使用 `127.0.0.1`，避免 Cookie host 不一致；不在前端 `localStorage` 保存访问令牌。
- Slice 0 数据库策略：Alembic 显式创建 `investment_research` schema，并将 `alembic_version`、`roles`、`users` 放入该 schema；运行时 SQLAlchemy 通过 Postgres `search_path` 使用该 schema；测试环境用 SQLite 覆盖 DB session。
- Slice 0 验证结果：`uv run ruff check .`、`uv run mypy .`、`uv run pytest`、`pnpm lint`、`pnpm typecheck`、`pnpm --filter @investment-research/web format`、`pnpm build` 均已通过；本地 PG 迁移和管理员种子已用环境变量凭据跑通。
- Slice 0 后续核查暴露测试策略不足：仅靠 pytest/lint/build 不够，必须增加真实 HTTP、真实 PostgreSQL、真实浏览器和控制台验证。已新增 `docs/product/02-planning/contracts/08_测试与验收契约.md` 作为跨 Slice 测试验收契约。
- `/login` 页面出现的 React hydration warning 中包含 `cz-shortcut-listen="true"`，无插件 Chrome 复测未复现，判断为浏览器插件注入属性导致的开发环境 warning，不是项目代码属性。
- Slice 0 已完成收尾验收：登录页、Dashboard、导航、health API、真实 PostgreSQL 迁移/seed、真实 HTTP auth、双 host 浏览器 smoke、未登录重定向、错误密码提示、控制台和 hydration 检查均已通过。
- 本地登录 host 规则已明确：用户可使用 `localhost:3001` 或 `127.0.0.1:3001`，前端会自动把 API host 对齐当前页面 host，避免 HttpOnly Cookie 写到另一个 loopback host 后导致 Dashboard RSC 请求 307 回登录页。
- 登录页已完成一次主题化视觉微调：右侧空白文案区替换为半导体芯片/硅片主题互动视觉，密码默认填充本地开发密码但保持隐藏，并提供显示/隐藏按钮；无 emoji 图标。
- 后续模块完成标准：静态检查、单元/API、真实 DB、真实 HTTP、无插件浏览器 QA、权限/负向路径、数据质量和文档回写必须按模块涉及范围执行。
- Slice 1 开发前执行计划已形成：`docs/product/02-planning/slices/Slice_1_开发执行计划.md` 明确资料库/来源台账的 Source、SourceFile、SourceTag 数据库模型、MinIO 存储边界、API、页面、权限、种子样本、负向用例、真实 PostgreSQL/HTTP/浏览器验收和文档回写要求。后续如用户确认进入代码开发，应从该计划开始，不直接从高层 Slice 描述开工。
- Slice 1 已完成首版实现并通过本地验收：新增 Source Library 资料列表、资料详情、来源台账 API、`sources/source_files/source_tags` 表、MinIO 文件上传、来源等级、版权风险、提取状态占位、双 host 浏览器 smoke 和移动宽度 smoke。Slice 1 不包含 OCR、AI 摘要、自动版权判断、报告、图表、产业链或高管图谱。
- 本机 Playwright 已可通过 `C:\Users\jarvan_iv\.agents\skills\gstack\node_modules` 复用；后续浏览器 QA 不要重复搜索或重新安装。使用 `node_repl` 时先 `js_add_node_module_dir` 加该路径，再 `await import("playwright")`；如 bundled browser 缺失，使用系统 Chrome `C:\Program Files\Google\Chrome\Application\chrome.exe` 并加 `--disable-extensions`。
- Slice 2 已完成产业链/公司/指标基础库首版实现：新增 IndustryNode、Company、CompanyIndustryNode、Metric、MetricSource 数据模型、Alembic 迁移、API、服务层、权限规则、种子脚本、前端 `/industry`、`/companies`、`/metrics` 页面、详情页、i18n 和导航保护。
- Slice 2 验收结果：后端 `ruff/mypy/pytest` 通过，前端 `format/lint/typecheck/build` 通过，真实 PostgreSQL 迁移和 seed 通过，真实 HTTP smoke 通过，无插件 Chrome 双 host 浏览器 smoke 通过。种子数据当前为 42 个产业链节点、10 家公司、20 个指标。
- Slice 2 本地环境注意事项：本机 `8002` 端口出现 Windows 旧监听/僵尸进程状态，导致旧服务仍返回错误；已用干净后端 `8003` 完成验证，并临时在本地 ignored `.env` 指向 `127.0.0.1:8003`。后续若坚持恢复 `8002`，优先重启本机或清理旧监听后再改回 `.env`。
- Slice 2A 开发执行计划已形成：`docs/product/02-planning/slices/Slice_2A_开发执行计划.md` 已拆清高管、任职、学校、教育履历、分支机构、产品技术和校友图谱快照的数据库、API、页面、权限、种子数据、合规边界、测试和验收。后续代码开发应从该计划启动。
- 高管校友图谱数据存在准确性和合规风险：学校、专业、学历、学位等字段通常来自简历文本解析，需要来源原文、置信度、人工校验和合法授权边界。
- Slice 2A 已完成首版实现并通过本地分层验收：新增高管、学校、教育履历、任职、公司分支/产品技术和校友快照相关表；实现高管、学校、教育核验、公司高管、学校校友和校友图谱 API；实现 `/executives`、`/executives/[id]`、`/universities`、`/universities/[id]/alumni`、`/companies/[id]/executives`、`/alumni-graph` 页面。
- Slice 2A 种子数据按用户确认采用计划中的 5 家样板公司和 10 所学校；开发阶段高管样本使用“样板高管”占位，不冒充真实公开高管事实。真实数据后续必须通过公开披露/授权数据源、来源原文、置信度和人工校验进入系统。
- Slice 2A 验收结果：后端 `ruff/mypy/pytest` 通过，前端 `format/lint/typecheck/build` 通过，PostgreSQL 迁移和 seed 通过，真实 HTTP smoke 返回 20 个高管、10 所学校、33 个图谱节点、40 条关系边，系统 Chrome + Playwright 浏览器 smoke 通过且无控制台错误。
- Slice 2A 真实数据策略已明确：先不做全网爬虫，先按 `docs/product/02-planning/slices/Slice_2A_真实数据采集与导入计划.md` 从 2 家公司官方披露中人工整理小样本，使用 `docs/product/03-templates/import/` 下的 CSV 模板验证字段，再决定是否开发导入功能。
- 高管真实数据第一轮建议范围：北方华创 + 中微公司，每家公司 5-8 名核心高管；来源优先使用巨潮资讯年报/公告、交易所公告、公司官网和年报 PDF；教育履历默认 pending，人工核验后才能 verified。
- Slice 9 已完成数据源/API 接入增强：新增 `data_source_providers`、`external_metric_mappings`、`data_sync_jobs`、`data_sync_logs`，实现 `/data-sources`、`/data-sync-jobs/[id]`、连接测试、`metric_preview` 同步预览和人工确认入库。
- Slice 9 数据源安全边界：接口不回显 `api_key_ref`，只返回 `has_api_key_ref`；当前只启用开发期 mock 适配器，非 mock 数据源只做登记和密钥引用配置检查，不做真实付费 API 调用；确认入库写入 Source、pending Metric 和 MetricSource，不覆盖 confirmed 人工数据。
- Slice 9 验收结果：后端 `ruff/mypy/pytest` 通过，pytest 为 51 tests；前端 `lint/typecheck/build` 通过；Alembic 应用 `0012_data_sources`；真实 HTTP smoke 和 Playwright 无插件浏览器 smoke 均通过。
- 本轮修复一个浏览器真实联调发现的问题：`CORS_ORIGINS` 支持 JSON 数组字符串和逗号分隔字符串；命令行 HTTP 测试不能替代浏览器 CORS smoke。
- Slice 10 已完成样板报告闭环：新增只读聚合 API `/api/sample-closures` 和 `/api/sample-closures/{sample_key}`，新增 `/sample-closures` 总览和详情页，覆盖行业总览、材料国产替代、光刻胶专题、上市公司完整版投研和高管校友图谱 5 类样板。
- Slice 10 数据边界：不新增新的业务主数据表，只聚合报告、资料、指标、图表、审稿、AI run、内容计划、公司深度和高管校友数据；`seed_slice10.py` 是开发演示种子，不能视为已核验真实投资事实。
- Slice 10 验收结果：后端 `ruff/mypy/pytest` 通过，pytest 为 55 tests；前端 `lint/typecheck/build` 通过；Alembic head、`seed_slice10`、真实 HTTP 和无插件 Chrome 浏览器 smoke 均通过。真实 HTTP 中 5 个样板均为 100%，`ready_samples=5`，`average_completion=100`。
- Slice 0-10 阶段收口评审已完成：当前系统可以演示内部研究工作台主链路，但不能宣称为正式投研产品、完整真实数据库或可直接对外交付的研报系统。下一阶段建议顺序是演示稳定化包、第一份真实样板报告、报告导出与图表资产化。
- 2026-06-21 已完成 P1 研究工作台化改造：Dashboard、报告生产和公司研究已从对象管理页面升级为研究任务驱动的工作台主线。
- 2026-06-22 已完成 P2 第一份真实样板报告选题确认：新增 `docs/product/02-planning/P2_第一份真实样板报告选题确认.md`，用户已确认第一份真实样板选择 `北方华创完整版投研分析 v0.1`。该选题用于验证上市公司完整版投研报告主链路，覆盖资料、公司、指标、图表、报告、AI、审稿、导出边界和样板闭环。
- 2026-06-22 已完成 P2 北方华创真实资料包与数据清单：新增 `docs/product/02-planning/P2_北方华创真实资料包与数据清单.md`，列出 2025 年报、2025 半年报、2025 三季报、2026 一季报、官网、产品页和 ESG 报告等第一批资料入口，以及资料缺口、公司基础字段、产品技术字段、财务指标、图表需求、章节映射和系统录入顺序。下一步应先人工下载/登记官方资料并提取 2021-2025 年核心指标，不直接写代码。

## 当前阻塞

- 暂无。

## 关键依赖

- 项目工作区: `C:\Work\note\CursorWorkSpace\investment-research`
- Wiki 项目页: `20_projects/active/investment-research/索引.md`

## 最近变化

- 2026-06-13: 已通过 `attach_project.py` 接入 Wiki，并登记 2 个原始资料文档。
- 2026-06-13: 已形成初步方向研判：优先验证上市公司投研内容工厂，半导体只是当前样例行业；创业项目评价作为第二方向保留。
- 2026-06-13: 已将原始 Word 输入移动到 `docs/product/04-source-materials/raw/`，并生成给老板汇报报告 `docs/product/00-executive/archive/给老板的投研系统方向汇报_v1.md`。
- 2026-06-14: 老板反馈后方向收敛为半导体优先；新增 GaN PDF 和微信公众号图表型报告截图作为报告风格样本；已更新 `docs/product/00-executive/archive/给老板的投研系统方向汇报_v2.md` 为当前执行版，明确微信样本是图文页式/图片化行业报告，并把下一步拆为 30 天执行计划。
- 2026-06-14: 根据老板最新反馈重写 v3 汇报和开发 PRD；v3 已作为独立综合版覆盖前序结论，强调内容质量、准确度、精准性、半导体先跑通再复制、三类收入模式；PRD 已改为可开发执行基准，覆盖页面、流程、数据模型、智能体、阶段任务和验收清单。
- 2026-06-15: 老板认可 v3 和 PRD 大方向，并补充：第一阶段按半导体全产业链展开；材料、设备、设计、制造、封测再细分；AI 图表生成可以前置但需人工校对；ToB 暂不急推，先验证研报质量；数据源大概率需要采购并评估 API。
- 2026-06-15: 新增老板手工样本 `半导体上市公司投研分析.docx`，其本质是完整版上市公司投研报告 + 财务指标分析体系 + 估值框架 + 课程化转化 + 工具包雏形。
- 2026-06-15: 已生成 `docs/product/00-executive/给老板的投研系统方向汇报_v4.md` 作为老板综合汇报版，并生成 `docs/product/01-requirements/半导体智能研究与服务平台_PRD_v2.md` 作为当前开发基准。
- 2026-06-15: 老板确认 v4 全部关键事项并认可 PRD_v2；已删除 v4 中“建议老板确认的事项”，并在 v4/PRD_v2 中明确核心系统采用自研业务底座。
- 2026-06-15: 已将本项目从“模糊老板需求 -> 多轮需求分析 -> v4 汇报 -> PRD_v2 -> 垂直切片开发计划”的经验沉淀为共享模式 `30_shared/patterns/AI项目从想法到落地标准工作流.md`。
- 2026-06-15: 已新增项目开发计划 `docs/product/02-planning/半导体智能研究与服务平台_垂直切片开发计划.md`，切片顺序为 Slice 0 工程脚手架、Slice 1 资料库、Slice 2 产业链/公司/指标、Slice 3 报告项目、Slice 4 图表、Slice 5 审稿、Slice 6 AI 辅助、Slice 7 发布拆分、Slice 8 公司深度、Slice 9 数据源、Slice 10 样板报告闭环。
- 2026-06-16: 共享模式已升级为面向新手的可执行提示词手册，覆盖从想法接收到反馈迭代的主路径，以及需求变更、重大 Bug、安全权限、测试失败、数据库/数据变更等企业级异常分支。
- 2026-06-16: 已完成产品文档目录重整，当前关键路径为：老板汇报 `docs/product/00-executive/给老板的投研系统方向汇报_v4.md`，PRD `docs/product/01-requirements/半导体智能研究与服务平台_PRD_v2.md`，计划 `docs/product/02-planning/半导体智能研究与服务平台_垂直切片开发计划.md`，原始资料 `docs/product/04-source-materials/raw/`。
- 2026-06-16: 老板新增半导体上市公司高管校友图谱需求，已直接纳入现有 v4/PRD_v2/垂直切片计划，不新建 v5 或 PRD_v3；该模块定位为“半导体产业人才与校友图谱”，核心对象包括高管、学校、教育履历、公司任职、分支机构、技术产品和行业地位。
- 2026-06-16: 当时已将工程化拆解内容合并回 `docs/product/02-planning/半导体智能研究与服务平台_垂直切片开发计划.md`，作为阶段性主计划；单独工程化拆解草稿已移入 `docs/product/02-planning/archive/`。
- 2026-06-18: 已将过大的垂直切片开发计划拆分为轻量总纲、8 份公共工程契约和 12 份 Slice 工程说明书；拆分前完整稿已归档到 `docs/product/02-planning/archive/`，当前进入“工程基准文档审阅与项目控制文件补齐”阶段，仍未开始代码开发。
- 2026-06-19: 已新增根目录 README、MIT LICENSE 和 .gitignore，初始化本地 Git main 分支，配置 GitHub 远端 `https://github.com/jarvanlove/investment-research.git`；已增强 AGENTS/CLAUDE 的项目约束，并补齐 PRODUCT_SPEC、ARCHITECTURE、TESTING、SECURITY 的当前基准。
- 2026-06-19: 发现本项目无法 push 的原因是当前项目使用 HTTPS 远端且本地 `GITHUB_PERSONAL_ACCESS_TOKEN` 不可用，而 `ObsidianToWiki` 使用 SSH 远端；已将本项目远端切换为 SSH，合并远端初始 MIT LICENSE 提交并成功 push。
- 2026-06-19: 用户确认本地 PostgreSQL、MinIO、Redis 条件和推荐技术栈；真实本地密码只保留在会话中，不写入仓库文档。
- 2026-06-19: 用户逐项确认 Slice 0 开发前约定、种子数据范围、private GitHub 文档保留策略和前端设计规则；已要求全部更新对应文档。
- 2026-06-19: 用户澄清 `product-design:index` 和 `design-taste-frontend` 是后续正式开发前端时使用的 AI skill 顺序；已将文档表述从普通“前端设计约束”改为“AI 前端设计工作流约束”。
- 2026-06-19: 用户确认下一步建议后，新增 Slice 0 详细开发执行计划，并重写 README；确认 `scripts/` 未 push 的原因是空目录，已添加 `.gitkeep`。
- 2026-06-19: 已实现 Slice 0 代码骨架：`apps/api` 为 FastAPI + SQLAlchemy + Alembic，`apps/web` 为 Next.js + Tailwind + Lucide；已更新 README、ARCHITECTURE、TESTING、SECURITY、TASKS 和 CHANGELOG 为实际实现状态。
- 2026-06-19: 针对浏览器 hydration warning 和 Slice 0 验收遗漏，新增测试与验收契约；确认 `cz-shortcut-listen` 属于浏览器插件干扰，同时修复真实 PostgreSQL session schema 设置问题并补充未来模块验收门禁。
- 2026-06-19: Slice 0 已完成最终收尾：修复 `localhost` 与 `127.0.0.1` Cookie host 不一致导致的登录后 Dashboard 307 问题，补齐 not-found/favicon，加入半导体主题互动登录视觉，并通过双 host 无插件 Chrome 登录 smoke。
- 2026-06-19: 已新增 Slice 1 开发执行计划并同步项目入口文档，当前下一步若继续开发，应先按该计划启动 `S1-IMPL`，不要跳到 Slice 2 或资料库以外的模块。
- 2026-06-19: Slice 1 已实现并完成本地分层验收：后端 `ruff/mypy/pytest` 通过，前端 `lint/typecheck/build` 通过，Alembic 创建 Source 三表，真实 HTTP source create/list/upload 通过，MinIO health 200，无插件 Chrome 双 host 主流程通过，移动宽度 `/sources` 可见。
- 2026-06-19: 已将本机 Playwright 路径写入项目测试规范，避免后续验证时重复查找；同时新增 Slice 2 开发执行计划，当前未写代码。
- 2026-06-19: 已修复 `/sources` 开发态样式丢失问题，原因是 Next dev 缓存/进程状态异常；通过停止旧前端进程、清理 `apps/web/.next` 并重启前端恢复。
- 2026-06-19: 已完成 Slice 2 产业链/公司/指标基础库实现和分层验收：数据库迁移、种子数据、后端 API、前端页面、权限负向路径、真实 HTTP 和无插件浏览器 smoke 均已通过。
- 2026-06-19: 已新增 Slice 2A 开发执行计划，明确下一步不跳到 Slice 3，而是按总纲推进高管校友图谱基础库。

## 下一步

- 生成两个 Word 原始输入的 extracted Markdown 版本，便于后续智能体读取。
- 将微信截图样本、GaN PDF 样本和老板手工公司投研样本分别沉淀成可执行报告模板。
- 将高管校友图谱需求沉淀为数据源评估清单、字段字典和第一批样板公司/学校范围。
- 若用户继续推进，下一步不能自动开启新 Slice；P2 已进入真实样板报告与产品化推进阶段。第一份真实样板已确认为 `北方华创完整版投研分析 v0.1`，P2-2 资料/指标/图表清单已形成；下一步应先下载/登记官方资料，人工提取 2021-2025 年核心指标和图表数据，再决定是否进入系统内跑 P2-3。
- 阶段收口评审文档: `docs/product/02-planning/Slice_0-10_阶段收口评审.md`。后续确定下一阶段前应先读该文档。
- 若用户要先补真实数据，下一步应填写 4 个 CSV 模板并确认字段，而不是直接写导入代码或爬虫。
- 审阅已拆分的 `02-planning/` 总纲、公共工程契约和 Slice 工程说明书，确认 Slice 1 是否还需要继续下钻到更细的任务包。

