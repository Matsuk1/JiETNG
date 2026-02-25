# JiETNG Complete Command List

This document lists all available commands for the JiETNG LINE Bot.

---

## Table of Contents

- [Basic Commands](#basic-commands)
- [Account Management](#account-management)
- [Score Queries](#score-queries)
- [Song Queries](#song-queries)
- [Version Achievements](#version-achievements)
- [Friend Features](#friend-features)
- [Utility Commands](#utility-commands)

---

## Basic Commands

### Support

| Command | Aliases | Description |
|---------|---------|-------------|
| `donate` | None | Display donation information to support JiETNG's development |
| `status` | None | Display bot status (uptime, CPU, memory, etc.) |
| `command` | `cmd` | Display the list of available score commands |

---

## Account Management

### Binding and Viewing

| Command | Aliases | Description |
|---------|---------|-------------|
| `bind` | None | Bind SEGA account |
| `profile` | `getme` | View current account binding info |
| `unbind` | None | Unbind account |
| `settings` | `rebind` | Update account settings (password, timezone, language, version, etc.) without unbinding |

### Data Update

| Command | Aliases | Description |
|---------|---------|-------------|
| `maimai update` | `update` | Sync latest scores from maimai NET |

**Notes**:
- Data update requires SEGA account binding
- Update typically completes within seconds
- Rate limit: Maximum 2 requests per 30 seconds

---

## Score Queries

### Standard Score Charts

| Command | Aliases | Description |
|---------|---------|-------------|
| `b50` | `best50` | Best 35 (old ver.) + Best 15 (new ver.) |
| `b40` | `best40` | Best 25 (old ver.) + Best 15 (new ver.) - Legacy Rating calculation |
| `b100` | `best100` | Best 70 (old ver.) + Best 30 (new ver.) |
| `b35` | `best35` | Old version Best 35 only |
| `b15` | `best15` | New version Best 15 only |

### Special Score Charts

| Command | Aliases | Description |
|---------|---------|-------------|
| `ab35` | `allb35` | Mixed version Best 35 |
| `ab50` | `allb50` | Mixed version Best 50 |
| `ab100` | `allb100` | Mixed version Best 100 |
| `apb50` | `ap50` | AP/AP+ only Best 50 |
| `fdxb50` | `fdx50` | FDX/FDX+ only Best 50 |
| `rct50` | `r50`, `recent50` | Recent 50 plays |
| `idealb50` | `idlb50` | Ideal Best 50 |

### Advanced Filters

All score chart commands support the following filters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `-lv [value] [max]` | Filter by chart constant. Single value = exact match; two values = range | `b50 -lv 13.2 13.8` or `b50 -lv 13.7` |
| `-ra [value] [max]` | Filter by Rating. Single value = exact match; two values = range | `b50 -ra 301 312` or `b50 -ra 301` |
| `-star [value] [max]` | Filter by DX star count. Single value = exact match; two values = range | `b50 -star 3 5` or `b50 -star 3` |
| `-scr [min] [max]` | Filter by achievement rate (max optional, unlimited if omitted) | `b50 -scr 100.3 100.8` or `b50 -scr 100.3` |
| `-dx [min] [max]` | Filter by DX score percentage (max optional, unlimited if omitted) | `b50 -dx 92 95` or `b50 -dx 92` |

**Note**: Filter behavior differs by parameter type:
- `-lv 13.7` means chart constant = 13.7 (exact match); use `-lv 13.5 14.0` for a range
- `-ra 301` means Rating = 301 (exact match); use `-ra 301 312` for a range
- `-star 3` means DX star count = 3 (exact match); use `-star 3 5` for a range
- `-scr 100.3` means achievement ≥100.3% (no upper limit)
- `-dx 92` means DX score ≥92% (no upper limit)

#### Filter Examples

```
b50 -lv 13.2 13.8                    # B50 with constant 13.2-13.8
b50 -lv 13.7                         # B50 with constant exactly 13.7
b50 -ra 301 312                      # B50 with Rating 301-312
b50 -ra 301                          # B50 with exactly Rating 301
b50 -star 3 5                        # B50 with DX star count 3-5
b50 -star 3                          # B50 with exactly 3 DX stars
b50 -scr 100.3 100.8                 # B50 with achievement 100.3%-100.8%
b50 -scr 100.3                       # B50 with achievement ≥100.3% (no limit)
b50 -dx 92 95                        # B50 with DX score 92%-95%
b50 -dx 92                           # B50 with DX score ≥92% (no limit)
b50 -lv 13.2 13.8 -scr 100.0         # B50 with constant 13.2-13.8 and achievement ≥100%
b100 -lv 13.0 14.9 -dx 92 95         # B100 with constant 13.0-14.9 and DX 92%-95%
idealb50 -lv 13.5 14.0               # Ideal B50 with constant 13.5-14.0
```

---

## Song Queries

### Song Information

| Command Format | Aliases | Description | Example |
|----------------|---------|-------------|---------|
| `[Song]ってどんな曲` | `[Song]info`, `[Song]song-info` | Search song details | `ヒバナってどんな曲` |
| `[Song]のレコード` | `[Song]record`, `[Song]song-record` | View personal score | `ヒバナのレコード` |

### Level Score List & Constant List

| Command Format | Aliases | Description | Example |
|----------------|---------|-------------|---------|
| `[Level]のレコードリスト (Page)` | `[Level]record-list (Page)`, `[Level]records (Page)` | View all scores for specified level | `13のレコードリスト` |
| `[Constant]のレコードリスト (Page)` | `[Constant]record-list (Page)`, `[Constant]records (Page)` | View all scores for specified constant | `14.5のレコードリスト` |

**Notes**:
- **Level List**: Enter an integer (1-15) to view all charts in that level
  - Example: `13のレコードリスト` - View all Lv.13 chart scores
- **Constant List**: Enter a decimal to view all charts with specified constant
  - Example: `14.5のレコードリスト` - View all constant 14.5 chart scores
  - Example: `13.7のレコードリスト` - View all constant 13.7 chart scores
- Up to 50 records per page (up to 35 old version + up to 15 new version), use page parameter to navigate
- Automatically sorted by Rating in descending order

---

## Version Achievements

### Plate Achievement Status

**Command Format**: `[Version Nameplate]の達成状況`

**Aliases**: Use `achievement-list` or `achievement` to replace `の達成状況`

| Plate Type | Example | Description |
|------------|---------|-------------|
| 極 (Extreme) | `宴極の達成状況` | View "宴極" plate achievement |
| 将 (Master) | `双将の達成状況` | View "双将" plate achievement |
| 神 (God) | `鏡神の達成状況` | View "鏡神" plate achievement |
| 舞舞 (Dancer) | `彩舞舞の達成状況` | View "彩舞舞" plate achievement |

**More Examples**:
```
宴極の達成状況                # 宴 Extreme
双将の達成状況                # 双 Master
鏡神の達成状況                # 鏡 God
彩舞舞の達成状況              # 彩 Dancer
真極の達成状況                # 真 Extreme
真将の達成状況                # 真 Master
真神の達成状況                # 真 God
真舞舞の達成状況              # 真 Dancer
```

**English Alias Examples**:
```
宴極achievement-list            # Same as 宴極の達成状況
双将achievement                 # Same as 双将の達成状況
```

### Version Song List

| Command Format | Aliases | Description | Example |
|----------------|---------|-------------|---------|
| `[Version]のバージョンリスト` | `[Version]version-list`, `[Version]version` | View all songs in that version | `PRiSM PLUSのバージョンリスト` |

**Version Examples**:
```
PRiSM PLUSのバージョンリスト
FESTiVAL PLUSのバージョンリスト
BUDDiESのバージョンリスト
UNiVERSEのバージョンリスト
```

---

## Friend Features

### Friend Management

| Command | Aliases | Description |
|---------|---------|-------------|
| `friend list` | `friends` | View added friends list |
| `friend-rcd [Code] [type?] [filters?]` | None | View friend's score chart |

**Examples**:
```
friend list                                   # View friends list
friend-rcd 1234567890123456                   # View friend's B50 (default)
friend-rcd 1234567890123456 b100              # View friend's B100
friend-rcd 1234567890123456 b50 -lv 14.7     # View friend's B50 (constant 14.7)
```

**Notes**:
- Requires SEGA account binding
- `[type]` supports all B-series commands (b50, b100, ab50, etc.), defaults to b50
- `[filters]` supports the same filter parameters as b50 (-lv, -ra, -scr, etc.)
- Private chat only, not available in group chats

---

## Utility Commands

### Rating Calculator

| Command | Description | Example |
|---------|-------------|---------|
| `rc [constant]` | View Rating table for specified constant | `rc 13.2` |

### Score Calculator

| Command | Description | Example |
|---------|-------------|---------|
| `calc [tap] [hold] [slide] (touch) [break]` | Calculate notes' score | `calc 500 100 200 50 50` |

**Notes**:
- Calculator shows achievement for various miss types (Great/Good/Miss)
- Supports both 4-parameter (no touch) and 5-parameter (with touch) formats

### Random Song

| Command | Description | Example |
|---------|-------------|---------|
| `random (level/levelValue)` | Randomly select a song | `random 14` |

### Location Service

| Feature | Description |
|---------|-------------|
| Send Location | Find nearby maimai arcades (up to 4 locations) |

**Notes**:
- In LINE, tap "+" button and select "Location"
- Send your current location or any location
- Bot will return nearby maimai arcade information (name, address, distance, map link)

### Leaderboard

| Command | Aliases | Description |
|---------|---------|-------------|
| `rank` | `ranking`, `ランキング` | View DX Rating leaderboard for your current version |
| `rank jp` | `ranking jp`, `ランキング jp` | View JP server DX Rating leaderboard |
| `rank intl` | `ranking intl`, `ランキング intl` | View International server DX Rating leaderboard |

**Notes**:
- Displays DX Rating rankings among JiETNG users in the same version
- Specify `jp` or `intl` to view the leaderboard for a specific version

---

## @Mention Feature

In group chats, mention (@) another registered JiETNG user to view their score data.

**Usage**: Mention a user + command (mention can appear anywhere before or within the command)

**Examples**:
```
@friend b50              # View friend's B50
@friend profile          # View friend's account info
@friend 14 record-list   # View friend's Lv14 score list
```

**Notes**:
- The mentioned user must be a registered JiETNG user, otherwise falls back to your own data
- Supports all score-related commands (b50, b100, record-list, progress, etc.)

---

## Quick Reference

### Common Commands

```
donate                     # View donation support options
bind                       # Bind SEGA account
settings                   # Update account settings
update                     # Update score data
b50                        # View B50
rank                       # View DX Rating leaderboard
ヒバナってどんな曲            # View song info
ヒバナのレコード              # View personal score
宴極の達成状況               # View Extreme achievement
friend list                # Friends list
```

### Filter Examples

```
b50 -lv 13.2 13.8          # Constant 13.2-13.8
b50 -lv 13.7               # Exactly constant 13.7
b50 -ra 301 312            # Rating 301-312
b50 -ra 301                # Exactly Rating 301
b50 -star 3 5              # DX star count 3-5
b50 -star 3                # Exactly 3 DX stars
b50 -scr 100.3 100.8       # Achievement 100.3%-100.8%
b50 -scr 100.3             # Achievement ≥100.3% (no limit)
b50 -dx 92 95              # DX score 92%-95%
b50 -dx 92                 # DX score ≥92% (no limit)
```

---

**Last Updated**: 2026-02-25
**Version**: Generated from main.py analysis
