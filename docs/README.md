# JiETNG Documentation

This directory contains the VitePress documentation site for JiETNG.

## Commands

```bash
cd docs
npm install
npm run docs:dev
npm run docs:build
npm run docs:preview
```

The production build is generated in:

```text
docs/.vitepress/dist/
```

## Current Structure

```text
docs/
├── .vitepress/
│   ├── config.mts
│   └── theme/
├── commands/
│   ├── basic.md
│   ├── index.md
│   └── record.md
├── features/
│   └── search.md
├── guide/
│   └── getting-started.md
├── more/
│   ├── faq.md
│   ├── license.md
│   ├── privacy.md
│   └── support.md
├── en/
│   └── ...
├── ja/
│   └── ...
├── public/
│   ├── bookmarklet/
│   └── ...
├── bookmarklet.md
├── demo.md
├── developer-api.md
└── index.md
```

The root locale is Simplified Chinese. English pages live under `docs/en/`, and Japanese pages live under `docs/ja/`.

## Content Scope

The docs should describe the current JiETNG behavior:

- LINE Bot commands and self-only rules
- SEGA account binding and `maimai update`
- Import Token users and bookmarklet uploads
- B-series score images, filters, record lookup, plate progress, and nearby arcade search
- Developer API and user Import API

Do not edit generated files under `docs/.vitepress/dist/` or dependency files under `docs/node_modules/`.

## Deployment Notes

The VitePress config uses:

- `base: '/'`
- sitemap hostname: `https://jietng.matsuk1.com`
- local search
- locales: root `zh-CN`, `/en/`, `/ja/`

For hosted builds, use:

```text
Build command: cd docs && npm install && npm run docs:build
Output directory: docs/.vitepress/dist
Node version: 18+
```
