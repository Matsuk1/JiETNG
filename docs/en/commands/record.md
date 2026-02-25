# Record Commands

Best 50 (b50) and Best 100 (b100) charts are fundamental features of JiETNG, displaying your highest-rated scores with beautifully designed visualizations.

## What is Best 50?

The "Best 50" system is『maimai でらっくす』official ranking method, consisting of:

- **Best 35**: Your top 35 highest scores in **old version songs** (songs from previous versions)
- **Best 15**: Your top 15 highest scores in **current version songs** (songs from current version)

Your **DX Rating** is the sum of these 50 scores.

<img src="/b50_example.png" alt="Best 50 Score Example" style="width: 22%; max-width: 400px; min-width: 200px; display: block; margin: 1.5rem auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" />

## Commands

### Basic Best Charts

```
b50          # Generate Best 50 chart
b40          # Generate Best 40 chart (Legacy Rating calculation)
b100         # Generate Best 100 chart
best50       # Alternative command for b50
best40       # Alternative command for b40
best100      # Alternative command for b100
```

### Variations

```
best35       # Show only top 35 old version songs
best15       # Show only top 15 current version songs
ab35         # All Best 35  (ignore song version)
ab50         # All Best 50  (ignore song version)
ab100        # All Best 100 (ignore song version)
apb50        # All Perfect Best 50 (AP/AP+ scores only)
fdxb50       # Full DX Best 50 (FDX/FDX+ scores only)
idlb50       # Ideal Best 50 (simulate best scores)
```

## Chart Features

### What's Displayed

Each score card displays:

- <� **Song name** and difficulty
- <� **Song version**: old version or current version
- P **Internal constant**: e.g., 14.7
- =� **Achievement rate**: Your score percentage
- <� **Rank grade**: SSS+, SSS, SS+, etc.
- < **Full Combo type**: AP+, AP, FC+, FC
- =% **Full Sync**: FDX+, FDX, FS+, FS
- =� **Rating**: Single song rating
- =� **DX Rating**: Your DX Rating

### User Info Header

Charts include your profile:

- =d Player name and avatar
- <� Dan/Class
- P Total rating
- <� Title

## Advanced Usage

### Filtering Scores

You can apply filters to customize b50 output:

#### Filter by Level

```
b50 -lv 14.7            # Exactly constant 14.7
b50 -lv 14 14.9         # Constant 14.0~14.9 (all level 14 songs)
b50 -lv 15 15.9         # Constant 15.0~15.9 (all level 15 songs)
```

#### Filter by Rating

```
b50 -ra 200             # Exactly Rating 200
b50 -ra 180 200         # Rating 180-200
```

#### Filter by Achievement Rate

```
b50 -scr 100.5          # Achievement rate 100.5%+
b50 -scr 99 100         # Achievement rate 99%-100%
```

#### Filter by DX Score

```
b50 -dx 95              # DX score 95%+
b50 -dx 90 95           # DX score 90-95%
```

#### Filter by DX Star Rating

```
b50 -star 3             # Exactly 3 DX stars
b50 -star 3 5           # 3~5 DX stars
```

#### Filter by Version

```
b50 -ver buddies                   # Buddies version only
b50 -ver splash splash+            # Splash and Splash PLUS versions
b50 -ver festival+ buddies         # FESTiVAL PLUS and Buddies versions
```

::: tip Version Name Notes
- Version names are case-insensitive
- Use `+` to indicate PLUS versions (e.g., `splash+`)
- Multiple versions can be specified, separated by spaces
:::

#### Filter by Difficulty

```
b50 -diff mas                      # MASTER difficulty only
b50 -diff mas rem                  # MASTER and Re:MASTER difficulties
b50 -diff bas adv exp              # BASIC, ADVANCED, and EXPERT difficulties
```

::: tip Difficulty Abbreviations
- `bas` = BASIC
- `adv` = ADVANCED
- `exp` = EXPERT
- `mas` = MASTER
- `rem` = Re:MASTER
- Full names can also be used (e.g., `basic`, `master`)
- Difficulty names are case-insensitive
- Multiple difficulties can be specified, separated by spaces
:::

#### Filter by Chart Type

```
b50 -type dx                       # DX charts only
b50 -type std                      # STD charts only
```

#### Pagination

```
b50 -page 2                        # Old songs #36-70, new songs #16-30
b100 -page 2                       # Old songs #71-140, new songs #31-60
```

### Combining Filters

You can combine multiple filters:

```
b50 -lv 14.7 -scr 100.5                  # Constant 14.7 with achievement rate 100.5%+
b50 -ra 200 -dx 95                       # Exactly Rating 200 with DX score ≥95%
b50 -ver buddies -lv 14 14.9             # Buddies version with level 14 songs
b50 -ver splash splash+ -scr 100         # Splash/Splash+ with achievement ≥100%
b50 -diff mas -lv 14 14.9               # MASTER difficulty with level 14 songs
b50 -diff mas rem -scr 100.5             # MASTER/Re:MASTER with achievement 100.5%+
b50 -type dx -diff mas                   # MASTER difficulty in DX charts
b50 -lv 14 15 -scr 99.5 -dx 90           # Complex filtering
b50 -diff mas -lv 14 14.9 -page 2        # Go to page 2
```

## Chart Type Explanations

### Best 50 (b50)

Standard ranking chart following official rules:
- Top 35 from old version songs
- Top 15 from new version songs
- Your actual DX rating

**Use case**: View your official rating and progress

### Best 100 (b100)

Extended version showing more scores:
- Top 70 from old version songs
- Top 30 from new version songs

**Use case**: Find songs just below your b50 threshold

### All Best 50 (ab50)

Ignores song version distinction:
- Top 50 highest scores regardless of version

**Use case**: View highest achievements without version separation

### All Perfect Best 50 (apb50)

Shows only AP songs:
- Only AP (All Perfect) and AP+ scores
- Ranked by rating

**Use case**: Monitor your AP progress

### Full DX Best 50 (fdxb50)

Shows only FDX songs:
- Only FDX (Full DX) and FDX+ scores
- Ranked by rating

**Use case**: Monitor your FDX progress

### Ideal Best 50 (idlb50)

Theoretical maximum rating:
- Simulates previous tier scores for all songs
- Shows potential rating growth

**Use case**: Set goals for rating improvement


## FAQ

### Why is my rating different from in-game?

- JiETNG only updates when you run `maimai update`
- Some song constants may not be standard

### Some scores are missing?

Make sure you've played these songs recently. Older scores may not appear if:
- They've been replaced by better scores
- Songs have been removed from the game
- Data sync issues (try `maimai update` again)


## Internal Level Query

View all songs of a specified difficulty level, grouped by internal constants (e.g., 13.0, 13.1, 13.2, etc.).

### Command Format

```
13の定数リスト    # Japanese command (constant list)
13のレベルリスト  # Japanese command (level list)
13 level-list   # English command
```

### What's Displayed

- Left side shows internal constants (e.g., 13.0, 13.1, 13.2, etc.)
- Right side shows all song covers for each constant
- Top shows total song count statistics
- Constants sorted from high to low

### Server Selection

Level queries automatically use the server version set during binding (JP or INTL).

### Use Cases

- 📋 **View constant distribution**: Understand constant ranges for a difficulty
- 🎯 **Find target songs**: Find songs in specific constant ranges
- 📊 **Compare difficulties**: Compare song counts across different levels

## Level & Rank Progress

View achievement progress for a specific difficulty level and rank, such as checking progress towards achieving SSS+ rank on all 13+ difficulty charts.

### Command Format

```
13sss+進捗        # View 13 difficulty SSS+ rank progress
13+sss progress   # View 13+ difficulty SSS rank progress (English)
14AP progress 2   # View 14 difficulty AP rank progress (page 2)
15fdx+ progress   # View 15 difficulty FDX+ rank progress
```

### Supported Ranks

- **Score Ranks**: S, S+, SS, SS+, SSS, SSS+
- **Full Combo**: FC, FC+, AP, AP+
- **Full Sync**: FDX, FDX+

::: tip Command Notes
- Rank names are case-insensitive (SSS equals sss)
- Supports both Japanese (進捗) and English (progress) keywords
- Add page number at the end to view more charts
- Supported difficulty levels: 11, 11+, 12, 12+, 13, 13+, 14, 14+, 15
:::

### What's Displayed

- **Completed**: Charts that achieved the target rank (up to 35 per page)
- **Incomplete**: Charts that haven't reached the target rank (up to 15 per page)
- Sorted by achievement rate from high to low
- First page displays statistics:
  - Number of completed charts
  - Number of incomplete charts
  - Number of unplayed charts
  - Total number of charts

### Use Cases

- 🎯 **Goal Tracking**: See how close you are to completing a specific rank for a difficulty
- 📊 **Progress Statistics**: Understand overall achievement status for a difficulty rank
- 🔍 **Find Target Charts**: Quickly find charts close to the target rank for practice
- 📈 **Growth Tracking**: Browse through all related charts via pagination to see your progress

### Examples

```
13sss進捗         # View 13 difficulty SSS rank progress (page 1)
13sss進捗 2       # View 13 difficulty SSS rank progress (page 2)
14+ap+ progress   # View 14+ difficulty AP+ rank progress
15fdx progress 3  # View 15 difficulty FDX rank progress (page 3)
```

## Related Features

- 🔍 [Score Search](/en/features/search) - Search for specific songs

---

Next: [Learn about advanced score search →](/en/features/search)
