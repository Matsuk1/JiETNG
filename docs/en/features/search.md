---
title: maimai DX Search and Filtering
description: JiETNG supports maimai B50 filters, constants, levels, DX Rating, achievement, rating breakdown, and song record search.
---

# Search and Filtering

JiETNG search is split into score image filters, song search, and song ID lookup.

## Score Filters

```text
b50 -lv 14 14.9 -diff mas rem -scr 100.5
ab50 -ver buddies -type dx
rct50 -page 2
ap50 -lv 13.6
```

You can filter by level/constant, chart rating, achievement, DX score, DX stars, difficulty, chart type, version, and page.

The result is still rendered as a score image, which is useful for constant-range B50, MAS/Re:MAS-only lists, or version-specific views.

## Song Search

```text
artist Nanahira
designer Jack
ヒバナ info
ヒバナってどんな曲
```

- `artist` searches by artist.
- `designer` searches by chart designer.
- `info` / `song-info` / `ってどんな曲` shows song details.
- Keywords are case-insensitive.

## Song Records

```text
ヒバナ record
ヒバナのレコード
search-record 123456
```

`record` searches your record by title or alias. `search-record` uses the 6-character song ID.

## Data Source

Queries use processed records currently saved in JiETNG. They may come from:

- `maimai update`
- bookmarklet uploads with Import Token
- developer API imports

Query commands do not automatically resync official data.
