# Accessibility Evidence: human-control-cockpit

## Result

- Verdict: Pass
- Viewports: 1440x900 and 390x844
- Browser: Chromium through Playwright CLI

## Keyboard and Structure

- The first Tab stop is the visible “跳到主要内容” skip link targeting `#main`.
- Every evidence item uses native `details/summary`; Enter opens the selected disclosure.
- Playwright confirmed the focused summary has a `3px` `#1660AB` outline.
- The page exposes one `h1`, five ordered `h2` region headings, landmark `main`, banner, and content information.

## Contrast and Responsive Evidence

- Approved baseline pair `#66D3C0` on `#3C4252` has recorded contrast `5.56:1`.
- Primary text uses `#17212B` on white/light surfaces; muted text uses `#52616B` only for secondary metadata.
- The 390px check returned `scrollWidth=390` and `clientWidth=390`, so there is no horizontal overflow.
- `prefers-reduced-motion` users receive no entrance animation.

## Privacy

- Generated HTML contains no source code, secret values, or private absolute paths.
- Git evidence contains only bounded changed-file labels; Context Receipt evidence uses a hash and repository-relative receipt path.
