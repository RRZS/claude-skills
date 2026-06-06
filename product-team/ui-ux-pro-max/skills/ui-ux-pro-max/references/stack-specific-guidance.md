# Stack-Specific Guidance — Why One CSV per Stack

The `data/stacks/` directory ships 16 separate CSV files — one per supported stack — instead of a single generic "web best practices" file. This is intentional: cross-stack rules generalize poorly, and the wrong abstraction (e.g. "always memoize" applied uniformly) actively hurts in some stacks (Svelte 5 runes, SwiftUI value semantics) while being correct in others (React).

## Supported Stacks (16)

| Category | Stacks | CSV |
|----------|--------|-----|
| Plain web | HTML + Tailwind | `html-tailwind.csv` |
| React | React, Next.js, shadcn/ui | `react.csv`, `nextjs.csv`, `shadcn.csv` |
| Vue | Vue, Nuxt.js, Nuxt UI | `vue.csv`, `nuxtjs.csv`, `nuxt-ui.csv` |
| Other web | Svelte, Astro, Angular | `svelte.csv`, `astro.csv`, `angular.csv` |
| PHP | Laravel (Blade + Livewire + Inertia) | `laravel.csv` |
| iOS | SwiftUI | `swiftui.csv` |
| Android | Jetpack Compose | `jetpack-compose.csv` |
| Cross-platform | React Native, Flutter | `react-native.csv`, `flutter.csv` |
| 3D / WebGL | Three.js | `threejs.csv` |

## What Each Stack CSV Encodes

Per row:

- **Topic** — short identifier (e.g., `rerender-memo`, `safe-areas`, `runes-reactivity`)
- **Description** — what the rule prevents or enables
- **Code Example** — copy-pasteable snippet in the stack's idiom
- **Anti-Pattern** — what to avoid and why
- **When to Apply** — scenarios where this rule fires

Example row from `react.csv`:

| Topic | Description | Code Example | Anti-Pattern |
|-------|-------------|--------------|--------------|
| `rerender-memo` | Wrap pure components in `memo()` when parent re-renders on unrelated state | `export default memo(MyList)` | Memoizing every component reflexively (memoization has runtime cost) |

Example row from `svelte.csv`:

| Topic | Description | Code Example | Anti-Pattern |
|-------|-------------|--------------|--------------|
| `runes-reactivity` | Use `$state`, `$derived`, `$effect` in Svelte 5 instead of legacy `$:` | `let count = $state(0)` | Mixing runes and legacy reactivity in the same component |

The two stacks have **opposite optimization defaults**: React rewards selective memoization; Svelte 5 rewards trust in the compiler. A single "JS framework performance" CSV would average these into uselessness.

## When to Query a Stack CSV

- Implementing a feature in a specific framework
- Debugging a stack-specific performance issue
- Onboarding to a stack the team hasn't shipped in before
- Reviewing code for stack-idiomatic violations

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "list virtualization" --stack react
python3 skills/ui-ux-pro-max/scripts/search.py "safe-area gesture-handler" --stack react-native
python3 skills/ui-ux-pro-max/scripts/search.py "navigation tab-bar" --stack swiftui
python3 skills/ui-ux-pro-max/scripts/search.py "image optimization" --stack nextjs
```

## Why Cross-Platform Stacks Get Their Own CSVs

React Native and Flutter are not "React for mobile" or "Dart for mobile" — they ship distinct runtime models (bridge vs Fabric / engine), distinct layout (Yoga / Skia), distinct gesture systems, distinct navigation primitives. Performance guidance from `react.csv` (which assumes a browser DOM) actively misleads in React Native (which has no DOM, no CSS, no `useLayoutEffect` semantics).

Similarly, `swiftui.csv` rules around `@State` / `@StateObject` / `@ObservedObject` have no direct analog in Compose's `remember` / `derivedStateOf` / `collectAsStateWithLifecycle`. The CSVs preserve these differences instead of papering over them.

## Three.js Is in This List Because 3D Web UI Is in This List

The `threejs.csv` is larger than the others (44KB vs 8–18KB) because 3D web UI ships an entirely different mental model — scene graphs, raycasting, post-processing — that doesn't compose with DOM-based stack rules. As styles like "Spatial UI", "3D Hyperrealism", and "AI-Native UI" become more common, having stack-level Three.js guidance bundled in is the difference between a recommendation that's actionable and one that's aspirational.

## What's NOT in the Stack CSVs

- **CSS rules** — those live in the general `ux-guidelines.csv`. CSS is shared across all web stacks.
- **Component recipes** — those are downstream of the design system and live in the rendered code, not the CSV.
- **General accessibility rules** — those are in `ux-guidelines.csv` because they apply universally.

The stack CSVs encode **stack-idiomatic** guidance, not general UI rules. A team using Vue should query `vue.csv` for Vue-specific best practices and `ux-guidelines.csv` for accessibility; the two layers are intentionally separated.

## Sources

1. React docs — "Render and commit" + "You might not need memo" (https://react.dev). Authoritative source for selective memoization vs reflexive memoization.
2. Next.js docs — "Performance" + "Image Optimization" + "App Router" (https://nextjs.org/docs). Source for the SSR / RSC / Image guidance in `nextjs.csv`.
3. Vue.js docs — "Performance" + "Composition API best practices" (https://vuejs.org/guide/best-practices/performance.html). Source for the Vue-idiomatic patterns.
4. Svelte docs — "Runes" + "Performance" (https://svelte.dev/docs/svelte/what-are-runes). Source for the Svelte 5 reactivity model encoded in `svelte.csv`.
5. Apple SwiftUI docs — "Managing model data" + "Building blocks" (https://developer.apple.com/documentation/swiftui/). Source for state primitives and navigation patterns.
6. Android Jetpack Compose docs — "State and side effects" + "Performance" (https://developer.android.com/jetpack/compose). Source for the Compose state model.
7. React Native docs — "Performance" + "New Architecture" (https://reactnative.dev/docs/performance). Source for the React Native specific perf rules (bridge, Fabric, JSI).
8. Flutter docs — "Performance best practices" + "Rendering pipeline" (https://docs.flutter.dev/perf/best-practices). Source for the Skia / Impeller rendering guidance.
9. Three.js Manual — "Optimization" + "WebGL fundamentals" (https://threejs.org/manual/). Source for the scene graph / raycasting / draw-call guidance in `threejs.csv`.
10. Laravel docs + Filament + Livewire — production patterns for server-rendered + reactive PHP UI (https://laravel.com/docs).
