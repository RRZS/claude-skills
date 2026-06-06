---
name: ui-ux-pro-max
description: Design intelligence skill that generates complete design systems on demand — pattern + style + colors + typography + effects + anti-patterns — from 161 industry-specific reasoning rules, 67 UI styles, 161 color palettes, 57 font pairings, 99 UX guidelines, 25 chart types, and stack guidelines for 16 web/mobile/3D stacks. Use when building landing pages, dashboards, mobile apps, or any UI; selecting style, palette, or typography; reviewing UI for accessibility, contrast, touch targets, or anti-patterns; or implementing stack-specific best practices (React, Next.js, Vue, Nuxt, Svelte, Angular, Astro, Laravel, SwiftUI, Jetpack Compose, React Native, Flutter, Three.js, html+tailwind, shadcn).
license: MIT
metadata:
  derived_from: "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill"
  original_author: "NextLevelBuilder (Goon Nguyen / @mrgoonie)"
  original_license: MIT
  upstream_version: "2.5.0"
  voice: "NextLevelBuilder — practical, opinionated, anti-pattern-aware, stack-fluent"
  version: 1.0.0
  category: design
---

# UI/UX Pro Max — Design Intelligence

> Derived from [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (MIT). Upstream data, scripts, and voice preserved verbatim per the MIT license. Additions: deep references citing ≥5 sources each, stdlib data-integrity validator, `cs-ui-ux-pro-max-advisor` agent, `/cs:ui-ux-review` command.

## Use When

Activate this skill when the request involves:

| Trigger | Start From |
|---------|------------|
| New page or app (landing, dashboard, mobile app) | Step 1 → Step 2 (design system) |
| New component (card, modal, form, chart) | Step 3 (domain search) |
| Choosing style / color / font for a product type | Step 2 (design system) |
| Reviewing existing UI for a11y / contrast / anti-patterns | [Quick reference](references/quick-reference.md) §1–3 |
| Stack-specific implementation (React, SwiftUI, Flutter, etc.) | Step 4 (stack search) |
| Persisting design rules across sessions | Step 2b (`--persist`) |

**Skip** when: pure backend, API-only, infrastructure, or non-visual scripting.

## Prerequisites

Python 3.x. No third-party packages required (stdlib only).

```bash
python3 --version
```

## Workflow

### Step 1 — Read the request

Extract: product type (SaaS / fintech / e-commerce / wellness / etc.), audience, style keywords (minimal / vibrant / dark / playful), target stack.

### Step 2 — Generate a design system (REQUIRED first pass)

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "<product_type> <industry> <keywords>" --design-system -p "Project Name"
```

Returns: pattern + style + colors + typography + key effects + anti-patterns + pre-delivery checklist. Reasoning rules in `data/ui-reasoning.csv` filter style/color/typography to the industry.

### Step 2b — Persist (optional, for multi-session work)

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Project Name" [--page "checkout"]
```

Creates `design-system/MASTER.md` (global tokens) + `design-system/pages/<page>.md` (page-level overrides). Page rules override MASTER when present.

### Step 3 — Domain deep-dive (as needed)

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "<keyword>" --domain <product|style|color|typography|landing|chart|ux|react|web|prompt>
```

### Step 4 — Stack-specific guidance

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "<keyword>" --stack <react|nextjs|vue|nuxtjs|nuxt-ui|svelte|angular|astro|laravel|swiftui|jetpack-compose|react-native|flutter|threejs|html-tailwind|shadcn>
```

## Three Non-Negotiable Rules

1. **Accessibility (CRITICAL)** — 4.5:1 contrast, visible focus, alt text, keyboard nav, `prefers-reduced-motion`.
2. **Touch & interaction (CRITICAL)** — 44×44pt minimum, 8pt+ spacing, clear loading feedback, no hover-only paths.
3. **Performance (HIGH)** — WebP/AVIF, lazy-load, reserve space (CLS < 0.1), virtualize lists ≥50 items.

See [accessibility-and-touch.md](references/accessibility-and-touch.md) for the WCAG / HIG / Material foundations. The 9-item pre-delivery checklist lives at the bottom of [quick-reference.md](references/quick-reference.md).

## References (one level deep)

- [quick-reference.md](references/quick-reference.md) — Inline cheat sheet from upstream (296 lines, 10 priority categories)
- [full-skill-playbook.md](references/full-skill-playbook.md) — Full upstream playbook with workflow, search domains, stacks, anti-patterns
- [design-system-foundations.md](references/design-system-foundations.md) — Why the design-system-generator works (atomic design + tokens + industry pattern matching)
- [accessibility-and-touch.md](references/accessibility-and-touch.md) — WCAG / Apple HIG / Material foundations for the CRITICAL rules
- [style-color-typography.md](references/style-color-typography.md) — How styles, palettes, and pairings were selected
- [stack-specific-guidance.md](references/stack-specific-guidance.md) — Why one CSV per stack

## Related

Agent: [`cs-ui-ux-pro-max-advisor`](../../../../agents/product/cs-ui-ux-pro-max-advisor.md) · Command: [`/cs:ui-ux-review`](../../../../commands/ui-ux-review.md) · Adjacent: `apple-hig-expert`, `ui-design-system`, `landing-page-generator`.

**Version:** 1.0.0 (upstream v2.5.0) — Derived from nextlevelbuilder/ui-ux-pro-max-skill (MIT)
