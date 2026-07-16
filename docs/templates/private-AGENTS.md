# AGENTS.md

This workspace is the user's private ObsidianToWiki vault and durable knowledge store.

- vault_root: `{{PRIVATE_VAULT_ROOT}}`
- runtime_root: `{{PUBLIC_RUNTIME_ROOT}}`
- personal_index: `10_personal/索引.md`
- project_index: `20_projects/索引.md`
- shared_index: `30_shared/索引.md`
- output_index: `40_outputs/索引.md`

## Working Rules

- This is the Codex entrypoint for the private vault. Do not treat `CLAUDE.md` as its parent.
- Read `wiki.private.json` before accessing content and honor all AI access exclusions.
- Read `index.md` and the relevant layer or project index before durable writes.
- Keep raw sources immutable under `01_inbox/raw/`.
- Store personal knowledge in `10_personal/`, project memory in `20_projects/`, reusable knowledge in `30_shared/`, and generated analysis in `40_outputs/`.
- Never replace private knowledge with public scaffold content during an update.
- Use the public runtime at `runtime_root`; copied private scripts are compatibility assets, not the canonical executable.
