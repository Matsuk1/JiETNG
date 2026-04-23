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
- [Search Commands](#search-commands)
- [Utility Commands](#utility-commands)

---

## Basic Commands

### Support

| Command | Aliases | Description |
|---------|---------|-------------|
| `donate` | None | Display donation information to support JiETNG's development |
| `status` | None | Display bot status (uptime, CPU, memory, etc.) |

---

## Account Management

### Binding and Viewing

| Command | Aliases | Description |
|---------|---------|-------------|
| `bind` | None | Bind SEGA account |
| `profile` | `getme` | View current account binding info |
| `unbind` | None | Unbind account |
| `rebind` | None | Rebind account (update password, version, Aime). SEGA ID cannot be changed |
| `settings` | None | Update personal settings (timezone, language, background, etc.) |

### Data Update

| Command | Aliases | Description |
|---------|---------|-------------|
| `maimai update` | `update` | Sync latest scores from maimai NET |

---

## Score Queries

### Standard Score Charts

| Command | Aliases | Description |
|---------|---------|-------------|
| `b50` | `best50` | Best 35 (old ver.) + Best 15 (new ver.) |
| `b40` | `best40` | Best 25 (old ver.) + Best 15 (new ver.) - Legacy Rating calculation |
| `b35` | `best35` | Old version Best 35 only |
| `b15` | `best15` | New version Best 15 only |

### Special Score Charts

| Command | Aliases | Description |
|---------|---------|-------------|
| `ab35` | `allb35` | Mixed version Best 35 |
| `ab50` | `allb50` | Mixed version Best 50 |
| `apb50` | `ap50` | AP/AP+ only Best 50 |
| `fdxb50` | `fdx50` | FDX/FDX+ only Best 50 |
| `rct50` | `r50` | Recent 50 plays |
| `idealb50` | `idlb50` | Ideal Best 50 |
| `unknown` | `unkn` | Songs with unknown version |

### Filters

Supports `-lv`, `-ra`, `-scr`, `-dx`, `-star`, `-diff`, `-ver`, `-type`, `-page` and more. See [Record Commands](/en/commands/record#filters) for details.

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

**Aliases**: Use `achievement` to replace `の達成状況`

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
宴極achievement                 # Same as 宴極の達成状況
双将achievement                 # Same as 双将の達成状況
```

### Version Song List

| Command Format | Aliases | Description | Example |
|----------------|---------|-------------|---------|
| `[Version]のバージョンリスト` | `[Version] version-list` | View all songs in that version | `PRiSM PLUSのバージョンリスト` |

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
friend-rcd 1234567890123456 b50 -lv 14.7     # View friend's B50 (constant 14.7)
```

**Notes**:
- Requires SEGA account binding
- `[type]` supports all B-series commands (b50, ab50, etc.), defaults to b50
- `[filters]` supports the same filter parameters as b50 (-lv, -ra, -scr, etc.)
- Private chat only, not available in group chats

---

## Search Commands

### Song Search

| Command Format | Description | Example |
|----------------|-------------|---------|
| `artist <keyword> [page]` | Search songs by artist name | `artist Nanahira` |
| `designer <keyword> [page]` | Search songs by chart designer | `designer Jack` |

**Notes**:
- Private chat only (to prevent spam in groups)
- Keywords are case-insensitive
- Use page parameter to navigate results

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
| Send Location | Find nearby maimai arcades |

**Notes**:
- In LINE, tap "+" button and select "Location"
- Send your current location or any location
- Bot will return nearby maimai arcade information

### Leaderboard

| Command | Aliases | Description |
|---------|---------|-------------|
| `rank` | `ranking` | View DX Rating leaderboard for your current version |
| `rank jp` | `ranking jp` | View JP server DX Rating leaderboard |
| `rank intl` | `ranking intl` | View International server DX Rating leaderboard |

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
- Supports all score-related commands (b50, record-list, progress, etc.)

