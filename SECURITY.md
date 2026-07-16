# Security Policy

## Scope

This repository contains templates, scripts, and documentation for an LLM-maintained Obsidian wiki.

Security-sensitive areas include:

- script execution behavior
- source ingestion logic
- file path handling
- generated content that may include unsafe external input
- local AI-access exclusion policy and retrieval boundaries
- upgrade/migration overwrite behavior
- Git update and installer command execution
- private scaffold baseline, candidate, backup, and receipt integrity

## Reporting

If you find a security issue, do not open a public issue with exploit details.

Instead, report it privately to the repository maintainer using the project's preferred private contact channel.

## Examples of Relevant Issues

- path traversal
- unsafe shell invocation
- prompt injection handling gaps
- unsafe external file ingestion behavior
- accidental disclosure of local file paths or secrets

## Local Private Policy

`wiki.private.json` can exclude exact vault paths or globs from ObsidianToWiki indexing and ingestion. Excluded files remain untouched and can still be opened manually in Obsidian or another local editor.

This policy only governs ObsidianToWiki code paths. It does not prevent Codex, Claude Code, Cursor, MCP servers, backup software, or other processes from reading a file directly when those tools have filesystem access. Configure each external tool's workspace permissions separately for OS-level isolation.

Malformed private policy fails closed for ObsidianToWiki operations. Never commit the real policy when its path list is sensitive; only the example template belongs in the public repository.

Automatic product update accepts only a clean public worktree and fast-forward Git history. It does not stash, reset, checkout over local work, or execute a force pull. Private managed files require a matching recorded hash before replacement; conflicts preserve the original and write both a candidate and backup.

The private policy is not a cloud-exfiltration boundary. An AI coding tool with filesystem access may still read local files outside ObsidianToWiki. Limit each provider's workspace roots, MCP permissions, and tool approvals independently.
