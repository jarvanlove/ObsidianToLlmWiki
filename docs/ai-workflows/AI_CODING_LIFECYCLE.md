# AI Coding Lifecycle

This project uses ObsidianToWiki's AI coding lifecycle protocol.

## Start

Before editing:

1. Read `wiki.context.json`.
2. Read project control files.
3. Read relevant project wiki pages.
4. State task boundary, risk level, expected touched files, and verification plan.

The agent invokes the lifecycle runtime internally; users only state their goal.

## Close

Before reporting completion:

1. Inspect the diff.
2. Record exact verification commands and results.
3. Update `TASKS.md`.
4. Check whether other control files or `docs/adr/` should change.
5. File back only durable conclusions to the wiki.

The agent records and resolves the close receipt internally before reporting completion.
