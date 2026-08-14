# Remove HTML Cockpit and Rewrite README Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the local HTML/JSON cockpit completely while preserving read-only natural-language project status, then replace the oversized README with a concise product landing page that retains the Karpathy LLM-Wiki methodology, major product iterations, and current capabilities.

**Architecture:** Keep the existing privacy-bounded status projection as a read-only Python module used only by natural-language status answers. Remove all browser output, CLI cockpit commands, automatic cockpit generation, templates, screenshots, and visual-governance artifacts. Documentation will describe one product model: Git owns code, the private Markdown vault owns durable knowledge, and local ignored state supports execution without becoming product content.

**Tech Stack:** Python 3.10, Markdown, unittest/pytest, Git CLI, existing ObsidianToWiki runtime.

---

### Task 1: Preserve natural-language status without HTML

**Files:**
- Create: `00_system/scripts/project_status.py`
- Modify: `00_system/scripts/handle_nl_request.py`
- Modify: `00_system/scripts/project_session.py`
- Modify: `00_system/scripts/otw.py`
- Delete: `00_system/scripts/project_cockpit.py`
- Test: `tests/test_project_status.py`
- Test: `tests/test_project_concierge.py`
- Test: `tests/test_automatic_memory_lifecycle.py`
- Test: `tests/test_human_controlled_ai_e2e.py`
- Test: `tests/test_project_session_receipt.py`

1. Add tests proving “项目现在怎么样” returns bounded status and creates no HTML/JSON files.
2. Run the targeted tests and confirm they fail against the existing cockpit behavior.
3. Extract only the safe projection and text formatter into `project_status.py`.
4. Remove the `otw cockpit` parser and dispatcher, automatic cockpit generation, and cockpit-specific session fields.
5. Run the targeted tests and confirm they pass.

### Task 2: Delete all HTML cockpit assets and evidence

**Files:**
- Delete: `00_system/templates/cockpit/index.html`
- Delete: `00_system/templates/cockpit/styles.css`
- Delete: `docs/design/ui-tasks/human-control-cockpit.yaml`
- Delete: `docs/design/qa/human-control-cockpit.md`
- Delete: `docs/design/qa/human-control-cockpit-accessibility.md`
- Delete: `output/playwright/human-control-cockpit/`
- Delete: `tests/test_project_cockpit.py`

1. Delete the static rendering templates, generated screenshots, UI task, and QA evidence.
2. Search tracked files for cockpit HTML paths and confirm none remain.

### Task 3: Align product and lifecycle documentation

**Files:**
- Modify: `PRODUCT_SPEC.md`
- Modify: `ARCHITECTURE.md`
- Modify: `TASKS.md`
- Modify: `TESTING.md`
- Modify: `OPERATIONS.md`
- Modify: `CHANGELOG.md`
- Modify: `使用手册.md`
- Modify: `快速开始.md`
- Modify: `docs/templates/project-AGENTS.md`
- Modify: `docs/templates/project-CLAUDE.md`
- Modify: `docs/templates/global-skills/obsidiantowiki-manager/SKILL.md`
- Modify: `docs/templates/project-adapters/docs/ai-workflows/adapters.md`
- Modify: `tests/test_engineering_governance_contract.py`

1. Replace HTML cockpit promises with natural-language project status and bounded project memory.
2. Record removal in Unreleased and retain historical acceptance reports as historical evidence.
3. Verify current product documentation contains no claim that an HTML cockpit is generated.

### Task 4: Rewrite README as a product landing page

**Files:**
- Modify: `README.md`

1. Keep the Andrej Karpathy LLM-Wiki attribution and source link near the top.
2. Explain the product, the problem, and the public-runtime/private-wiki boundary in plain Chinese.
3. Add a compact timeline covering the initial scaffold, private project memory, structured ingestion/retrieval, safe productization, UI governance, and Human-Controlled AI Engineering 2.0.
4. List current capabilities without script-level detail or roadmap noise.
5. Keep installation, everyday natural-language examples, privacy boundary, and links to detailed guides.
6. Keep the README near 150-220 lines and confirm every claim matches current code.

### Task 5: Verify and file back

**Files:**
- Modify: relevant private Wiki project pages after verification.

1. Run targeted status, lifecycle, session, governance, and documentation tests.
2. Run the full test suite, strict Doctor, Python compilation, and `git diff --check`.
3. Search for live cockpit CLI/template/output references; allow only explicitly historical plan/acceptance records.
4. Update project control files and write the verified implementation summary to the private Wiki.
