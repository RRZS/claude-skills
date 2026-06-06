# Style, Color, Typography — How They Were Selected

The 67 styles, 161 palettes, and 57 typography pairings in `data/` are not assembled from "what looks good"; they are organized around three observable principles every senior designer optimizes against. This file makes those principles explicit so the recommendations can be challenged and improved.

## Style Selection (`styles.csv` — 67 rows)

Each style row encodes:

- **Name** — public-facing style name (Glassmorphism, Bento Grid, etc.)
- **Keywords** — synonyms and CSS keywords (used by BM25 retrieval)
- **Best For** — product categories where the style wins
- **Performance** — Excellent / Good / Poor — does it ship without jank
- **Accessibility** — WCAG AA / A / Fails — is it accessible by default
- **Light/Dark mode** — Full / Partial / Single — which themes work
- **Effects** — characteristic motion, blur, shadow primitives

The 67 styles cluster into three eras:

- **Foundational (15 styles)** — Swiss Modernism, Flat, Minimalism, Brutalism, Skeuomorphism. Stable, well-understood, performant.
- **Modern (35 styles)** — Glassmorphism, Neumorphism, Claymorphism, Bento Grid, Aurora UI, Soft UI Evolution. Current production aesthetics.
- **Emerging (17 styles)** — Spatial UI (visionOS), AI-Native UI, Tactile/Deformable, Voice-First Multimodal. Forward-looking.

Why this matters: requesting a "modern fintech" landing should not return Skeuomorphism (foundational, out of cultural alignment) even though it scores well on trust. The reasoning rules in `ui-reasoning.csv` constrain the per-industry pool before BM25 ranks within it.

## Color Palettes (`colors.csv` — 161 rows)

One palette per product type. Each palette ships 17 token roles:

- Surface roles: `background`, `foreground`, `card`, `card-foreground`, `muted`, `muted-foreground`, `border`
- Action roles: `primary`, `on-primary`, `secondary`, `on-secondary`, `accent`, `on-accent`
- State roles: `destructive`, `on-destructive`, `ring`
- Plus a `notes` field documenting accessibility adjustments

This is the **semantic-token layer** of the design-system stack — the same shape used in shadcn/ui, Tailwind UI, Material 3 dynamic color, and IBM Carbon. Every palette in `colors.csv` is pre-verified to hit WCAG AA on primary / on-primary; the `notes` column documents any palette where the upstream had to nudge a color to meet contrast.

Example: the SaaS palette uses `#2563EB` primary with `#FFFFFF` on-primary — that's a 4.83:1 ratio, comfortably above 4.5:1. The accent was adjusted from `#F97316` to `#EA580C` to hit 3:1 against the background, documented in notes as `Accent adjusted from #F97316 for WCAG 3:1`.

## Typography Pairings (`typography.csv` — 57 rows)

Each pairing ships:

- **Heading family** + **Body family** (always one or two families, never three+)
- **Google Fonts share URL** — pre-built selection link with the right weights
- **CSS @import** — copy-pasteable `@import url(...)` snippet
- **Mood** — keywords for matching (financial, playful, editorial, etc.)
- **Best For** — product categories

Why limited to two families: type pairings beyond two introduce vertical-rhythm conflict (different x-heights), force more font requests (perf hit), and dilute brand voice. The 57 pairings are a curated subset of Google Fonts that compose cleanly within these constraints.

The Cormorant Garamond / Montserrat pairing for wellness:
- Cormorant Garamond — serif, low contrast, "calm luxury"
- Montserrat — geometric sans, high availability across weights
- Mood keywords: elegant, calming, sophisticated, editorial
- Best for: luxury brands, wellness, beauty, editorial

This pairs an emotional serif heading with a neutral sans body — the standard "luxury editorial" pattern across The New York Times Style, Aesop, Glossier.

## Why Mood Keywords Carry Weight

The keyword field is the BM25 ranking signal. A query like `"elegant calming sophisticated"` would surface this pairing because every word matches the mood field. This pushes the retrieval system toward emotion-first matching rather than feature-first — the right move for design.

## Anti-Pattern Encoding

Several rules in `styles.csv` and `ui-reasoning.csv` ship explicit anti-patterns:

- **No emoji as structural icons** — emoji rendering is OS-dependent, can't be tokenized
- **No bright neon for healthcare** — clinical context demands restraint
- **No AI purple/pink gradients for banking** — signals "rushed AI startup" in finance
- **No dark mode for wellness** — wellness brands need warmth; pure dark feels clinical
- **No Glassmorphism for accessibility-first products** — backdrop-blur regressively reduces contrast

The generator surfaces these inline. Designers often know the rules but forget to check; encoding them as hard negatives in the data eliminates the failure mode entirely.

## Sources

1. Adam Wathan & Steve Schoger — *Refactoring UI* (https://www.refactoringui.com/). The canonical practical guide to color systems, type hierarchy, and visual restraint used as a basis for the palette + pairing structure.
2. Google Material Design 3 — "Color system" (https://m3.material.io/styles/color). Source of the role-based color token model (primary / on-primary / surface / on-surface).
3. shadcn/ui — semantic color tokens (https://ui.shadcn.com/docs/theming). Production reference for the 17 token roles used in `colors.csv`.
4. IBM Carbon Design System — "Color tokens" (https://carbondesignsystem.com/elements/color/overview/). Production-scale semantic color taxonomy.
5. Google Fonts — type pairings and weight availability (https://fonts.google.com). Source of all typography pairings in `typography.csv`.
6. Matthew Butterick — *Practical Typography* (https://practicaltypography.com/). Reference text on type pairing constraints and vertical rhythm.
7. Stephen Coles — *The Anatomy of Type* (Harper Design, 2012). Source for the technical taxonomy of typeface classification used in mood matching.
8. Tobias Frere-Jones et al. — Frere-Jones Type writings on font pairing for editorial vs functional contexts (https://frerejones.com/blog).
