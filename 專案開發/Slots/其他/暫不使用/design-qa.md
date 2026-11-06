# Slot UI Design QA

- Source visual truth: the user's Help screenshots and latest FG board screenshot in the conversation (no local filesystem path available). The latest requested state is a visibly lighter blue background across the board region while FG is active.
- Implementation: `Project_AI/Slots/help_ui_standardizer.js`, loaded once by every current slot-game index: H013, H015, H019, H025, H026, H027, and H028.
- Implementation screenshot: unavailable; no in-app Browser tool is exposed in this session.
- Viewport: not captured.
- State: Help dialog open on the combined Paytable and Scatter section at Bet 1.00; latest additional state is the game board immediately after FG is triggered and during FG spins.
- Primary interactions tested: static JavaScript parsing and script-reference validation only.
- Console errors checked: not available without a browser-rendered session.

## Full-view comparison evidence

Blocked. The source screenshots are visible in the conversation, but a browser-rendered implementation screenshot could not be captured for side-by-side comparison.

## Focused region comparison evidence

Blocked. The normalized dialog chrome, title hierarchy, full-width light-blue panels, inset spacing, merged C1 payout row, table typography, and borders could not be visually compared across all seven games at a matching viewport.

## Findings

- [P2] Browser-rendered visual comparison unavailable.
  - Location: Help Paytable in all seven game indexes.
  - Evidence: code and script references validate, but there is no implementation screenshot.
  - Impact: spacing, overflow, and exact visual fidelity to the supplied reference cannot be certified.
  - Fix: open one representative Help dialog in the user's selected browser, capture the Paytable at Bet 1.00, and compare it with the supplied reference.
- [P2] Cross-game rendered consistency comparison unavailable.
  - Location: complete Help dialog in H013, H015, H019, H025, H026, H027, and H028.
  - Evidence: all three legacy Help structures now pass through one DOM and CSS normalizer, but seven matching browser captures are unavailable.
  - Impact: computed-style or viewport-specific differences caused outside the normalized Help subtree cannot be ruled out visually.
  - Fix: capture the same Help state and viewport in all seven games and compare dialog size, spacing, typography, colors, tables, and overflow behavior.
- [P2] FG board color comparison unavailable.
  - Location: `#grid-panel` in H013, H015, H019, H025, H026, H027, and H028.
  - Evidence: all seven games now toggle the shared `fg-mode` state and use the same `#174a70` board-region background, but no browser-rendered FG screenshot was captured.
  - Impact: the precise perceived brightness and contrast against each game's symbols cannot be certified visually.
  - Fix: trigger FG in each game at the same viewport and compare the board background, symbol contrast, message bar, and transition back to BG.

## Required fidelity surfaces

- Fonts and typography: fixed to the same Segoe UI/Arial stack, 600-weight green headings, sizes, line heights, alignment, and Title Case normalization in all seven games; visual verification blocked.
- Spacing and layout rhythm: inset card padding, rule-panel spacing, full-width table panels, responsive horizontal scrolling, and table margins implemented; visual verification blocked.
- Colors and visual tokens: existing `--text`, `--line`, `--blue`, and `--accent` tokens reused, with the same translucent light-blue background applied to rule and table panels; visual verification blocked.
- Image quality and asset fidelity: no image assets are used in this table component.
- Copy and content: `Paytable (Current Bet: 1.00)`, `Symbol`, Title Case normalization, and combined C1 payout rows implemented; visual verification blocked.

## Comparison history

- Initial pass: blocked because no browser-rendered implementation capture is available.
- Current pass: normalized the entire dialog shell and Help subtree; legacy cards, direct paragraphs, payout grids, div-based payout tables, and HTML tables now converge on the same classes and fixed visual tokens. Browser comparison remains blocked.
- Typography refinement: reduced all green section and group headings from 800 to 600 weight without changing their size, color, or spacing. Browser comparison remains blocked.
- FG board refinement: added one shared light-blue `#grid-panel` state with a subtle blue inset border and transition; added the missing `fg-mode` toggle to H025. Browser comparison remains blocked.
- H015 FG-state correction: the active `Source/demogame.js` runtime maintained a separate FG state and did not toggle `fg-mode`; its `updateStats()` now derives the class from `state.fg.remaining`, including trigger, subsequent FG spins, completion, and reset. Browser comparison remains blocked.

## Final result

final result: blocked
