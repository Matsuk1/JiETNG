# Developer API

JiETNG exposes two API groups:

- **Developer API**: called with developer tokens for user management, binding links, permissions, and image generation.
- **User Import API**: called with a user Import Token to upload processed score JSON.

Default endpoint:

```text
https://jietng-endpoint.matsuk1.com
```

## Authentication

Developer API:

```http
Authorization: Bearer <developer_token>
```

Import API:

```http
Authorization: Bearer <import_token>
```

Developer tokens and Import Tokens are different credentials. Developer tokens are for integrations. Import Tokens belong to one user and only upload that user's records.

## Developer Tokens

Manage tokens in LINE:

```text
devtoken create <note>
devtoken list
devtoken revoke <token_id>
devtoken info <token_id>
```

The plaintext token is shown only once.

## Permissions

A developer token can access a user when:

- the token created that user and is the owner, or
- the user accepted a permission request from that token.

Permission endpoints:

```http
POST /api/v2/users/<user_id>/permissions
PATCH /api/v2/users/<user_id>/permissions/requests/<request_id>
DELETE /api/v2/users/<user_id>/permissions/<token_id>
DELETE /api/v2/users/<user_id>/permissions/self
```

Users can also handle requests in LINE:

```text
accept-perm-request <request_id>
reject-perm-request <request_id>
```

## User Endpoints

```http
POST /api/v2/users
POST /api/v2/users/<user_id>/bind
PUT /api/v2/users/<user_id>/bind
GET /api/v2/users/<user_id>/bind-url
GET /api/v2/users/<user_id>/rebind-url
GET /api/v2/users/<user_id>/settings-url
POST /api/v2/users/<user_id>/sync/stream
```

`/sync/stream` returns `application/x-ndjson`: the first line is `accepted`, then the final line is `completed` or `failed`. Sync requires a full SEGA binding. Import Token users should upload processed records instead.

## Score Image

```http
GET /api/v2/users/<user_id>/image?command=b50
GET /api/v2/users/<user_id>/songs/<song_id>/image
GET /api/v2/users/<user_id>/plate?title=真神
GET /api/v2/users/<user_id>/achievement?level=14%2B&rank=sss
GET /api/v2/songs/<song_id>/image
GET /api/v2/users/<user_id>/export?fmt=json
GET /api/v2/dxdata?ver=jp
```

### Score-result OCR

```http
POST /api/v2/score-recognition
Authorization: Bearer <developer_token>
Content-Type: multipart/form-data
```

Multipart fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | file | yes | JPEG, PNG, or WebP result image; defaults to 20 MiB and 40 million pixels maximum |
| `ver` | text | no | `jp` or `intl`; defaults to `jp` and selects the song/chart dataset |

OCR runs synchronously. A response is successful only when the title, achievement, and complete judgement table can be matched and validated against one chart. Main-screen-only images, incomplete sub-screens, and unidentified songs return `422`.

```bash
curl -X POST https://jietng-endpoint.matsuk1.com/api/v2/score-recognition \
  -H "Authorization: Bearer <developer_token>" \
  -F "ver=jp" \
  -F "image=@result.jpg"
```

The successful JSON contains:

- `song`: dxdata `id`, canonical `title`, and `type` (`dx` or `std`).
- `chart`: `difficulty`, displayed `level`, and numeric `internal_level`.
- `score.achievement`: recognized achievement percentage.
- `score.judgements`: fixed `tap`, `hold`, `slide`, `touch`, and `break` rows; each contains `critical_perfect`, `perfect`, `great`, `good`, and `miss`.
- `score.break_detail`: the current most likely BREAK sub-grades shown by the Flex result. `candidate_count` counts sub-grade candidates within the selected BREAK row; optional `row_candidate_count` counts feasible aggregate rows when Calc inferred the entire row. It is `{}` when no discrete match is available.
- `validation`: title match type, row/column alignment, MISS corrections, Calc range/corrections, and uncertain OCR cells.

Example response:

```json
{
  "success": true,
  "song": {"id": "50d3df", "title": "Little \"Sister\" Bitch", "type": "dx"},
  "chart": {"difficulty": "master", "level": "13+", "internal_level": 13.8},
  "score": {
    "achievement": 100.5658,
    "judgements": {
      "tap": {"critical_perfect": 403, "perfect": 225, "great": 15, "good": 0, "miss": 1},
      "hold": {"critical_perfect": 18, "perfect": 7, "great": 0, "good": 0, "miss": 0},
      "slide": {"critical_perfect": 98, "perfect": 0, "great": 0, "good": 0, "miss": 0},
      "touch": {"critical_perfect": 66, "perfect": 0, "great": 0, "good": 0, "miss": 0},
      "break": {"critical_perfect": 20, "perfect": 13, "great": 0, "good": 0, "miss": 0}
    },
    "break_detail": {"critical_perfect": 20, "perfect_high": 12, "perfect_low": 1, "great_high": 0, "great_middle": 0, "great_low": 0, "good": 0, "miss": 0, "candidate_count": 1}
  },
  "validation": {
    "title_match_type": "exact",
    "exact_title_match": true,
    "compared_rows": 5,
    "matching_rows": 5,
    "row_offset": 0,
    "column_offset": 0,
    "miss_corrections": {},
    "achievement_calc": {"observed": 100.5658, "minimum": 100.4749, "maximum": 100.5733, "consistent": true, "complete": true},
    "calc_corrections": [],
    "uncertain_cells": []
  }
}
```

### OCR result image

`POST /api/v2/score-recognition/image` accepts the same multipart `image` and `ver` fields, limits, and authentication as the JSON endpoint. A successful request returns the rendered result as `image/png`:

```bash
curl -X POST https://jietng-endpoint.matsuk1.com/api/v2/score-recognition/image \
  -H "Authorization: Bearer <developer_token>" \
  -F "ver=jp" \
  -F "image=@result.jpg" \
  --output ocr-result.png
```

When Calc finds multiple valid results, the image endpoint renders the highest-ranked candidate. `X-JiETNG-OCR-Candidate-Index` and `X-JiETNG-OCR-Candidate-Count` report its index and the total candidate count.

The server upload limit can be changed with `SCORE_RECOGNITION_API_MAX_IMAGE_BYTES`. Requests are rate-limited per developer token.

`/songs/search` chooses the version in this order: explicit `ver`, then the version stored on `user_id`, then `jp`.

`command` accepts the same B-series words users can type:

| command | Meaning |
|---------|---------|
| `b50` / `best50` | Best 50 |
| `b40` / `best40` | Best 40 |
| `b35` / `best35` | Best 35 |
| `b15` / `best15` | Best 15 |
| `ab35` / `allb35` | All Best 35 |
| `ab50` / `allb50` | All Best 50 |
| `apb50` / `ap50` | AP Best 50 |
| `fdxb50` / `fdx50` | FDX Best 50 |
| `rct50` / `r50` | Recent 50 |
| `idealb50` / `idlb50` | Ideal Best 50 |
| `s50` / `sun50` / `寸50` / `寸止め` | Near-miss 50 for SSS+ / SSS |
| `unknown` | Songs with unknown version |

Filters can be included in the command string, for example `b50 -lv 14.7`.

## Bookmarklet Image Endpoint

```http
POST /api/web/session-image
Content-Type: application/json
```

Receives bookmarklet JSON and returns `image/png`. It does not require a developer token, but CORS is intended for official maimai mobile pages.

Core body:

```json
{
  "ver": "jp",
  "command": "b50",
  "params": "-lv 14",
  "timezone": 9,
  "profile": {},
  "records": []
}
```

This endpoint generates an image only. Use Import API to save records.

## Import Records

Users create Import Tokens from the `settings` page. Plaintext is shown only once.

```http
POST /api/v2/import/records
Authorization: Bearer <import_token>
Content-Type: application/json
```

Example:

```json
{
  "version": "jp",
  "profile": {
    "name": "Player",
    "rating": 15392,
    "trophy": "真皆伝",
    "trophy_content": "真皆伝",
    "trophy_url": "https://...",
    "icon_url": "https://...",
    "nameplate_url": "https://...",
    "class_rank_url": "https://...",
    "course_rank_url": "https://..."
  },
  "records": {
    "best": [
      {
        "title": "Song Title",
        "type": "DX",
        "difficulty": "Master",
        "achievement": 100.5,
        "dx_score": 1234,
        "dx_score_max": 1500,
        "rank": "SSS+",
        "combo": "AP+",
        "sync": "FDX+"
      }
    ],
    "recent": []
  }
}
```

`rating_block_path` does not need to be uploaded; the server derives it from `rating`.

Replacement rules:

- `"records": {"best": []}` clears Best.
- `"records": {"recent": []}` clears Recent.
- Omitting a section keeps existing server data.

Success:

```json
{
  "success": true,
  "user_id": "U...",
  "best_count": 1200,
  "recent_count": 50,
  "version": "jp",
  "message": "Records imported successfully."
}
```

## CORS

Bookmarklet endpoints are designed for:

- `https://maimaidx.jp`
- `https://maimaidx-eng.com`

## Error Codes

| Status | Typical reason |
|--------|----------------|
| `400` | Invalid parameters or payload |
| `401` | Invalid token or SEGA credentials |
| `403` | Missing permission |
| `404` | User, token, request, or task not found |
| `409` | Binding conflict |
| `413` | OCR image exceeds the upload limit |
| `415` | Unsupported OCR image format |
| `422` | Valid image that cannot be recognized and validated as a complete score |
| `429` | Rate limit exceeded |
| `503` | Official maintenance or full sync queue |

## Safety

- Do not ship developer tokens or Import Tokens in public frontend code.
- Import Tokens are for the user's own browser or trusted tools.
- Third-party applications should use developer token plus user permission flow.
- When unlinking, call `DELETE /api/v2/users/<user_id>/permissions/self`.
