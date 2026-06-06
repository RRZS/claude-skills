# UI/UX Pro Max — Design Intelligence Skill

> Derived from [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (MIT). See [NOTICE.md](NOTICE.md) for full attribution.

A complete design intelligence skill: **161 industry-specific reasoning rules**, **67 UI styles**, **161 color palettes**, **57 font pairings**, **99 UX guidelines**, **25 chart types**, and **stack-specific guidance for 16 web/mobile/3D frameworks**. Generates a complete design system on demand using BM25 retrieval + industry reasoning rules — no LLM calls, stdlib only.

## What It Does

Given a free-text product description, the skill emits a complete design system:

```
TARGET: Serenity Spa - RECOMMENDED DESIGN SYSTEM
PATTERN: Hero-Centric + Social Proof
STYLE: Soft UI Evolution
COLORS:  Primary #E8B4B8 (Soft Pink), Secondary #A8D5BA (Sage), CTA #D4AF37 (Gold)
TYPOGRAPHY: Cormorant Garamond / Montserrat
KEY EFFECTS: Soft shadows + 200-300ms transitions + Gentle hover states
AVOID: Bright neon + Harsh animations + Dark mode + AI gradients
PRE-DELIVERY CHECKLIST: [9 items]
```

## Quick Start

```bash
# Generate a design system
python3 skills/ui-ux-pro-max/scripts/search.py "fintech banking trust" --design-system -p "Bank App"

# Search a specific domain
python3 skills/ui-ux-pro-max/scripts/search.py "glassmorphism dark" --domain style
python3 skills/ui-ux-pro-max/scripts/search.py "real-time dashboard" --domain chart

# Stack-specific guidance
python3 skills/ui-ux-pro-max/scripts/search.py "list virtualization" --stack react
python3 skills/ui-ux-pro-max/scripts/search.py "safe-area gesture" --stack react-native

# Persist for multi-session work (Master + Overrides pattern)
python3 skills/ui-ux-pro-max/scripts/search.py "SaaS dashboard" --design-system --persist -p "MyApp" --page "dashboard"
```

## Structure

```
ui-ux-pro-max/
├── .claude-plugin/plugin.json
├── NOTICE.md                              # Attribution
├── UPSTREAM-LICENSE                       # Upstream MIT license
├── README.md                              # This file
└── skills/ui-ux-pro-max/
    ├── SKILL.md                           # < 100 lines, YAML frontmatter
    ├── data/                              # 15 main CSVs + 16 stack CSVs
    │   ├── ui-reasoning.csv               # 161 industry reasoning rules
    │   ├── styles.csv                     # 67 UI styles
    │   ├── colors.csv                     # 161 palettes (17 token roles each)
    │   ├── typography.csv                 # 57 Google Fonts pairings
    │   ├── ux-guidelines.csv              # 99 best practices
    │   ├── charts.csv                     # 25 chart types
    │   ├── landing.csv                    # Landing page patterns
    │   ├── google-fonts.csv               # Font catalogue
    │   ├── products.csv, design.csv, draft.csv, icons.csv,
    │   ├── app-interface.csv, react-performance.csv
    │   └── stacks/                        # 16 stack-specific CSVs
    │       ├── react.csv, nextjs.csv, vue.csv, nuxtjs.csv,
    │       ├── nuxt-ui.csv, svelte.csv, astro.csv, angular.csv,
    │       ├── shadcn.csv, html-tailwind.csv, laravel.csv,
    │       ├── swiftui.csv, jetpack-compose.csv,
    │       ├── react-native.csv, flutter.csv, threejs.csv
    ├── scripts/
    │   ├── search.py                      # CLI entry point
    │   ├── core.py                        # BM25 + retrieval
    │   ├── design_system.py               # Design system reasoning engine
    │   └── data_integrity_check.py        # Stdlib validator (this wrapper)
    └── references/
        ├── full-skill-playbook.md         # Upstream playbook (verbatim)
        ├── quick-reference.md             # Upstream quick reference (verbatim)
        ├── design-system-foundations.md   # Wrapper deep-dive (8 sources)
        ├── accessibility-and-touch.md     # Wrapper deep-dive (8 sources)
        ├── style-color-typography.md      # Wrapper deep-dive (8 sources)
        └── stack-specific-guidance.md     # Wrapper deep-dive (10 sources)
```

## Supported Stacks

**Web:** HTML + Tailwind, React, Next.js, Vue, Nuxt.js, Nuxt UI, Svelte, Astro, Angular, shadcn/ui, Laravel
**Mobile:** SwiftUI (iOS), Jetpack Compose (Android), React Native, Flutter
**3D:** Three.js

## Wrapper Additions

This wrapper preserves the upstream voice + data verbatim and adds:

- **Concise SKILL.md** with progressive disclosure (under 100 lines)
- **4 deep-dive references** citing ≥ 5 authoritative sources each (karpathy gate)
- **Stdlib data-integrity validator** (`data_integrity_check.py`)
- **Agent:** [`cs-ui-ux-pro-max-advisor`](../../agents/product/cs-ui-ux-pro-max-advisor.md)
- **Slash command:** [`/cs:ui-ux-review`](../../commands/ui-ux-review.md) — 6-question UI review gate

## Prerequisites

Python 3.x. No third-party dependencies (stdlib only).

## License

MIT, identical to upstream. See [NOTICE.md](NOTICE.md) and [UPSTREAM-LICENSE](UPSTREAM-LICENSE).

## Related Skills

- [`apple-hig-expert`](../apple-hig-expert/) — Apple HIG with Liquid Glass focus (iOS / macOS / visionOS)
- [`ui-design-system`](../skills/ui-design-system/) — Token generator from a brand color
- [`landing-page-generator`](../skills/landing-page-generator/) — Next.js / TSX landing page scaffolder

---

**Version:** 1.0.0 (upstream v2.5.0)
**Status:** Production Ready
