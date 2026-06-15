# JiETNG maimai session image bookmarklet

This tool runs inside the logged-in maimai DX mobile site and uses the current
browser session to collect profile and best records, then renders a score image
inside an overlay on the original maimai page.

The panel can generate B-series record images from the same collected Best
records without re-fetching the maimai pages: `B50`, `B40`, `B35`, `B15`,
`AB35`, `AB50`, `AP50`, `FDX50`, and `IDLB50`. It also accepts the same filter
string used by the native b-records command, such as `-lv 13 -diff mas`. The
collected records are cached in `sessionStorage`, so refreshing the same browser
tab and opening the bookmarklet again still reuses the cached records. The last
selected options and generated preview are also restored when the bookmarklet is
opened again in that tab.

It does not read or ask for SEGA ID passwords. The browser sends existing
maimaidx cookies to same-origin maimai pages.

Supported official domains:

- JP: `https://maimaidx.jp/maimai-mobile/home/`
- INTL: `https://maimaidx-eng.com/maimai-mobile/home/`

## Usage

1. Open `https://maimaidx.jp/maimai-mobile/home/` and log in.
2. Create a browser bookmark.
3. Set the bookmark URL to the generated code in `dist/bookmarklet.txt`.
4. Click the bookmark while staying on the maimai mobile site.
5. The bookmarklet collects records and shows the generated PNG image in an
   overlay on the same maimai page.

The same bookmarklet also supports the international site:
`https://maimaidx-eng.com/maimai-mobile/home/`.

## Build the bookmarklet URL

From the repository root:

```bash
python3 bookmarklet/build.py
```

The generated URL is written to:

```text
bookmarklet/dist/bookmarklet.txt
```

## Payload schema

The bookmarklet sends this JSON shape to JiETNG:

```json
{
  "schema": "jietng.maimai.session_image.v1",
  "source": "maimai-session-bookmarklet",
  "captured_at": "2026-06-14T00:00:00.000Z",
  "origin": "https://maimaidx.jp",
  "version": "jp",
  "cmd_type": "best50",
  "command": "-lv 13 -diff mas",
  "profile": {
    "name": "player",
    "rating": "15000"
  },
  "records": {
    "best": []
  }
}
```

Record items are intentionally close to JiETNG's internal write format:

```json
{
  "name": "song title",
  "difficulty": "master",
  "type": "dx",
  "score": "100.5000%",
  "dx_score": "1234 / 1234",
  "score_icon": "sssp",
  "combo_icon": "ap",
  "sync_icon": "fdx"
}
```

## Web API

The endpoint is a direct JSON-to-PNG API:

```http
POST https://jietng-endpoint.matsuk1.com/api/web/session-image
Content-Type: application/json
```

Allowed CORS origins are the two official maimai mobile origins:

- `https://maimaidx.jp`
- `https://maimaidx-eng.com`

The endpoint returns `image/png` and does not write records to the database.
The bookmarklet converts the PNG response into a local blob URL and displays it
in an overlay on the source maimai page.
