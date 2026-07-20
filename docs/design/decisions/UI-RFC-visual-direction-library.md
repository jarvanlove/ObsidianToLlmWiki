# Design RFC: 内置受控视觉方向色库：19 组来源色卡、6 组默认方向和无障碍 token 治理

## Status

Approved on 2026-07-20.

## Problem

The UI governance runtime blocked unapproved design changes but gave an AI no trustworthy visual starting point when a project had no approved screenshots or design files. A model could therefore choose arbitrary colors, making otherwise compliant UI work visually inconsistent.

## Evidence

- The user supplied 19 reviewed Chinese/brand palette pairs and asked that they be retained rather than reduced to an arbitrary single theme.
- Direct pair contrast review shows ten pairs at or above 4.5:1, six that are suitable only for large text or controls, and three decorative pairs below 3:1.
- The original source image for palette 17 places its two names and hex values in opposite positions; the registry records the visually correct mapping and flags the correction.

## Proposed Decision

1. Store all 19 reviewed pairs in a public, auditable visual-direction registry; do not copy the user's source images or local paths.
2. Mark six directions as defaults: 深海铜, 雾青玄, 橙炭, 纸本棕, 酒红暖白, 宣纸鸢尾.
3. Use 雾青玄 as the deterministic fallback when a project has neither an approved reference nor an existing baseline.
4. Keep ten additional directions selectable only with a recorded user choice; keep three low-contrast pairs reference-only.
5. Persist the first approved U1+ direction as `docs/design/UI_VISUAL_BASELINE.json`. U1/U2 cannot replace it; an approved U3 RFC can.
6. Require semantic UI tokens and prohibit ad hoc color-chart hex values in implementation.

## Alternatives Considered

- Keep only six palettes: rejected because it discards reviewed visual material and narrows future product fit.
- Let the model choose among all 19: rejected because it recreates the random "blind box" behavior.
- Generate unlimited themes from RGB/RYB primaries: deferred. The source pairs are compositional references, not a sufficient accessibility-tested generative system.

## System Impact

- Tokens: registry provides shared surface/text/border/focus tokens and direction anchors; projects freeze the selected baseline locally.
- Components: no component library or dependency is added.
- Patterns: no-reference tasks use a fixed fallback; controlled choices need a user-selection note.
- Responsive behavior: the visual direction preview is reviewed at 1440x900 and 390x844.
- Accessibility: pair contrast classification limits unsafe pairs; actual foreground/background combinations remain subject to task-level validation.
- Performance: one local JSON registry and a static reference page; no runtime network request.
- Skill and evaluation rules: named UI Skills remain candidate/executor-only; the registry is deterministic project policy, not Design Authority.

## Migration

New U1+ tasks create a baseline automatically. Existing projects retain their current facts until a task explicitly initializes or approves a visual baseline; no project UI file is bulk-rewritten.

## Validation and Approvals

- Product-owner approval: user explicitly chose “19 组全量入库，6 组作为无参考时的可靠默认值，其余按规则可选；未来再扩展新的色相家族” and confirmed that AI should default only to stable themes while users select the rest by temperament.
- Runtime tests: `python -m unittest tests.test_ui_governance -v`.
- Visual review: browser screenshots at desktop and mobile viewports, plus a zero-console-error review.
