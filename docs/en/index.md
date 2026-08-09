---
layout: home
title: JiETNG · maimai B50 / DX Rating Breakdown · JP / INTL Score Tracker
titleTemplate: false

hero:
  name: "JiETNG"
  text: "maimai DX<br>Score Tracker"
  tagline: LINE bot for JP and INTL maimai DX · B50 / Best 50 / Recent 50 / DX Rating / rating breakdown / bookmarklet import
  image:
    src: /hero-image.svg
    alt: JiETNG Logo
  actions:
    - theme: brand
      text: Get Started
      link: /en/guide/getting-started
    - theme: alt
      text: Bookmarklet
      link: /en/bookmarklet
    - theme: alt
      text: GitHub
      link: https://github.com/Matsuk1/JiETNG

features:
  - icon: 📊
    title: Score Images
    details: Generate B50, B40, Best 35/15, All Best, AP Best, FDX Best, Recent 50, and Ideal Best images.
    link: /en/commands/record
    linkText: Record commands

  - icon: 🔎
    title: Precise Filters
    details: Filter by level, constant, achievement, DX score, chart type, difficulty, version, and page.
    link: /en/features/search
    linkText: Search features

  - icon: 🧩
    title: Two Data Sources
    details: Sync through a bound SEGA account, or upload processed records with an Import Token and the bookmarklet.
    link: /en/bookmarklet
    linkText: Bookmarklet

  - icon: 🏆
    title: Progress Tracking
    details: Track plate status, level targets, and cleared / unplayed / uncleared states.
    link: /en/commands/
    linkText: Command list

  - icon: 🌐
    title: JP and INTL
    details: Supports both Japanese and International maimai NET data, with Chinese, English, and Japanese docs.
    link: /en/guide/getting-started
    linkText: Quick start

  - icon: 🔐
    title: Export and API
    details: Includes settings, JSON/XML export, Import Tokens, developer tokens, and permission APIs.
    link: /en/developer-api
    linkText: API docs
---

<style>
.VPFeature { cursor: pointer; }
.VPFeature:hover .icon {
  transform: scale(1.12) rotate(4deg);
  transition: transform 0.2s ease;
}
.vp-doc h2 {
  border-top: none;
  padding-top: 24px;
}
</style>

## What Is JiETNG?

JiETNG is a **maimai DX / maimai でらっくす** score tracker and LINE bot. It can sync records from maimai NET through a bound SEGA account, or receive processed records uploaded by the browser bookmarklet through an Import Token.

Current major features include B50 / Best 50 images, Recent 50, DX Rating and rating breakdown views, song/chart lookup, level and constant lists, plate status, friend record lookup, nearby arcade search, JSON/XML export, developer APIs, and Import Token upload.

The project is designed for searches such as `maimai b50`, `maimai DX Rating`, `maimai rating breakdown`, and `maimai score tracker`.

## Quick Start

1. Add the JiETNG LINE Bot.
2. Send `bind` in a private chat. Bind a SEGA account, or choose import-only mode with an Import Token.
3. Send `maimai update` to sync official data, or use the [bookmarklet](/en/bookmarklet) on the official maimai site.
4. Try `b50`, `record`, `13.6 records`, or `真極 plate`.

[Read the guide →](/en/guide/getting-started)

## Support

- [Command reference](/en/commands/)
- [Developer API](/en/developer-api)
- [GitHub Issues](https://github.com/Matsuk1/JiETNG/issues)
- [Discord](https://discord.gg/NXxFn9T8Xz)
