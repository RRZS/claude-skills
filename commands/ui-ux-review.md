---
name: "cs-ui-ux-review"
description: "/cs:ui-ux-review <feature-or-page> — 6-question forcing UI/UX gate before any visual implementation ships. Refuses single-axis recommendations (color-only, font-only) and demands the full design-system context. Backed by the ui-ux-pro-max skill's 161 reasoning rules + 67 styles + 161 palettes."
---

# /cs:ui-ux-review — UI/UX Forcing Questions

**Command:** `/cs:ui-ux-review <feature-or-page>`

The ui-ux-pro-max-advisor persona pressure-tests any UI implementation before it ships. Six forcing questions matching the upstream pre-delivery checklist + the two CRITICAL rules.

## When to Run

- Before implementing a new page, screen, or app
- Before merging a PR that adds or changes visible UI
- When auditing an existing surface for accessibility / anti-patterns
- When a stakeholder says the UI "looks off" but can't articulate why

## The Six UI/UX Questions

### 1. What's the product type, audience, and target stack?
**Style, palette, and typography are downstream of these three answers.**
- Product type: SaaS / fintech / wellness / e-commerce / dashboard / portfolio / gaming / etc.
- Audience: B2B vs B2C; consumer demographics; technical literacy
- Stack: React / Next.js / Vue / SwiftUI / Flutter / etc.
- If any of these is "we'll figure it out as we go," stop and answer them first.

### 2. Have you generated the design system, or are you picking colors and fonts in isolation?
**Isolated recommendations ship inconsistent UI.**
- Run `python3 .../search.py "<product_type> <industry> <keywords>" --design-system -p "Project"` first
- Get pattern + style + colors + typography + effects + anti-patterns as one output
- If you only have a color, you have nothing — re-run with the full design-system context

### 3. What anti-patterns does `ui-reasoning.csv` flag for your industry?
**Industry-specific anti-patterns are the most overlooked design failure mode.**
- Fintech: AI purple/pink gradients (signals rushed AI startup, not bank-grade)
- Healthcare: bright neon (clinical context demands restraint)
- Wellness: pure dark mode (warmth demands light-leaning palette)
- Banking: playful illustrations (trust signaling is the conversion lever)
- The generator surfaces these inline — read them, don't skip past

### 4. Do the two CRITICAL rules pass?
**Accessibility + touch are not "nice to have"; failing either makes the feature non-existent for ≥ 15% of users.**
- Body text contrast ≥ 4.5:1 (WCAG 2.2 SC 1.4.3)
- Touch targets ≥ 44×44 pt (Apple HIG) with 8 pt+ spacing
- Focus rings visible (≥ 2px, ≥ 3:1 contrast)
- Keyboard order matches visual order
- `prefers-reduced-motion` honored

### 5. Is the stack-specific guidance applied?
**Cross-stack rules generalize poorly — "always memoize" is wrong in Svelte 5 and right in React.**
- Run `python3 .../search.py "<feature>" --stack <your-stack>`
- React: selective memoization, not reflexive
- Svelte 5: runes-first reactivity, no legacy `$:`
- React Native: hitSlop for sub-44 visual icons
- SwiftUI: `@State` only for view-local; `@StateObject` for owning view models
- Use the stack idioms; don't port idioms from a different stack

### 6. Does the pre-delivery checklist pass?
**Nine items. If any fails, the UI ships looking unprofessional.**
- [ ] No emoji as icons (SVG only — Phosphor / Heroicons / Lucide)
- [ ] Touch targets ≥ 44×44 pt with 8 pt+ spacing
- [ ] Contrast ≥ 4.5:1 body, ≥ 3:1 large + UI
- [ ] Focus rings visible (2–4px); keyboard order matches visual
- [ ] Dark mode tested independently (not inferred from light)
- [ ] `prefers-reduced-motion` honored
- [ ] Responsive at 375 / 768 / 1024 / 1440 px; safe areas respected
- [ ] Semantic color tokens (no hardcoded hex in components)
- [ ] Loading and error states defined for every async path

## Workflow

```bash
# 0. Sanity check the data bundle
python3 product-team/ui-ux-pro-max/skills/ui-ux-pro-max/scripts/data_integrity_check.py

# 1. Generate the design system (REQUIRED)
python3 product-team/ui-ux-pro-max/skills/ui-ux-pro-max/scripts/search.py "<product> <industry> <keywords>" --design-system -p "Project"

# 2. Persist for multi-session work
python3 product-team/ui-ux-pro-max/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Project"

# 3. Stack-specific guidance
python3 product-team/ui-ux-pro-max/skills/ui-ux-pro-max/scripts/search.py "<feature>" --stack <stack>

# 4. Domain deep-dive (per failing axis)
python3 product-team/ui-ux-pro-max/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --domain <product|style|color|typography|landing|chart|ux|react|web|prompt>
```

## Output Format

```markdown
# UI/UX Review: <feature-or-page>
**Date:** YYYY-MM-DD

## The Decision Being Made
[greenfield | extend | audit | refactor]

## Context
- Product type: <type>
- Audience: <segment>
- Target stack: <stack>

## Generated Design System
- PATTERN: <name>
- STYLE: <name>
- COLORS: primary <hex>, accent <hex>, background <hex>
- TYPOGRAPHY: <heading> / <body>
- KEY EFFECTS: <effects>
- ANTI-PATTERNS TO AVOID: <list from ui-reasoning.csv>

## Two CRITICAL Rules
- Contrast: PASS/FAIL — <ratio>
- Touch targets: PASS/FAIL — <pt minimum verified>
- Focus rings: PASS/FAIL — <thickness + contrast>
- Keyboard order: PASS/FAIL
- prefers-reduced-motion: PASS/FAIL

## Stack-Specific Idioms
- <stack>: <key rules from stack CSV>
- Anti-patterns avoided: <list>

## Pre-Delivery Checklist
- [x|/] 1. No emoji as icons
- [x|/] 2. Touch targets ≥ 44×44 pt
- [x|/] 3. Contrast ≥ 4.5:1
- [x|/] 4. Focus rings visible
- [x|/] 5. Dark mode tested independently
- [x|/] 6. prefers-reduced-motion honored
- [x|/] 7. Responsive 375/768/1024/1440
- [x|/] 8. Semantic color tokens
- [x|/] 9. Loading + error states

## Verdict
🟢 SHIP | 🟡 WARN-WITH-JUSTIFICATION | 🔴 BLOCK

## Top 3 Actions (if not green)
[3 concrete fixes with file:line + token names]
```

## Routing

- `/cs:karpathy-check` — code-quality concerns in the implementation
- `/cs:focused-fix` — when an entire feature/module needs systematic UI repair
- `/cs:plugin-audit` — when shipping the UI/UX skill itself to ClawHub

## Related

- Agent: [`cs-ui-ux-pro-max-advisor`](../agents/product/cs-ui-ux-pro-max-advisor.md)
- Skill: [`ui-ux-pro-max`](../product-team/ui-ux-pro-max/skills/ui-ux-pro-max/SKILL.md)
- Adjacent: `apple-hig-expert` (Apple HIG), `ui-design-system` (token generator), `landing-page-generator` (TSX scaffolder)

---

**Version:** 1.0.0
**Derived:** nextlevelbuilder/ui-ux-pro-max-skill (MIT) + this repo's wrapper
