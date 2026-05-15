# AgentSys Website

A single-page static showcase site for [AgentSys](https://github.com/agent-sh/agentsys) — a modular runtime and orchestration system for AI agents.

## Run locally

No build step. Open `index.html` directly, or serve the folder:

```bash
cd agentsys-website
python3 -m http.server 8000
# visit http://localhost:8000
```

## Files

- `index.html` — full landing page (hero, problem, approach, benchmarks, commands, workflow, install, principles, footer)
- `styles.css` — dark theme, responsive, no external dependencies

## Deploy

Drop the folder onto any static host (GitHub Pages, Netlify, Vercel, Cloudflare Pages, S3). Nothing to build.

This is an unofficial showcase. Source content is paraphrased from the upstream [agent-sh/agentsys](https://github.com/agent-sh/agentsys) README and `site/content.json`.
