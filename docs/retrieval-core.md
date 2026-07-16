# Retrieval Core

## Boundary

Markdown remains the only source of truth. The SQLite database under `00_system/.cache/` is disposable derived data and can always be rebuilt.

The retrieval core owns deterministic behavior shared by all future agent/API adapters:

- Markdown freshness detection
- project, page type, and tag filters
- existing page-value weighting
- best matching heading and bounded snippet
- page path plus `source_notes` and `source_refs` provenance
- stable JSON and context-pack output

Agents remain responsible for query interpretation, iterative follow-up searches, reasoning, and final answers.

## Commands

Build or incrementally refresh the index:

```powershell
python .\00_system\scripts\build_retrieval_index.py
```

Force all Markdown pages to be parsed again:

```powershell
python .\00_system\scripts\build_retrieval_index.py --full
```

Return structured results for an agent:

```powershell
python .\00_system\scripts\search_wiki.py "权限设计" --project demo --format json
```

Return a bounded Markdown context pack:

```powershell
python .\00_system\scripts\search_wiki.py "权限设计" --project demo --format context --token-budget 4000
```

Search refreshes changed and deleted Markdown pages by default. `--no-refresh` is intended only for controlled diagnostics.

## Quality Gate

```powershell
python .\00_system\scripts\evaluate_retrieval.py --cases .\00_system\registry\retrieval_eval_cases.json
```

The command gates path, heading, provenance, pass rate, and MRR. Semantic probes are reported separately. Inspectable topic aliases cover measured synonym gaps before heavier infrastructure is considered.

## Current Limits

- Page scoring remains local and combines lexical coverage, existing page weights, and configured topic aliases.
- FTS5 is used for heading/chunk localization, not embedding-based semantic understanding.
- Token budgets are local estimates, not provider-specific tokenizer counts.
- Project Skills and the optional MCP stdio server consume this contract without redefining retrieval.
- Embeddings, semantic reranking, and file watchers remain out of scope while semantic probes pass.
