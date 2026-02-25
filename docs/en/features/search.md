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

- **Song Title** (English & Japanese)
- **Cover Art**
- **Artist**
- **Version Information**
- **Available Difficulties** (Basic / Advanced / Expert / Master / Re:MASTER)
- **Chart Constant**
- **Chart Type** (Standard / DX)
- **Category (Genre)**

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
- Achievement Rate
- DX Score
- Completion Status (FC / FC+ / AP / AP+)
- Sync Status (FS / FS+ / FDX / FDX+)
- Rating Contribution Value

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

