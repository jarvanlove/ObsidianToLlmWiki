---
title: Product UI Contract
status: draft
updated: {{TODAY}}
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

- Design Authority owner: TODO
- Approved Figma sources: TODO
- Approved Stitch directions: TODO
- Component entrypoint: TODO
- Token source: TODO
- Browser verification command: TODO
- Screenshot location: TODO
- Accessibility verification command: TODO

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
