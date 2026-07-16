# ADR 0001: Local Runtime, Private Vault, and Versioned Project Bridges

- Status: Accepted
- Date: 2026-07-16

## Context

Manual onboarding required users to create a private vault, run several synchronization and migration scripts, install Skills, and reason about project reattachment. Updates could not distinguish core project bridges from optional adapters, and private scaffold files had no general baseline proving whether replacement was safe.

## Decision

Keep the public local runtime and private Markdown vault as separate sources of truth. Install one global Manager Skill per supported provider environment. Store real machine paths only in ignored user/project context. Version runtime, vault schema, private scaffold, core project scaffold, shared assets, and optional adapters separately.

The root installer performs one setup transaction. Later updates are explicit natural-language operations with clean-worktree and fast-forward Git preflight. Before pull, matching private files become baselines. Private files update only from an unchanged baseline; conflicts preserve the original, stage `.new`, and write a backup. Every registered core project bridge upgrades automatically; optional adapters remain opt-in.

## Consequences

- Normal users learn one install action and then use natural language.
- Existing projects do not require reattachment after product updates.
- Private customization has deterministic preservation and review evidence.
- A first update from a release predating baselines may stage more candidates, but it cannot silently overwrite private changes.
- The private vault remains usable without Git; receipts and backups provide update recovery evidence.
