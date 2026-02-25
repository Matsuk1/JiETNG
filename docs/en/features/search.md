# Song Search and Record Query

## Song Information Search

```
[song name] info
[song name] song-info
[song name] ってどんな曲
```

Fuzzy matching with 85% similarity threshold, returns up to 6 results. Case-insensitive; special symbols can be omitted.

**Displays:** Song title (English/Japanese), cover art, artist, version, available difficulties, chart constant, chart type (Standard / DX), genre.

---

## Songs by Version

```
[version name] version
[version name] version-list
[version name] のバージョンリスト
```

`FESTiVAL+` is automatically recognized as `FESTiVAL PLUS`.

---

## Search by Artist

```
artist [keyword]
artist [keyword] [page]
```

**Displays:** Song title, artist name, chart type (DX / STD / UTAGE)

:::warning Private chat only
:::

---

## Search by Chart Designer

```
designer [keyword]
designer [keyword] [page]
```

**Displays:** Song title, matched designer name with difficulty label (e.g. `Jack [EXP]`), chart type (DX / STD / UTAGE)

:::warning Private chat only
:::

---

## Single Song Record

```
[song name] record
[song name] song-record
[song name] のレコード
```

**Displays:** Achievement rate, DX score, combo status (FC/FC+/AP/AP+), sync status (FS/FS+/FDX/FDX+), Rating contribution.

---

## Records by Level

```
[level] record-list
[level] records
[level] のレコードリスト
[level] record-list [page]
```

- Integer (e.g. `14`) matches 14.0~14.5; `14+` matches 14.6~14.9; decimal (e.g. `14.7`) is an exact match
- Up to 50 songs per page (old ver. 35 + new ver. 15)
