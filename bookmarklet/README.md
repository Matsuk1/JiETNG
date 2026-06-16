# JiETNG maimai session image bookmarklet

This bookmarklet runs inside the logged-in maimai DX mobile site and uses the
current browser session to collect profile, Best records, and Recent records.
It then renders a score image inside an overlay on the original maimai page.

The panel intentionally exposes only two image modes:

- `B50`
- `AP50`

Generate only creates the image. It does not upload records. If the user saves a
JiETNG Import Token in the panel, records can be uploaded explicitly with the
Upload button. Upload sends processed Best and Recent records to
`/api/v2/import/records` and reuses cached page data when available.

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
5. Select `B50` or `AP50`, then click Generate.
6. Use Upload only when you want to send records to JiETNG with an Import Token.

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
docs/public/bookmarklet/maimai-session-image.txt
```

## Payload schema

The bookmarklet sends this JSON shape to JiETNG for image generation:

```json
{
  "schema": "jietng.maimai.session_image.v1",
  "source": "maimai-session-bookmarklet",
  "captured_at": "2026-06-14T00:00:00.000Z",
  "origin": "https://maimaidx.jp",
  "version": "jp",
  "cmd_type": "best50",
  "command": "",
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

Optional manual record import:

```http
POST https://jietng-endpoint.matsuk1.com/api/v2/import/records
Authorization: Bearer <import_token>
Content-Type: application/json
```
