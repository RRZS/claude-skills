# Accessibility & Touch — The Two CRITICAL Rules

The skill's two non-negotiable categories are **Accessibility** (Priority 1) and **Touch & Interaction** (Priority 2). Failing either typically makes a product unusable for ≥ 15% of users, ships a regulatory liability in regulated markets, and is the most common reason an otherwise polished UI looks unprofessional in audit.

## Accessibility Floor — What "Pass" Means

| Check | Threshold | Source |
|-------|-----------|--------|
| Body text contrast | ≥ 4.5:1 | WCAG 2.2 SC 1.4.3 (Level AA) |
| Large text contrast (≥ 24px or 18.66px bold) | ≥ 3:1 | WCAG 2.2 SC 1.4.3 |
| Non-text UI contrast | ≥ 3:1 | WCAG 2.2 SC 1.4.11 |
| Focus indicator | Visible, ≥ 2px, ≥ 3:1 from background | WCAG 2.2 SC 2.4.7 + 2.4.13 |
| Keyboard operability | All controls reachable + operable | WCAG 2.2 SC 2.1.1 |
| Reduced motion | Honor `prefers-reduced-motion` | WCAG 2.2 SC 2.3.3 (AAA) + Apple HIG / Material 3 |
| Alt text | Descriptive for meaningful images, empty (`alt=""`) for decorative | WCAG 2.2 SC 1.1.1 |
| Form labels | Programmatically associated (`<label for>` or `aria-label`) | WCAG 2.2 SC 1.3.1, 3.3.2 |
| Color independence | Info conveyed by something besides color | WCAG 2.2 SC 1.4.1 |

These are floor values. The skill defaults to WCAG AA across all generated palettes — the `colors.csv` rows are pre-vetted to hit ≥ 4.5:1 on the primary on-primary pair. When the generator suggests an accent color that fails, it surfaces the failure in the pre-delivery checklist.

## Why 44×44 — Touch Target Minimum

| Platform | Minimum | Spacing |
|----------|---------|---------|
| iOS | 44×44 pt | 8 pt between targets |
| Material Design (Android) | 48×48 dp | 8 dp between targets |
| Web (WCAG 2.2 SC 2.5.8) | 24×24 CSS px | — (AA target size) |
| Web (Apple HIG / Best Practice) | 44×44 CSS px | 8 px between targets |

The skill uses the **stricter Apple value** (44×44 pt) as the default. Reason: CSS pixels at standard 1.0 device pixel ratio fail Fitts's law for finger input below ~40px. The WCAG 24px floor is a minimum, not a target.

Hit-slop / hitTestPadding extends the touchable area beyond the visual bounds — used when the visual icon must be smaller (e.g., 24×24 SVG icon button) but still hit a 44×44 touch zone. This is the standard pattern in React Native (`hitSlop`), SwiftUI (`contentShape`), and Flutter (`materialTapTargetSize`).

## Common Failure Modes (And the Fix)

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Focus ring removed for "clean look" | `outline: none` without replacement | Replace with custom 2–4px focus ring; use `:focus-visible` for keyboard-only |
| Icon button reads as "button button button" | Missing `aria-label` | Add `aria-label="<verb> <noun>"` — "Open menu", "Delete row" |
| Light gray on white body text | Designer used #999 for "muted" | Switch to ≥ #595959 on white (matches WCAG 4.5:1) |
| Hover-only menu disappears for touch users | No tap path | Add tap-toggle alternative; verify on iPad |
| Animation jank on low-end devices | No `prefers-reduced-motion` | Wrap animations in `@media (prefers-reduced-motion: no-preference)` |
| Text grows but layout breaks | Fixed heights | Use min-height, flex/grid auto-sizing, no truncated buttons |
| Tab order skips around | DOM order ≠ visual order | Fix DOM order; avoid `tabindex` > 0 |
| Modal traps screen reader behind backdrop | Backdrop not `aria-hidden` | Apply `aria-hidden="true"` to non-modal siblings; `inert` if supported |
| Forms shows errors only at the top | Error not associated with field | Use `aria-describedby` pointing to the per-field error |
| Color-only error indication | Red border without icon/text | Add icon + text — "Email is required" |

## Touch & Interaction Defaults

| Concern | Default | Rationale |
|---------|---------|-----------|
| Tap feedback latency | 80–150 ms | Below 80 ms feels instant (no perceived feedback); above 150 ms feels laggy |
| Animation duration | 150–300 ms | Apple HIG sweet spot; matches Material 3 motion-medium tokens |
| Easing | Platform-native (ease-in-out, spring) | Linear feels mechanical; long ease-out feels heavy |
| Loading button | Disabled + spinner | Prevents double-submit; signals async state |
| Gesture exclusivity | One primary gesture per region | Avoids nested tap/drag conflicts |
| Hit area expansion | `hitSlop` / `contentShape` to 44 pt | Lets visual icons be small while staying tappable |

## Why Both Rules Are CRITICAL, Not Important

A button users can't see (low contrast) and a button users can't tap (small target) have the same effect: the feature doesn't exist for them. Every other quality concern (style consistency, animation polish, copy clarity) is irrelevant downstream of these two. That's why the generator's pre-delivery checklist surfaces both first, before color or typography review.

## Sources

1. W3C WCAG 2.2 — Web Content Accessibility Guidelines 2.2 (W3C Recommendation, 2023). Authoritative source for the contrast / focus / keyboard / target-size criteria: https://www.w3.org/TR/WCAG22/
2. W3C ARIA Authoring Practices Guide (APG) — pattern library for ARIA roles + keyboard interaction: https://www.w3.org/WAI/ARIA/apg/
3. Apple Human Interface Guidelines — "Accessibility" + "Layout" sections (developer.apple.com/design/human-interface-guidelines). Source of the 44×44pt touch target and motion guidance.
4. Google Material Design 3 — "Accessibility" + "Motion" (https://m3.material.io/foundations/accessible-design). Source of the 48dp Android target and motion-medium tokens.
5. WebAIM — "WebAIM Million" annual analysis of the top 1M home pages + contrast checker (https://webaim.org/). Authoritative real-world data on accessibility failure rates.
6. Heydon Pickering — *Inclusive Components* (https://inclusive-components.design/) + *Inclusive Design Patterns*. The reference text for accessible component implementation.
7. US Access Board — Section 508 standards (https://www.access-board.gov/ict/). Federal procurement floor for accessibility in the US.
8. Nielsen Norman Group — "Accessibility" research library (https://www.nngroup.com/topic/accessibility/). Industry research on cost-of-failure and real user impact.
