# Accessibility Evidence: visual-direction-library

## Scope

This report covers the visual-direction registry and its static review page. It does not claim that a future product page is accessible merely because it chooses a listed palette.

## Color Rules

- Six defaults are selected from the reviewed registry; their source-pair contrast is recorded in the registry.
- Ten controlled directions require user selection and carry limits such as “large text/control only” where the original pair is below normal-text contrast.
- Three reference-only directions are rejected by the runtime as production baselines because their original pair contrast is below 3:1.
- All project UI work must use semantic text, surface, border, action, accent, and focus tokens. A source color pair is never automatically treated as a text/background pair.

## Review Evidence

- Desktop `1440x900`: `output/playwright/visual-direction-library/.playwright-cli/page-2026-07-20T04-07-00-896Z.png`
- Mobile `390x844`: `output/playwright/visual-direction-library/.playwright-cli/page-2026-07-20T04-07-07-033Z.png`
- Browser console: 0 errors and 0 warnings after the review page loaded.

## Result

Pass for the registry and preview artifact. Product-specific UI tasks still require their own actual foreground/background contrast evidence and keyboard/focus review.
