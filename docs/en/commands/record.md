---
title: B50 Record Commands
description: JiETNG maimai DX B50, Best 50, Recent 50, DX Rating, rating breakdown, level targets, and song record command reference.
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

Supported fields include level/constant, chart rating, achievement, DX score, DX stars, difficulty, chart type, version, next-version preview, page, and display multiplier.

## Song Records

```text
ヒバナ record
```

`record` searches by title or alias. If multiple songs match, the bot returns a selectable list.

## Level and Constant Lists

```text
13 records
13.6 records
14.7 records 2
13.6 levels
```

Integers mean levels; decimals mean constants. A trailing number is treated as the page.

## Targets

```text
13sss+ prog
14ss+ prog -uc
14ss+ prog -up
14ss+ prog -c
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
真極 plate
真極 plate -uc
PRiSM PLUS ver
13.6 levels
```

Plate commands also support `-uc`, `-up`, and `-c`.

## Mentions

In group chats, mention a registered JiETNG user to query their score data:

```text
@friend b50
@friend 13 records
@friend 14sss+ prog
```

Only score-related commands support mention queries. Account, settings, export, and update commands are always self-only.
