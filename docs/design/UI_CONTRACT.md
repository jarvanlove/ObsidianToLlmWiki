---
title: Product UI Contract
status: approved
updated: 2026-07-20
---

# Product UI Contract

## Design Authority

Visual sources are authoritative in this order:

1. Approved Golden Screens or approved Figma nodes.
2. Product goals, user tasks, real content, and accessibility needs.
3. Project design tokens, product components, and interaction patterns.
4. Approved Design RFCs and decisions.
5. Project UI Skill Registry.
6. Generic or third-party UI Skills, library defaults, and model preferences.

Lower-priority sources must not override higher-priority sources.

## Project Facts

- Design Authority owner: ObsidianToWiki product maintainer; the user approved the 19-source/6-default decision in the task conversation.
- Approved Figma sources: None.
- Approved Stitch directions: None.
- Component entrypoint: `00_system/scripts/ui_governance.py`.
- Token source: `00_system/registry/ui_visual_directions.json` plus its shared semantic tokens.
- Browser verification command: Playwright CLI against `docs/design/references/visual-direction-library.html` through a local loopback server.
- Screenshot location: `output/playwright/visual-direction-library/`.
- Accessibility verification command: source-pair contrast review in the direction registry and `docs/design/qa/visual-direction-library-accessibility.md`.

## Approved Visual Direction

- Direction policy: retain all 19 reviewed sources; use the six default directions only when no reference exists; require a recorded user selection for controlled directions.
- Fixed no-reference fallback: `mist-teal-ink` / 雾青玄.
- Baseline mutation: U1/U2 retain the current baseline; only an approved U3 RFC may replace it.
- Source-image handling: the user-provided image files stay outside the public repository; the registry stores only reviewed color facts and use constraints.

## Implementation Boundaries

- Reuse approved project components and tokens before adding a new visual value.
- Do not change information architecture or visual direction during implementation.
- Do not install a UI library, icon set, font, or visual baseline without an approved Design RFC.
- Do not update a Golden Screen or screenshot baseline without explicit approval.
- A named third-party UI Skill may propose or execute only the role recorded in `UI_SKILL_REGISTRY.yaml`.

## Required States

When relevant, cover default, hover, active, focus-visible, disabled, loading, empty, error, success, permission, long-content, and responsive states.

## Evidence

Material UI work needs fixed-viewport browser screenshots, a Visual QA report, accessibility evidence, and explicit Design Authority approval before release.
