# Record Commands

<img src="/b50_example.png" alt="Best 50 Score Example" style="width: 22%; max-width: 400px; min-width: 200px; display: block; margin: 1.5rem auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" />

## Commands

### Basic Best Charts

```
b50          # Best 50 (old ver. 35 + new ver. 15)
b40          # Best 40 (legacy Rating calculation, old ver. 25 + new ver. 15)
best50 / best40   # Aliases for the above
```

### Variations

```
b35 / best35              # Old version Best 35 only
b15 / best15              # New version Best 15 only
ab35 / allb35             # All Best 35 (ignore version)
ab50 / allb50             # All Best 50 (ignore version)
apb50 / ap50              # All Perfect Best 50 (AP/AP+ scores only)
fdxb50 / fdx50            # Full DX Best 50 (FDX/FDX+ scores only)
idealb50 / idlb50         # Ideal Best 50 (simulate previous tier scores)
rct50 / r50               # Recent 50 plays
```

## Filters

All B-series commands support the following filter parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `-lv [value] [max]` | Filter by constant. Single value = exact match; two values = range | `-lv 14.7` or `-lv 14 14.9` |
| `-ra [value] [max]` | Filter by Rating. Single value = exact match; two values = range | `-ra 301` or `-ra 301 312` |
| `-star [value] [max]` | Filter by DX star count. Single value = exact match; two values = range | `-star 3` or `-star 3 5` |
| `-scr [min] [max]` | Filter by achievement rate (max optional) | `-scr 100.3` or `-scr 99 100` |
| `-dx [min] [max]` | Filter by DX score percentage (max optional) | `-dx 92` or `-dx 90 95` |
| `-ver [versions...]` | Filter by version, multiple allowed | `-ver buddies` or `-ver splash splash+` (plus → +) |
| `-diff [difficulties...]` | Filter by difficulty, multiple allowed | `-diff mas` or `-diff mas rem` |
| `-type [dx\|std]` | Filter by chart type | `-type dx` |
| `-page [n]` | Pagination | `-page 2` |

::: tip Difficulty abbreviations
`bas` = BASIC, `adv` = ADVANCED, `exp` = EXPERT, `mas` = MASTER, `rem` = Re:MASTER
:::

::: tip Version names
Case-insensitive. Use `+` for PLUS versions (e.g. `splash+`). Separate multiple versions with spaces.
:::

### Examples

```
b50 -lv 14.7                             # Constant 14.7 (exact match)
b50 -lv 14 14.9                          # Constant 14.0~14.9
b50 -ra 301 312                          # Rating 301~312
b50 -scr 100.3                           # Achievement ≥100.3%
b50 -dx 92 95                            # DX score 92%~95%
b50 -ver buddies -lv 14 14.9             # Buddies version level 14 songs
b50 -diff mas rem -scr 100.5             # MASTER/Re:MASTER with achievement ≥100.5%
b50 -type dx -diff mas                   # DX charts, MASTER difficulty
b50 -diff mas -lv 14 14.9 -page 2        # Go to page 2
```

---

## Internal Level Query

View all songs for a specified difficulty level, grouped by internal constant.

### Command Format

```
13の定数リスト    # Japanese command
13のレベルリスト  # Japanese command
13 level-list   # English command
```

Level queries automatically use the server version set during binding (JP or INTL).

---

## Level & Rank Progress

View achievement progress for a specified difficulty level and rank.

### Command Format

```
13sss+進捗        # Level 13 SSS+ rank progress
13+sss progress   # Level 13+ SSS rank progress
15fdx+ progress   # Level 15 FDX+ rank progress
```

### Supported Ranks

- **Score Ranks**: S, S+, SS, SS+, SSS, SSS+
- **Full Combo**: FC, FC+, AP, AP+
- **Full Sync**: FDX, FDX+

::: tip
- Rank names are case-insensitive
- Supports Japanese (進捗), English (progress) keywords
- Supported difficulty levels: 11, 11+, 12, 12+, 13, 13+, 14, 14+, 15
:::
