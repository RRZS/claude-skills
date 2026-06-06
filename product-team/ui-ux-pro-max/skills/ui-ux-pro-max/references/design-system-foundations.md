# Design System Foundations — Why the Generator Works

The `design_system.py` engine maps a free-text request to a complete design system in one pass. Three ideas make this work without LLM calls:

1. **Atomic decomposition** — every design system reduces to the same primitives: pattern → style → colors → typography → effects → anti-patterns. The generator emits one of each.
2. **Industry-conditioned matching** — the same query produces different recommendations for fintech vs wellness because `ui-reasoning.csv` encodes 161 industry-specific priorities (style priority, color mood, anti-patterns to avoid).
3. **BM25 + regex retrieval** — `core.py` scores rows by keyword overlap with industry weighting, no embeddings or model calls. Deterministic, offline, fast.

## Why "Pattern + Style + Colors + Typography + Effects" Is the Right Decomposition

This is the **token hierarchy** at the heart of every mature design system:

- **Pattern** — page structure (Hero-Centric, Trust & Authority, Bento Grid). Sourced from `landing.csv`.
- **Style** — visual language (Glassmorphism, Minimalism, Brutalism). Sourced from `styles.csv` (67 entries).
- **Colors** — semantic tokens (primary, on-primary, background, foreground, destructive, ring). Sourced from `colors.csv` (161 palettes, one per product type).
- **Typography** — heading + body pairing with Google Fonts URLs. Sourced from `typography.csv` (57 pairings).
- **Effects** — motion / shadow / radius / spacing primitives. Embedded in each style row.

Each layer composes on top of the lower one — atomic design, formalized by Brad Frost. The design-system community standardized on this stack between 2015–2020 as Material, Carbon, Fluent, and Polaris all converged on a similar three-tier token model (primitive → semantic → component).

## Industry-Specific Reasoning (The 161 Rules)

`ui-reasoning.csv` does the hard part of design-system selection: given a product type, what styles, palettes, anti-patterns are appropriate?

Example rows (paraphrased):

| Product Type | Pattern | Style Priority | Color Mood | Anti-Patterns |
|--------------|---------|---------------|------------|---------------|
| Beauty/Spa | Hero-Centric + Social Proof | Soft UI Evolution, Organic Biophilic | Soft Pink / Sage / Gold | Bright neon, Harsh animations, Dark mode, AI gradients |
| Fintech/Banking | Trust & Authority | Swiss Modernism 2.0, Exaggerated Minimalism | IBM Blue / Gold / Slate | Playful design, Unclear fees, AI purple/pink gradients |
| Gaming/Entertainment | Storytelling-Driven | 3D Hyperrealism, Cyberpunk, Retro-Futurism | Neon / High contrast | Conservative palettes, Sparse motion |
| Healthcare/Medical | Trust & Authority | Accessible & Ethical, Inclusive Design | Clean blue / White / Green | Aggressive marketing tones, Dark-only |

The rules encode what every senior designer knows but is hard to write down: "trust signals win in fintech, emotion wins in wellness, density wins in dashboards." Encoding them as CSV rows means the choice is reproducible and reviewable.

## Why CSV, Not JSON or YAML

The upstream choice of CSV is deliberate:

- **Grep-able** — debugging "why did it pick X?" is `grep` on a CSV.
- **Editable in any tool** — VS Code, Numbers, Excel, Google Sheets.
- **Version-control diffable** — one row per concept, line-level diffs.
- **No deserialization cost** — stdlib `csv.DictReader` is fast and zero-dep.

When data has > 50 rows of mostly-flat records, CSV outperforms YAML on every axis except deeply nested config.

## Master + Overrides Persistence Pattern

`--persist` writes `design-system/MASTER.md` (global) + `design-system/pages/<page>.md` (page-level overrides). On the next session, the agent reads MASTER first; if a page file exists for the current page, those rules **override** MASTER.

This mirrors how design tokens work in production:

- **Primitive tokens** — raw values (`blue-500: #2563EB`)
- **Semantic tokens** — role bindings (`color-primary: {blue-500}`)
- **Component tokens** — overrides per component (`button-primary-bg: {color-primary}`)

A page file is a component-level override. The pattern is well-established in Carbon, Polaris, Material 3, and Salesforce Lightning.

## Anti-Patterns Encoded as Hard Negatives

Every row in `ui-reasoning.csv` ships an **anti-patterns** column. The generator surfaces them inline in the output — not "consider also" but **AVOID**. This is the single most underrated feature.

Example: requesting a fintech design produces:

```
AVOID (Anti-patterns):
   Playful design + Unclear fees + AI purple/pink gradients
```

Because trust-signaling is the conversion lever in finance, anything that erodes trust (cartoonish illustrations, AI-shaped color palettes that signal "rushed AI startup") actively hurts. Encoding these as hard negatives prevents the generator from ever proposing them, even if the keyword query happens to match an inappropriate style.

## Sources

1. Brad Frost — *Atomic Design* (2016). Five-level decomposition (atoms → molecules → organisms → templates → pages). The foundational frame: https://atomicdesign.bradfrost.com/
2. Nathan Curtis — "Tokens in Design Systems" (EightShapes, 2016) + "Naming Tokens" (2020). The primitive / semantic / component three-tier model: https://medium.com/eightshapes-llc/tokens-in-design-systems-25dd82d58421
3. Alla Kholmatova — *Design Systems: A Practical Guide* (Smashing Magazine, 2017). The canonical book on pattern libraries vs design systems vs style guides.
4. Adele — UXPin's design-systems database (https://adele.uxpin.com/). Comparative survey of 50+ public design systems showing the convergence on token hierarchies.
5. Google Material Design 3 — "Design tokens" + "Roles for color" (https://m3.material.io/foundations/design-tokens). Production-scale token model with semantic role bindings.
6. IBM Carbon Design System — "Tokens" (https://carbondesignsystem.com/elements/themes/tokens/). Three-tier token system in active production at IBM.
7. Refactoring UI — Adam Wathan & Steve Schoger (https://www.refactoringui.com/). Source of the "design with primitives, refine with constraints" methodology underlying the generator.
8. Nielsen Norman Group — "Design Systems 101" (https://www.nngroup.com/articles/design-systems-101/). Industry definition + maturity model used to position generators like this one.
