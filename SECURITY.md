# Security Policy

## Scope

This repository contains templates, scripts, and documentation for an LLM-maintained Obsidian wiki.

Security-sensitive areas include:

- script execution behavior
- source ingestion logic
- file path handling
- generated content that may include unsafe external input

## Reporting

If you find a security issue, do not open a public issue with exploit details.

Instead, report it privately to the repository maintainer using the project's preferred private contact channel.

## Examples of Relevant Issues

- path traversal
- unsafe shell invocation
- prompt injection handling gaps
- unsafe external file ingestion behavior
- accidental disclosure of local file paths or secrets
