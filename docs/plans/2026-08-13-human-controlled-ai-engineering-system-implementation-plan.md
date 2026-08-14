# Human-Controlled AI Engineering System 2.0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **Status:** Product direction approved on 2026-08-13. M0-M5 were implemented, machine-accepted, and product-owner approved on 2026-08-14. Main integration was later explicitly authorized after documentation, index, private-Wiki, and final-verification gates.

**Goal:** 将 ObsidianToWiki 从“依赖用户主动调用、手工维护且会持续膨胀的 Markdown 项目记忆”升级为“项目接入后被动生效、上下文可信有界、记忆自动编译、同时服务 AI 与人类的人类可控 AI 工程系统”。

**Architecture:** 保留现有 `wiki.context.json`、项目控制文件、统一运行时和私人 Markdown Wiki；新增上下文可信门禁、记忆编译器、有界当前投影和静态本地驾驶舱。`engineering_governance.py` 管任务和门禁，`memory_compiler.py` 只消费证据完整的任务收据并生成原子记忆卡，`context_integrity.py` 决定什么可以进入模型，`project_cockpit.py` 把同一可信投影提供给人。默认不增加守护进程、数据库或强制 Git Hook。

**Tech Stack:** Python 3 标准库、PowerShell/Shell 包装器、JSON Schema 风格注册表、Markdown 原子记忆卡、静态 HTML/CSS/JSON 驾驶舱、`unittest`、Git CLI、现有 ObsidianToWiki 统一运行时。

---

## 交付边界与完成定义

本计划只实现设计文档中列出的本次必做范围。以下条件全部成立才允许发布：

1. 已接入项目中，用户只说“修复登录失败”也会进入治理流程，不要求用户记住“开始工作”。
2. P3 低风险任务不会制造多余确认；P1/P0 必须在实现前获得责任确认，在关闭前完成人类理解确认。
3. Bug 未复现、根因未知或修改范围超出计划时不能静默进入实现或关闭。
4. 验证不再是任意字符串，必须记录命令、退出码、证据类型、时间和结果。
5. 中断后可以从 `.obsidiantowiki/task-state.json` 恢复任务、Git 基线、范围与未完成门禁。
6. 关键变更必须生成“改了什么、为什么、影响哪里、如何验证、仍有什么风险、如何回滚”的解释包。
7. 能力恢复只记录可观察行为和知识候选，不生成虚假的综合能力分数。
8. 旧项目、旧收据和原有 `开始工作 / 继续 / 收工` 均保持兼容。
9. Wiki 损坏、过期、冲突或漏召回时，系统明确降级或阻断，不能把缺失事实交给 AI 补猜。
10. 空模板项目在首次真实任务后形成非空当前投影；超大旧项目可以无损编译、归档并恢复。
11. 七个核心页和默认 Context Pack 都有硬预算，模型读取量不随项目年龄线性增长。
12. 每次 AI 上下文都有 Context Receipt，可证明使用了哪些事实、哈希、可信状态和缺失项。
13. 用户不打开 Obsidian，也能通过自然语言和一屏驾驶舱理解当前状态、最近变化、风险、待决定与下一步。
14. 自动压缩只退出默认上下文，不删除原子事实、任务收据或 Git 证据。

**强制执行顺序：** 先执行“任务 1：锁定产品契约和迭代范围”，再执行 0A-0F；文档将 0A-0F 放在前面是为了突出它们是所有工程门禁的前置架构层，不表示允许先写代码后补产品契约。

## 任务 0A：实现纯只读上下文健康门禁

**Files:**

- Create: `00_system/scripts/context_integrity.py`
- Create: `00_system/registry/memory_policy.json`
- Create: `tests/test_context_integrity.py`
- Modify: `00_system/scripts/wiki_lib.py`
- Modify: `00_system/scripts/doctor.py`
- Modify: `00_system/scripts/otw.py`
- Modify: `00_system/scripts/otw.ps1`
- Modify: `00_system/scripts/otw.sh`

**Step 1: 写失败测试**

覆盖：缺失文件、不可读取 UTF-8、未闭合 Frontmatter、非法 YAML、Schema 错误、过期、缺少来源、同 ID 冲突、隐私排除和正常页面。损坏元数据必须返回 `quarantined`，不能继续以空 Frontmatter 索引。

核心接口固定为：

```python
def inspect_page(path: Path, *, policy: dict[str, object], today: date) -> dict[str, object]: ...
def inspect_context(repo_root: Path, required: list[dict[str, object]]) -> dict[str, object]: ...
```

返回状态只能是 `trusted / review_required / degraded / quarantined`，并附确定性 `reasons`。

**Step 2: 运行并确认失败**

Run: `python -m unittest tests.test_context_integrity -v`

Expected: FAIL，模块不存在。

**Step 3: 实现最小只读检查器**

新增 `otw context check --repo-root <repo> --format json`。该命令不得重建索引、同步页面、生成报告或修改时间戳；严格模式存在 `quarantined` 或必需内容缺失时退出 1。

**Step 4: 验证**

Run: `python -m unittest tests.test_context_integrity tests.test_doctor -v`

Expected: PASS；测试同时证明原有 `lint_wiki.py` 的写操作没有被偷偷调用。

**Step 5: Commit**

```bash
git add 00_system/scripts/context_integrity.py 00_system/registry/memory_policy.json 00_system/scripts/wiki_lib.py 00_system/scripts/doctor.py 00_system/scripts/otw.py 00_system/scripts/otw.ps1 00_system/scripts/otw.sh tests/test_context_integrity.py
git commit -m "feat: add read-only context integrity gate"
```

## 任务 0B：实现 Context Contract、预算与使用收据

**Files:**

- Create: `00_system/scripts/context_contract.py`
- Modify: `00_system/scripts/search_wiki.py`
- Modify: `00_system/scripts/retrieval_index.py`
- Modify: `00_system/scripts/handle_nl_request.py`
- Create: `tests/test_context_contract.py`
- Modify: `tests/test_retrieval_core.py`

**Step 1: 写失败测试**

覆盖：默认只读取项目最小控制闭包、`project.memory.md` 和最多 6 张可信卡；默认总预算 6,000 tokens；损坏卡不进入结果；无结果返回 `missing` 而不是“没有限制”；同一任务重复查询产生稳定内容哈希；超预算按相关性和权威级别淘汰，而不是字符串盲截断。

Contract 最小结构：

```json
{
  "task_id": "task-123",
  "required_kinds": ["current_control", "active_decision", "open_risk"],
  "max_age_days": {"active_decision": 180, "open_risk": 30},
  "max_cards": 6,
  "token_budget": 6000,
  "missing_policy": "block_for_p1_p0"
}
```

**Step 2: 运行失败测试**

Run: `python -m unittest tests.test_context_contract tests.test_retrieval_core -v`

Expected: FAIL。

**Step 3: 实现 Context Receipt**

每次上下文输出同时记录：query、task id、L0/L1 文件哈希、卡片 ID/哈希/状态、预算、缺失、冲突、生成时间和降级结论。收据写入 `.obsidiantowiki/context-receipts/<task-id>.json`，不写入 Git。

**Step 4: 验证**

Run: `python -m unittest tests.test_context_contract tests.test_retrieval_core -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add 00_system/scripts/context_contract.py 00_system/scripts/search_wiki.py 00_system/scripts/retrieval_index.py 00_system/scripts/handle_nl_request.py tests/test_context_contract.py tests/test_retrieval_core.py
git commit -m "feat: bound and receipt every AI context pack"
```

## 任务 0C：实现原子记忆卡与记忆编译器

**Files:**

- Create: `00_system/scripts/memory_compiler.py`
- Create: `00_system/templates/memory-card.md`
- Modify: `00_system/registry/memory_policy.json`
- Modify: `00_system/scripts/project_session.py`
- Create: `tests/test_memory_compiler.py`

**Step 1: 写失败测试**

覆盖：只有 resolved 收据可编译；常规文件修改不生成卡；决策、开放风险、根因模式、里程碑和能力观察正确分类；同一 stable key 幂等；新决定可以 `supersede` 旧决定；冲突进入 `disputed`；P1/P0 和共享候选不能自动批准；敏感内容被拒绝或脱敏。

卡片最小 Frontmatter：

```yaml
id: DEC-000123
kind: decision
status: active
effective_from: 2026-08-13
supersedes: []
source_receipt: task-123
evidence_refs: []
last_verified: 2026-08-13
confidence: verified
summary: 当前有效的一句话结论
```

**Step 2: 运行失败测试**

Run: `python -m unittest tests.test_memory_compiler -v`

Expected: FAIL。

**Step 3: 实现确定性编译管道**

AI 只负责生成候选摘要；类型、目标层、敏感等级、审批需求、稳定 ID、状态迁移和去重由 Runtime 决定。禁止直接总结整个聊天历史。

**Step 4: 验证**

Run: `python -m unittest tests.test_memory_compiler -v`

Expected: PASS，重复编译同一收据文件哈希不变。

**Step 5: Commit**

```bash
git add 00_system/scripts/memory_compiler.py 00_system/templates/memory-card.md 00_system/registry/memory_policy.json 00_system/scripts/project_session.py tests/test_memory_compiler.py
git commit -m "feat: compile task evidence into atomic memory cards"
```

## 任务 0D：实现有界当前投影、压缩和旧项目迁移

**Files:**

- Modify: `00_system/scripts/memory_compiler.py`
- Modify: `00_system/scripts/rebuild_indexes.py`
- Modify: `00_system/scripts/create_page.py`
- Modify: `00_system/scripts/attach_project.py`
- Create: `00_system/scripts/migrate_project_memory.py`
- Create: `tests/test_memory_projection.py`
- Create: `tests/test_memory_migration.py`

**Step 1: 写失败测试**

使用三个 fixture：空模板项目、正常项目、单页超过 100KB 的长期项目。覆盖七个核心页预算、当前/历史分离、90 天/30 事件时间线、active/superseded 过滤、迁移 dry-run、原文件备份、来源回链、重复迁移幂等和用户定制冲突保留。

**Step 2: 运行失败测试**

Run: `python -m unittest tests.test_memory_projection tests.test_memory_migration -v`

Expected: FAIL。

**Step 3: 实现投影和迁移**

新增：

```text
otw memory compile --repo-root <repo> [--dry-run]
otw memory migrate --repo-root <repo> --dry-run
otw memory migrate --repo-root <repo> --apply
```

`--apply` 前必须保存原始页面备份和迁移清单；无法确定的新旧状态标为 `review_required`，禁止 AI 自动决定。空模板项目从项目本地控制文件生成待确认首快照，不虚构内容。

**Step 4: 验证**

Run: `python -m unittest tests.test_memory_projection tests.test_memory_migration -v`

Expected: PASS；投影全部低于策略预算，原始 fixture 可完整恢复。

**Step 5: Commit**

```bash
git add 00_system/scripts/memory_compiler.py 00_system/scripts/rebuild_indexes.py 00_system/scripts/create_page.py 00_system/scripts/attach_project.py 00_system/scripts/migrate_project_memory.py tests/test_memory_projection.py tests/test_memory_migration.py
git commit -m "feat: keep project memory bounded and migratable"
```

## 任务 0E：实现自然语言管家、行动流和项目驾驶舱

**Files:**

- Create: `00_system/scripts/project_cockpit.py`
- Create: `00_system/templates/cockpit/index.html`
- Create: `00_system/templates/cockpit/styles.css`
- Modify: `00_system/scripts/otw.py`
- Modify: `00_system/scripts/handle_nl_request.py`
- Create: `tests/test_project_cockpit.py`
- Create: `tests/test_project_concierge.py`
- Create: `docs/design/ui-tasks/human-control-cockpit.yaml`

**Step 1: 建立 U2 设计治理任务**

通过公共 Runtime 对新驾驶舱执行 `ui assess` 和 `ui init`，记录视觉方向候选；在获得用户明确批准前，只允许实现数据合同和静态结构测试，不进入生产视觉实现。

**Step 2: 写失败测试**

覆盖五个默认区域：当前状态、最近变化、待决定、开放风险、下一步；无行动时显示“无需处理”而不是空页面；每项可下钻到卡片、任务收据或 Diff；HTML 不包含源码、密钥和私人绝对路径；自然语言回答引用 Context Receipt；驾驶舱生成失败不破坏 Markdown。

**Step 3: 运行失败测试**

Run: `python -m unittest tests.test_project_cockpit tests.test_project_concierge -v`

Expected: FAIL。

**Step 4: 实现静态本地投影**

新增 `otw cockpit build|open --repo-root <repo>`；`build` 生成 `.obsidiantowiki/cockpit/` 下的静态 HTML/JSON，`open` 只打开本地文件。自然语言“项目现在怎么样”使用同一投影，不另建第二套摘要逻辑。

**Step 5: 完成视觉验收**

在方向获批后，收集桌面和移动截图、Visual QA、键盘可用性、对比度和溢出证据，通过 U2 close 门禁。

**Step 6: 验证**

Run: `python -m unittest tests.test_project_cockpit tests.test_project_concierge -v`

Expected: PASS。

**Step 7: Commit**

```bash
git add 00_system/scripts/project_cockpit.py 00_system/templates/cockpit 00_system/scripts/otw.py 00_system/scripts/handle_nl_request.py tests/test_project_cockpit.py tests/test_project_concierge.py docs/design/ui-tasks/human-control-cockpit.yaml
git commit -m "feat: add human-first project cockpit"
```

## 任务 0F：把自动记忆维护接入项目生命周期

**Files:**

- Modify: `00_system/scripts/project_session.py`
- Modify: `00_system/scripts/handle_nl_request.py`
- Modify: `docs/templates/project-AGENTS.md`
- Modify: `docs/templates/project-CLAUDE.md`
- Modify: `docs/templates/global-skills/obsidiantowiki-manager/SKILL.md`
- Modify: `tests/test_project_lifecycle_e2e.py`
- Create: `tests/test_automatic_memory_lifecycle.py`

**Step 1: 写失败测试**

覆盖：`attach` 生成首快照候选；`start/continue` 只读检查 Context 和预算；`close` 自动生成记忆候选；收据决议后才编译；超过预算自动编译；90 天无活动生成冷却恢复摘要；用户不说任何 Wiki 命令也会完成维护；普通成功不产生人类打扰。

**Step 2: 运行失败测试**

Run: `python -m unittest tests.test_automatic_memory_lifecycle tests.test_project_lifecycle_e2e -v`

Expected: FAIL。

**Step 3: 接入既有生命周期**

不得新增第二套“记忆会话”。所有自动动作必须绑定现有任务 ID 和收据；失败时保留任务关闭结果，但将记忆状态标为 `pending_memory_repair`，P1/P0 必需历史写回失败则不得宣称治理完全关闭。

**Step 4: 验证**

Run: `python -m unittest tests.test_automatic_memory_lifecycle tests.test_project_lifecycle_e2e -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add 00_system/scripts/project_session.py 00_system/scripts/handle_nl_request.py docs/templates/project-AGENTS.md docs/templates/project-CLAUDE.md docs/templates/global-skills/obsidiantowiki-manager/SKILL.md tests/test_automatic_memory_lifecycle.py tests/test_project_lifecycle_e2e.py
git commit -m "feat: maintain bounded memory through normal work"
```

## 任务 1：锁定产品契约和迭代范围

**Files:**

- Modify: `PRODUCT_SPEC.md`
- Modify: `ARCHITECTURE.md`
- Modify: `TASKS.md`
- Modify: `TESTING.md`
- Modify: `SECURITY.md`
- Modify: `CHANGELOG.md`
- Reference: `docs/plans/2026-08-13-human-controlled-ai-engineering-system-design.md`

**Step 1: 先写产品契约检查测试**

在 `tests/test_engineering_governance_contract.py` 中断言控制文件明确包含：四层事实优先级、上下文可信门禁、有界预算、记忆编译器、环境式触发、P3-P0、根因门禁、范围漂移、人类理解门禁、结构化证据、能力候选、人类驾驶舱、隐私边界和兼容策略。

**Step 2: 运行测试并确认失败**

Run: `python -m unittest tests.test_engineering_governance_contract -v`

Expected: FAIL，提示当前控制文件缺少 2.0 契约。

**Step 3: 最小更新控制文件**

- `PRODUCT_SPEC.md`：写用户价值、AI/人类双界面、默认被动使用体验和非目标。
- `ARCHITECTURE.md`：写 L0-L3、可信门禁、记忆编译器、有界投影、治理内核、状态文件、收据和 Wiki 路由边界。
- `TASKS.md`：把本计划任务登记为可跟踪条目。
- `TESTING.md`：登记单元、集成、E2E、兼容和试点验收命令。
- `SECURITY.md`：写 P1/P0 的责任确认、敏感信息不得进入证据和 Wiki。
- `CHANGELOG.md`：先加入 Unreleased 条目，不提前宣称已发布。

**Step 4: 运行契约测试**

Run: `python -m unittest tests.test_engineering_governance_contract -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add PRODUCT_SPEC.md ARCHITECTURE.md TASKS.md TESTING.md SECURITY.md CHANGELOG.md tests/test_engineering_governance_contract.py
git commit -m "docs: define human-controlled AI engineering contract"
```

## 任务 2：实现任务状态模型与原子持久化

**Files:**

- Create: `00_system/scripts/engineering_governance.py`
- Create: `00_system/registry/engineering_governance.json`
- Create: `tests/test_engineering_governance_state.py`
- Modify: `.gitignore`

**Step 1: 写失败测试**

覆盖：

- 新任务生成 schema version 1 的状态。
- 状态只写入 `.obsidiantowiki/task-state.json`。
- 写入使用临时文件加 `os.replace`，失败时不留下半截 JSON。
- 未知状态、缺少任务 ID、非法风险等级、非法状态迁移全部拒绝。
- 状态文件属于本地运行态，不进入 Git。

核心接口固定为：

```python
def create_task_state(repo_root: Path, task: str, intent: str) -> dict[str, Any]: ...
def load_task_state(repo_root: Path) -> dict[str, Any]: ...
def transition_task(repo_root: Path, target: str, *, reason: str = "") -> dict[str, Any]: ...
def save_task_state(repo_root: Path, state: dict[str, Any]) -> None: ...
```

合法主状态固定为：

```text
detected -> investigating -> planned -> awaiting_approval -> implementing
-> verifying -> awaiting_understanding -> ready_to_close -> closed
```

旁路状态仅允许 `blocked`、`abandoned`、`stale`。

**Step 2: 确认测试失败**

Run: `python -m unittest tests.test_engineering_governance_state -v`

Expected: FAIL，模块不存在。

**Step 3: 实现最小状态内核**

状态至少包含：

```json
{
  "schema_version": 1,
  "task_id": "20260813T140000-login-failure",
  "task": "修复登录失败",
  "intent": "code_change",
  "status": "investigating",
  "risk": {"level": "P2", "reasons": [], "confirmed_by": null},
  "baseline": {},
  "acceptance": [],
  "scope": {"allowed": [], "changed": [], "drift": []},
  "diagnosis": {"reproduction": null, "root_cause": null, "minimal_fix": null},
  "verification": [],
  "understanding": {},
  "knowledge_candidates": [],
  "timestamps": {}
}
```

**Step 4: 运行测试**

Run: `python -m unittest tests.test_engineering_governance_state -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add 00_system/scripts/engineering_governance.py 00_system/registry/engineering_governance.json tests/test_engineering_governance_state.py .gitignore
git commit -m "feat: add durable engineering task state"
```

## 任务 3：捕获 Git 基线并支持中断恢复

**Files:**

- Modify: `00_system/scripts/engineering_governance.py`
- Modify: `00_system/scripts/project_session.py`
- Create: `tests/test_engineering_governance_recovery.py`
- Modify: `tests/test_project_session_receipt.py`

**Step 1: 写失败测试**

覆盖：开始任务时记录当前分支、HEAD、已跟踪修改、未跟踪文件和时间；恢复时区分“任务前已有改动”和“本任务新增改动”；HEAD 或分支被外部改变时标记 `stale`，不得覆盖现有任务。

**Step 2: 运行测试并确认失败**

Run: `python -m unittest tests.test_engineering_governance_recovery -v`

Expected: FAIL。

**Step 3: 实现基线与恢复**

新增接口：

```python
def capture_git_baseline(repo_root: Path) -> dict[str, Any]: ...
def compare_with_baseline(repo_root: Path, baseline: dict[str, Any]) -> dict[str, Any]: ...
def resume_summary(repo_root: Path) -> dict[str, Any]: ...
```

`project_session.py start/check` 读取相同状态，不再维护第二套会话真相。

**Step 4: 验证**

Run: `python -m unittest tests.test_engineering_governance_recovery tests.test_project_session_receipt -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add 00_system/scripts/engineering_governance.py 00_system/scripts/project_session.py tests/test_engineering_governance_recovery.py tests/test_project_session_receipt.py
git commit -m "feat: preserve task baseline across interrupted sessions"
```

## 任务 4：实现风险分级与责任确认

**Files:**

- Modify: `00_system/scripts/engineering_governance.py`
- Modify: `00_system/registry/engineering_governance.json`
- Create: `tests/test_engineering_governance_risk.py`

**Step 1: 写失败测试**

至少覆盖：文档拼写为 P3；普通局部代码为 P2；鉴权、权限、数据迁移、密钥、部署和外部写操作提升为 P1；不可逆删除、生产数据和高影响安全边界为 P0；不确定时向高一级保守提升；P1/P0 未确认不能进入 `implementing`。

**Step 2: 运行失败测试**

Run: `python -m unittest tests.test_engineering_governance_risk -v`

Expected: FAIL。

**Step 3: 实现可解释分类**

分类结果必须同时返回等级和命中原因，禁止只返回一个黑盒分数：

```python
{"level": "P1", "reasons": ["touches authentication boundary"], "source": "deterministic-rule"}
```

**Step 4: 验证**

Run: `python -m unittest tests.test_engineering_governance_risk -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add 00_system/scripts/engineering_governance.py 00_system/registry/engineering_governance.json tests/test_engineering_governance_risk.py
git commit -m "feat: enforce explainable engineering risk levels"
```

## 任务 5：实现 Bug 根因门禁和最小修改契约

**Files:**

- Modify: `00_system/scripts/engineering_governance.py`
- Create: `tests/test_engineering_governance_diagnosis.py`
- Modify: `docs/templates/project-control/AI_CODING_LIFECYCLE.md`

**Step 1: 写失败测试**

Bug 类型任务在进入 `implementing` 前必须满足：存在复现步骤或明确说明无法复现的证据、存在根因、存在“为何是最小修改”的说明、存在验收条件。缺少任一项时状态只能是 `investigating` 或 `blocked`。

**Step 2: 确认失败**

Run: `python -m unittest tests.test_engineering_governance_diagnosis -v`

Expected: FAIL。

**Step 3: 实现门禁**

不强迫所有任务伪装成 Bug：`feature`、`refactor`、`docs` 分别使用自己的前置条件；只有 Bug 强制根因链。

**Step 4: 验证**

Run: `python -m unittest tests.test_engineering_governance_diagnosis -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add 00_system/scripts/engineering_governance.py tests/test_engineering_governance_diagnosis.py docs/templates/project-control/AI_CODING_LIFECYCLE.md
git commit -m "feat: require root cause before bug implementation"
```

## 任务 6：实现修改范围与补丁循环门禁

**Files:**

- Modify: `00_system/scripts/engineering_governance.py`
- Create: `tests/test_engineering_governance_scope.py`

**Step 1: 写失败测试**

覆盖：计划内文件允许继续；新增目录、架构层、依赖、数据库迁移或部署配置会生成范围漂移；P3/P2 漂移发出非阻断或阻断提示；P1/P0 漂移必须重新确认；同一验收问题连续三次修改仍失败时进入 `blocked` 并要求重新诊断，禁止继续盲目补丁。

**Step 2: 运行失败测试**

Run: `python -m unittest tests.test_engineering_governance_scope -v`

Expected: FAIL。

**Step 3: 实现差异比较**

基于任务基线和 `scope.allowed` 计算，不扫描或修改项目外文件。补丁循环按“同一验收项失败 + 新一次实现”计数，不按普通命令次数误报。

**Step 4: 验证**

Run: `python -m unittest tests.test_engineering_governance_scope -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add 00_system/scripts/engineering_governance.py tests/test_engineering_governance_scope.py
git commit -m "feat: detect scope drift and patch loops"
```

## 任务 7：将验证字符串升级为结构化证据

**Files:**

- Modify: `00_system/scripts/project_session.py`
- Modify: `00_system/scripts/otw.ps1`
- Modify: `00_system/scripts/project_session.ps1`
- Modify: `00_system/scripts/project_session.sh`
- Create: `tests/test_engineering_governance_evidence.py`
- Modify: `tests/test_project_session_receipt.py`

**Step 1: 写失败测试**

验证记录至少包含 `kind`、`command`、`exit_code`、`result`、`recorded_at`、`source`。其中 `source` 只能是：

- `deterministic`
- `ai_self_check`
- `independent_ai_review`
- `human_observation`

测试还要证明：仅写“测试通过”不能关闭；非零退出码不能标为通过；P1/P0 仅有 AI 自检不能关闭；旧版字符串收据可读取但会被标记为 `legacy_unstructured`。

**Step 2: 运行失败测试**

Run: `python -m unittest tests.test_engineering_governance_evidence tests.test_project_session_receipt -v`

Expected: FAIL。

**Step 3: 实现收据 schema v2**

收据继续位于 `.obsidiantowiki/session-receipt.json`，避免双系统；新增 `evidence`、`gate_results`、`explanation_package`、`knowledge_candidates`，并保留 v1 读取迁移。

**Step 4: 验证**

Run: `python -m unittest tests.test_engineering_governance_evidence tests.test_project_session_receipt -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add 00_system/scripts/project_session.py 00_system/scripts/otw.ps1 00_system/scripts/project_session.ps1 00_system/scripts/project_session.sh tests/test_engineering_governance_evidence.py tests/test_project_session_receipt.py
git commit -m "feat: require structured verification evidence"
```

## 任务 8：实现关键变更解释包与人类理解门禁

**Files:**

- Modify: `00_system/scripts/engineering_governance.py`
- Modify: `00_system/scripts/project_session.py`
- Create: `tests/test_human_understanding_gate.py`
- Create: `docs/templates/project-control/ENGINEERING_GOVERNANCE.md`

**Step 1: 写失败测试**

关键变更解释包必须完整包含：

```text
1. 改了什么
2. 为什么这样改
3. 数据或调用链如何变化
4. 哪些文件和边界受到影响
5. 如何验证
6. 仍有哪些风险
7. 如何回滚
```

规则：P3 自动通过；P2 展示但允许继续；P1 要求用户确认“已理解影响和剩余风险”；P0 除理解确认外还必须有明确授权。AI 不能代替用户填写人类确认。

**Step 2: 确认失败**

Run: `python -m unittest tests.test_human_understanding_gate -v`

Expected: FAIL。

**Step 3: 实现解释包生成与门禁**

生成内容来自任务状态、Git diff 摘要和结构化证据；不把整段源码或敏感值复制进 Wiki。缺少信息时显示“未知”，不能自动编造。

**Step 4: 验证**

Run: `python -m unittest tests.test_human_understanding_gate -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add 00_system/scripts/engineering_governance.py 00_system/scripts/project_session.py tests/test_human_understanding_gate.py docs/templates/project-control/ENGINEERING_GOVERNANCE.md
git commit -m "feat: add human understanding gate for critical changes"
```

## 任务 9：实现能力恢复闭环与知识候选路由

**Files:**

- Modify: `00_system/scripts/engineering_governance.py`
- Modify: `00_system/scripts/project_session.py`
- Create: `tests/test_capability_recovery_loop.py`
- Modify: `docs/templates/project-control/ENGINEERING_GOVERNANCE.md`

**Step 1: 写失败测试**

只在以下条件触发一次轻量学习介入：新概念、P1/P0、同模块重复问题、AI 曾误判、用户连续跳过理解确认。交互只提供：

1. 让我先判断根因；
2. 给我解释调用链；
3. 这次跳过学习。

记录只允许可观察事件，例如“用户在看答案前选择了正确风险边界”“用户独立复述了回滚点”，禁止计算“综合能力 87 分”。

**Step 2: 运行失败测试**

Run: `python -m unittest tests.test_capability_recovery_loop -v`

Expected: FAIL。

**Step 3: 实现候选生成**

候选至少包含：

```json
{
  "type": "capability_observation",
  "topic": "authentication/session boundary",
  "observation": "user identified rollback point before reveal",
  "evidence_ref": "session-receipt.json#evidence-3",
  "suggested_destination": "project_memory",
  "sensitive": false,
  "status": "pending"
}
```

候选必须经过现有收据决议并交给 `memory_compiler.py` 后才能写入私人 Wiki；默认不把源码、密钥、个人评价写入共享层，不能绕过原子卡、去重和投影预算直接追加核心页。

**Step 4: 验证**

Run: `python -m unittest tests.test_capability_recovery_loop -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add 00_system/scripts/engineering_governance.py 00_system/scripts/project_session.py tests/test_capability_recovery_loop.py docs/templates/project-control/ENGINEERING_GOVERNANCE.md
git commit -m "feat: add evidence-based capability recovery loop"
```

## 任务 10：实现环境式被动触发和低噪音交互

**Files:**

- Modify: `00_system/scripts/handle_nl_request.py`
- Modify: `00_system/scripts/handle_nl_request.ps1`
- Modify: `00_system/scripts/handle_nl_request.sh`
- Modify: `docs/templates/global-skills/obsidiantowiki-manager/SKILL.md`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Modify: `00_system/scripts/attach_project.py`
- Create: `tests/test_ambient_governance_trigger.py`
- Modify: `tests/test_manager_skill_install.py`
- Modify: `tests/test_project_scaffold_upgrade.py`

**Step 1: 写失败测试**

意图分为 `read_only`、`code_change`、`external_mutation`、`destructive`。测试：

- “解释这段代码”不创建变更任务。
- “修复登录失败”自动创建或恢复治理任务。
- “部署到生产”至少为 P1，并要求确认。
- “删除生产数据”至少为 P0，并要求明确授权。
- 原有“开始工作 / 继续 / 收工”仍可作为诊断和恢复入口。
- 已有用户自定义的 `AGENTS.md` / `CLAUDE.md` 内容不会被覆盖，只更新受管区块。

**Step 2: 运行失败测试**

Run: `python -m unittest tests.test_ambient_governance_trigger tests.test_manager_skill_install tests.test_project_scaffold_upgrade -v`

Expected: FAIL。

**Step 3: 实现三层触发**

1. 项目入口文件：默认、跨模型、受管区块声明任何变更意图都要调用治理检查。
2. Manager Skill：识别普通自然语言变更请求并透明启动或恢复任务。
3. 可选适配器：只报告覆盖状态，不在本迭代增加后台守护进程。

正常 P3/P2 只在关键节点显示一行状态；仅根因未知、范围漂移、P1/P0、证据不足和理解确认时中断用户。

**Step 4: 验证**

Run: `python -m unittest tests.test_ambient_governance_trigger tests.test_manager_skill_install tests.test_project_scaffold_upgrade -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add 00_system/scripts/handle_nl_request.py 00_system/scripts/handle_nl_request.ps1 00_system/scripts/handle_nl_request.sh docs/templates/global-skills/obsidiantowiki-manager/SKILL.md AGENTS.md CLAUDE.md 00_system/scripts/attach_project.py tests/test_ambient_governance_trigger.py tests/test_manager_skill_install.py tests/test_project_scaffold_upgrade.py
git commit -m "feat: activate governance from ordinary coding intent"
```

## 任务 11：升级项目脚手架与旧项目兼容

**Files:**

- Modify: `00_system/registry/project_scaffold_schema.json`
- Modify: `00_system/registry/project_adapter_schema.json`
- Modify: `00_system/registry/runtime_release.json`
- Modify: `docs/templates/project-control/*`
- Modify: `00_system/scripts/attach_project.py`
- Modify: `00_system/scripts/project_adapter.py`
- Modify: `tests/test_project_adapter_upgrade.py`
- Modify: `tests/test_project_scaffold_upgrade.py`
- Create: `tests/test_engineering_governance_compat.py`

**Step 1: 写兼容失败测试**

覆盖：新接入项目获得治理控制文件；旧项目安全升级只改未被用户修改的模板；冲突文件进入 staged suggestion；旧 v1 收据可读取；新运行时不得让旧项目无法执行 `check` 和 `close`；高版本状态文件必须拒绝降级读取。

**Step 2: 运行失败测试**

Run: `python -m unittest tests.test_engineering_governance_compat tests.test_project_adapter_upgrade tests.test_project_scaffold_upgrade -v`

Expected: FAIL。

**Step 3: 实现版本升级**

- runtime release：`2.0.0`
- project scaffold：`4`
- receipt schema：`2`
- task state schema：`1`

实际版本只在所有验收完成后写入；开发中先使用 release candidate 标记，避免半成品被识别为稳定版。

**Step 4: 验证**

Run: `python -m unittest tests.test_engineering_governance_compat tests.test_project_adapter_upgrade tests.test_project_scaffold_upgrade -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add 00_system/registry/project_scaffold_schema.json 00_system/registry/project_adapter_schema.json 00_system/registry/runtime_release.json docs/templates/project-control 00_system/scripts/attach_project.py 00_system/scripts/project_adapter.py tests/test_project_adapter_upgrade.py tests/test_project_scaffold_upgrade.py tests/test_engineering_governance_compat.py
git commit -m "feat: upgrade project scaffold for governed AI coding"
```

## 任务 12：完成端到端验收与私人 Wiki 写回

**Files:**

- Create: `tests/test_human_controlled_ai_e2e.py`
- Modify: `tests/test_project_lifecycle_e2e.py`
- Modify: `README-zh.md`
- Modify: `README-EN.md`
- Modify: `使用手册.md`
- Modify: `标准自然语言话术清单.md`
- Modify: `OPERATIONS.md`
- Modify: `DEPLOYMENT.md`
- Modify: `CHANGELOG.md`

**Step 1: 编写端到端场景**

必须自动化覆盖设计文档 A-J：

- A：不说“开始工作”也能治理普通修复。
- B：简单 Bug 扩大修改时被范围门禁阻止。
- C：根因未知不能开写。
- D：P1 登录变更需要责任与理解确认。
- E：产生能力观察和知识候选，但不自动污染共享 Wiki。
- F：中断后恢复原任务和任务前已有改动。
- G：空模板项目从本地事实生成待确认首快照。
- H：超过 100KB 的旧记忆无损迁移为原子卡和有界投影。
- I：Wiki 损坏、过期、冲突或无结果时正确降级/阻断，模型拿不到隔离内容。
- J：用户不打开 Obsidian，也能通过自然语言和驾驶舱理解项目。

再增加两个边界场景：纯只读问答不产生任务；项目未接入时明确报告治理未覆盖，不假装已经受控。

**Step 2: 运行 E2E 并确认失败**

Run: `python -m unittest tests.test_human_controlled_ai_e2e tests.test_project_lifecycle_e2e -v`

Expected: 在前序任务完成前 FAIL。

**Step 3: 补齐最小集成和用户文档**

文档首页只保留普通用户需要知道的四句话：

1. 项目接入一次，之后照常向 AI 提需求。
2. 系统只在根因、风险、范围或理解需要你决定时打断。
3. 项目记忆会自动记录、压缩和按需读取，不需要用户维护七个 Markdown 页面。
4. `开始工作 / 继续 / 收工` 仍可用于手动检查和恢复。

专业状态、命令和 schema 放入运维和开发文档，不堆在新手入口。

**Step 4: 全量验证**

Run: `python -m unittest discover -s tests -v`

Expected: 全部 PASS。

Run: `python 00_system/scripts/doctor.py --strict`

Expected: exit 0，无 schema、模板、断链或私有 Wiki 边界错误。

Run: `git diff --check`

Expected: 无空白错误。

**Step 5: 进行三个一次性试点项目验收**

分别用：

- 一个干净的新项目；
- 一个有任务前未提交改动的旧项目；
- 一个包含鉴权或部署边界的 P1 模拟项目。

每个试点保存收据和状态摘要，不保存密钥或业务源码。只有三类试点都通过，才把 runtime release 从 RC 改为 `2.0.0`。

**Step 6: 关闭任务并写回私人 Wiki**

通过公共运行时执行 `task_verify -> task_close -> receipt_resolve -> memory_compile -> projection_rebuild -> cockpit_build`。只编译经收据确认的耐久结论：架构决策、风险边界、验收结果和后续任务；能力观察默认写项目私有原子记忆，不自动写共享层，不直接追加核心页。

**Step 7: Commit**

```bash
git add tests/test_human_controlled_ai_e2e.py tests/test_project_lifecycle_e2e.py README-zh.md README-EN.md 使用手册.md 标准自然语言话术清单.md OPERATIONS.md DEPLOYMENT.md CHANGELOG.md 00_system/registry/runtime_release.json
git commit -m "release: ship human-controlled AI engineering system 2.0"
```

## 推荐执行节奏

建议拆成六个可独立回滚的里程碑：

1. **M0 产品契约与上下文可信**：任务 1、0A-0B。先锁定产品边界，再解决“Wiki 损坏、过期、冲突或太大时 AI 仍继续猜”。
2. **M1 自动记忆与人类产品**：任务 0C-0F。解决“项目为空、无限追加、用户不想看 Markdown”。
3. **M2 可恢复治理基础**：任务 1-3。解决“AI 做了什么无法追踪、下次接不上”。
4. **M3 工程质量门禁**：任务 4-7。解决“没根因就开写、范围扩大、验证靠嘴说、无限补丁”。
5. **M4 人类理解与能力恢复**：任务 8-9。解决“代码交给 AI 后人逐渐看不懂、不会判断”。
6. **M5 被动使用与正式发布**：任务 10-12。解决“系统有能力但用户忘记主动调用”。

每个里程碑都必须保持主分支测试通过；不能用后续任务掩盖前序门禁缺陷。

## 明确不在本次实现

- 不做操作系统级全局拦截。
- 不做后台常驻进程。
- 不做新的数据库或云端账户系统。
- 不做 AI 能力排行榜或虚假综合分数。
- 不强迫每个低风险任务都让用户答题。
- 不自动把源码、个人评价或敏感验证数据写入共享 Wiki。
- 不把 Markdown 打开次数当成用户价值，也不要求用户手工维护原子卡和投影。
- 不默认把全部项目控制文件、全部核心页或全部历史卡片交给模型。
- 不在本次建设在线知识管理 SaaS、移动客户端或多人协作编辑器。
- 不承诺“100% 理解全部代码”；系统保证的是变更可追踪、关键边界必须解释、风险必须有人负责、能力有机会被持续练习。
