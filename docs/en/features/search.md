# Song Search and Record Query

Find 『maimai でらっくす』 song information, get random songs, and explore the complete song database.

## Song Information Search

Search by song name, abbreviation, or keywords to get detailed information.

### Basic Search

**Command Format:**

```
[song name] + info
[song name] + song-info
[song name] + ってどんな曲
```

**Examples:**

```
blew moon info
グリーンライツ・セレナーデ ってどんな曲
AMAZING MIGHTYYYY song-info
```

### Search Behavior

- **Fuzzy Matching**: Adopts intelligent matching (85% similarity threshold)
- **Multiple Results**: Displays up to 6 matching songs
- **Partial Name Matching**: For example, "amazing might" can match "AMAZING MIGHTYYYY!!!!!"

:::tip Search Tips
- Can use English or Japanese names
- Supports full names and abbreviations
- Case-insensitive
- Special symbols can usually be omitted
:::

### Display Content

Each result includes:

- 📝 **Song Title** (English & Japanese)
- 🎨 **Cover Art**
- 🎵 **Artist**
- 📅 **Version Information**
- 🎮 **Available Difficulties** (Basic / Advanced / Expert / Master / Re:MASTER)
- 📊 **Chart Constant**
- 🎯 **Chart Type** (Standard / DX)
- 🎬 **Category (Genre)**

---

## Random Song

Randomly get a song, with optional level specification.

### Basic Random

**Command Format:**

```
random
random-song
ランダム
ランダム曲
```

**Example:**

```
random
```

Randomly selects a song from the entire 『maimai でらっくす』 song library.

### Random by Level

**Command Format:**

```
random [level]
random-song [level]
ランダム [level]
```

**Examples:**

```
random 14
ランダム曲 13+
random-song 15
```

### Level Filter Syntax

- `14` represents 14.0~14.5
- `13+` represents 13.6~13.9
- `14.6` represents only charts with a constant of 14.6

---

## View Songs by Version

View all songs added in a specific 『maimai でらっくす』 version.

**Command Format:**

```
[version name] + version
[version name] + version-list
[version name] + のバージョンリスト
```

**Examples:**

```
FESTiVAL version
BUDDiES PLUS のバージョンリスト
Splash version-list
でらっくす PLUS version
```

:::tip Tips
- `FESTiVAL+` will be automatically recognized as `FESTiVAL PLUS`
:::

**Display Content:**
- Song list

---

## Search by Artist

Search all songs by a specific artist.

**Command Format:**

```
artist [keyword]
artist [keyword] [page]
```

**Examples:**

```
artist DECO*27
artist しーけー
artist Hiro 2
```

**Display Content:**
- Song title
- Artist name
- Chart type (DX / STD / UTAGE)

:::warning Private Chat Only
To prevent spam, this command can only be used in private chat.
:::

---

## Search by Chart Designer

Search all songs by a specific chart designer (noteDesigner).

**Command Format:**

```
designer [keyword]
designer [keyword] [page]
```

**Examples:**

```
designer Jack
designer はっぴー
designer rioN 3
```

**Display Content:**
- Song title
- Matched designer name with difficulty label (e.g. `Jack [EXP]`, `はっぴー [MAS]`)
- Chart type (DX / STD / UTAGE)

:::warning Private Chat Only
To prevent spam, this command can only be used in private chat.
:::

---

## Score Query

View your play records for a specific song.

**Command Format:**

```
[song name] + record
[song name] + song-record
[song name] + のレコード
```

**Examples:**

```
blew moon record
オンゲキ音頭 のレコード
AMAZING MIGHTYYYY song-record
```

:::warning Account Binding Required
Score features require binding your SEGA ID first. See [Account Binding](/en/guide/binding)
:::

**Display Content:**
- 📊 Achievement Rate
- 🎵 DX Score
- 🏆 Completion Status (FC / FC+ / AP / AP+)
- 💎 Sync Status (FS / FS+ / FDX / FDX+)
- 📈 Rating Contribution Value

If "Record Not Found" is displayed:
- May not have played this song
- Score not updated (try `maimai update`)
- Name matching error (try using info search first)

---

## View Scores by Level

View all scores for a specified level.

**Command Format:**

```
[level] + record-list
[level] + records
[level] + のレコードリスト
```

**Examples:**

```
14 record-list
13+ のレコードリスト
15 records
```

Pagination:
```
14 record-list 2
13+ のレコードリスト 3
```

---

## Comparison: Search vs Score Query

| Feature | Song Info Search | Score Query |
|------|---------------|-----------|
| **Purpose** | Get song data | View personal scores |
| **Binding Required** | ❌ No | ✅ Yes |
| **Display Content** | Song information | Personal data |
| **Use Case** | Explore/learn about songs | Progress tracking |
| **Response Speed** | Fast | Fast (cached) |

---

## Troubleshooting

### "Song Not Found"

**Possible Causes:**
- Spelling error
- Song is not part of 『maimai でらっくす』
- Version error (JP / International)

**Solutions:**
- Try different keywords
- Check [maimai wiki](https://maimai.fandom.com/)
- Try English or Japanese name

### Random Song Repetition

This is normal random probability. You can reduce repetition by filtering by level:
```
random 14+
```

### Version List Incomplete

**Possible Causes:**
- Incorrect name
- Database needs updating

**Solutions:**
- Check spelling
- Try alternative spelling
- Can report at [GitHub Issues](https://github.com/Matsuk1/JiETNG/issues)

---

## Quick Reference

```bash
# Search
[song] info          # Check song information
[song] record        # Check personal score

# Random
random               # Random song
random 14            # Random Lv14

# Version
FESTiVAL version     # View FESTiVAL songs

# Artist / Designer Search
artist DECO*27       # Search by artist
designer Jack        # Search by designer
designer Jack 2      # Page 2

# Level Scores
14 record-list       # Lv14 song scores
13+ records 2        # Page 2 of Lv13+ scores
```
