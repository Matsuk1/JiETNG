---
title: B50 Record Commands
description: JiETNG maimai DX B50, Best 50, Recent 50, DX Rating, rating breakdown, level progress, and song record command reference.
---

# Record Commands

<img src="/b50_example.png" alt="Best 50 Example" style="width: 22%; max-width: 400px; min-width: 200px; display: block; margin: 1.5rem auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" />

## B-Series Images

```text
b50 / best50
b40 / best40
b35 / best35
b15 / best15
ab35 / allb35
ab50 / allb50
apb50 / ap50
fdxb50 / fdx50
rct50 / r50
idealb50 / idlb50
s50 / sun50 / 寸50 / 寸止め
unknown
```

Filters can be appended to the same command.

`s50` / `sun50` lists near-miss scores for SSS+ and SSS: `100.4000% - 100.4999%` and `99.9000% - 99.9999%`.

## Filters

```text
b50 -lv 14.7
b50 -lv 14 14.9
b50 -ra 301 312
b50 -scr 100.3
b50 -dx 92 95
b50 -ver buddies -lv 14 14.9
b50 -diff mas rem -scr 100.5
b50 -type dx -diff mas
b50 -times 2
b50 -page 2
```

Supported fields include level/constant, chart rating, achievement, DX score, DX stars, difficulty, chart type, version, page, and display multiplier.

## Song Records

```text
ヒバナ record
ヒバナ song-record
ヒバナのレコード
search-record 123456
```

`record` searches by title or alias. `search-record` uses a 6-character song ID. If multiple songs match, the bot returns a selectable list.

## Level and Constant Lists

```text
13 records
13 record-list 2
13.6 records
14.7 record-list 2
```

Integers mean levels; decimals mean constants. A trailing number is treated as the page.

## Progress

```text
13sss+ progress
14AP進捗
15fdx+ 进度
14ss+ progress -uc
14ss+ progress -up
14ss+ progress -c
```

Targets: `s`, `s+`, `ss`, `ss+`, `sss`, `sss+`, `fc`, `fc+`, `ap`, `ap+`, `fdx`, `fdx+`.

Suffixes:

| Suffix | Meaning |
|--------|---------|
| `-uc` | Uncleared / not reached |
| `-up` | Unplayed |
| `-c` | Cleared / reached |

## Plates and Versions

```text
真極の達成状況
真極 achievement
真極の達成状況 -uc
PRiSM PLUSのバージョンリスト
PRiSM PLUS version-list
13.6のレベルリスト
13.6 level-list
```

Plate progress also supports `-uc`, `-up`, and `-c`.

## Mentions

In group chats, mention a registered JiETNG user to query their score data:

```text
@friend b50
@friend 13 records
@friend 14sss+ progress
```

Only score-related commands support mention queries. Account, settings, export, and update commands are always self-only.
