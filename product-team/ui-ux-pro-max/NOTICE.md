# Attribution

## Upstream Source

This skill is **derived from** the open-source [`ui-ux-pro-max-skill`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) by **NextLevelBuilder** (Goon Nguyen / @mrgoonie), released under the MIT License.

- **Upstream repository:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- **Upstream version at port:** v2.5.0
- **Upstream homepage:** https://uupm.cc
- **Upstream license:** MIT (see [UPSTREAM-LICENSE](UPSTREAM-LICENSE))

## What's Reproduced Verbatim

The following content is reproduced verbatim under the MIT license:

- All 31 CSV data files under [`skills/ui-ux-pro-max/data/`](skills/ui-ux-pro-max/data/) (161 reasoning rules, 67 styles, 161 palettes, 57 font pairings, 99 UX guidelines, 25 chart types, and 16 stack-specific CSVs)
- All Python scripts under [`skills/ui-ux-pro-max/scripts/`](skills/ui-ux-pro-max/scripts/) (`core.py`, `design_system.py`, `search.py`) — including the BM25 search engine, design system reasoning engine, and the Master + Overrides persistence pattern
- The full upstream playbook in [`skills/ui-ux-pro-max/references/full-skill-playbook.md`](skills/ui-ux-pro-max/references/full-skill-playbook.md) (placeholder values resolved, otherwise verbatim)
- The full upstream quick reference in [`skills/ui-ux-pro-max/references/quick-reference.md`](skills/ui-ux-pro-max/references/quick-reference.md)

## What This Wrapper Adds

Following the repo's hybrid voice pattern for MIT external imports (matching `engineering/write-a-skill`, `caveman`, `grill-me`, `handoff`):

1. **Concise SKILL.md** ([skills/ui-ux-pro-max/SKILL.md](skills/ui-ux-pro-max/SKILL.md)) — under 100 lines, with YAML frontmatter, "Use when" triggers, and pointers to the full playbook for progressive disclosure
2. **Four deep-dive references** in `skills/ui-ux-pro-max/references/`, each citing ≥ 5 authoritative sources per the repo's karpathy gate:
   - `design-system-foundations.md` (8 sources)
   - `accessibility-and-touch.md` (8 sources)
   - `style-color-typography.md` (8 sources)
   - `stack-specific-guidance.md` (10 sources)
3. **Stdlib data-integrity validator** ([skills/ui-ux-pro-max/scripts/data_integrity_check.py](skills/ui-ux-pro-max/scripts/data_integrity_check.py)) — verifies all CSV files load and row counts match the documented schema
4. **Agent**: [`cs-ui-ux-pro-max-advisor`](../../agents/product/cs-ui-ux-pro-max-advisor.md) — design-system-first interrogator
5. **Slash command**: [`/cs:ui-ux-review`](../../commands/ui-ux-review.md) — 6-question UI review gate

## License

This wrapper is also MIT-licensed, identical to the upstream. The MIT license terms apply to both the upstream content and this wrapper's additions.

## Compliance

Per the MIT license, the upstream copyright notice and permission notice are included in:

- This `NOTICE.md`
- The repo-level [LICENSE](../../LICENSE)
- The bundled [`UPSTREAM-LICENSE`](UPSTREAM-LICENSE) file

If you redistribute this skill or any substantial portion of it, retain the upstream attribution above.
