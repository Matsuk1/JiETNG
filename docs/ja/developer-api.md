# 開発者 API

JiETNG には 2 種類の API があります。

- **開発者 API**：開発者 Token で呼び出し、ユーザー管理、連携リンク、権限、画像生成に使います。
- **ユーザー Import API**：ユーザー Import Token で呼び出し、加工済み成績 JSON をアップロードします。

既定のエンドポイント：

```text
https://jietng-endpoint.matsuk1.com
```

## 認証

開発者 API：

```http
Authorization: Bearer <developer_token>
```

Import API：

```http
Authorization: Bearer <import_token>
```

開発者 Token と Import Token は別物です。Import Token は単一ユーザーに属し、そのユーザーの成績アップロードにだけ使います。

## 開発者 Token

LINE で管理します。

```text
devtoken create <メモ>
devtoken list
devtoken revoke <token_id>
devtoken info <token_id>
```

平文 token は作成時に一度だけ表示されます。

## 権限

開発者 Token がユーザーにアクセスできる条件：

- その Token がユーザーを作成した owner である。
- ユーザーがその Token の権限リクエストを承認した。

権限エンドポイント：

```http
POST /api/v2/users/<user_id>/permissions
PATCH /api/v2/users/<user_id>/permissions/requests/<request_id>
DELETE /api/v2/users/<user_id>/permissions/<token_id>
DELETE /api/v2/users/<user_id>/permissions/self
```

ユーザーは LINE でも処理できます。

```text
accept-perm-request <request_id>
reject-perm-request <request_id>
```

## ユーザー関連

```http
POST /api/v2/users
POST /api/v2/users/<user_id>/bind
PUT /api/v2/users/<user_id>/bind
GET /api/v2/users/<user_id>/bind-url
GET /api/v2/users/<user_id>/rebind-url
GET /api/v2/users/<user_id>/settings-url
POST /api/v2/users/<user_id>/sync/stream
```

`/sync/stream` は `application/x-ndjson` を返し、最初の行が `accepted`、最後の行が `completed` または `failed` になります。同期には完全な SEGA 連携が必要です。Import Token ユーザーは加工済み成績をアップロードしてください。

## スコア画像

```http
GET /api/v2/users/<user_id>/image?command=b50
GET /api/v2/users/<user_id>/songs/<song_id>/image
GET /api/v2/users/<user_id>/plate?title=真神
GET /api/v2/users/<user_id>/achievement?level=14%2B&rank=sss
GET /api/v2/songs/<song_id>/image
GET /api/v2/users/<user_id>/export?fmt=json
GET /api/v2/dxdata?ver=jp
```

### リザルト画像 OCR

```http
POST /api/v2/score-recognition
Authorization: Bearer <developer_token>
Content-Type: multipart/form-data
```

multipart フィールド：

| フィールド | 型 | 必須 | 説明 |
|------------|----|------|------|
| `image` | file | はい | JPEG、PNG、WebP。既定の上限は 20 MiB、4000 万画素 |
| `ver` | text | いいえ | `jp` または `intl`。既定は `jp` |

OCR は同期実行されます。曲名、達成率、完全な判定表を 1 つの譜面に照合して検証できた場合だけ成功します。メイン画面のみ、副画面が不完全、楽曲を特定できない場合は `422` を返します。

```bash
curl -X POST https://jietng-endpoint.matsuk1.com/api/v2/score-recognition \
  -H "Authorization: Bearer <developer_token>" \
  -F "ver=jp" \
  -F "image=@result.jpg"
```

成功 JSON の構造：

- `song`：dxdata の `id`、正式な `title`、`type`（`dx` / `std`）。
- `chart`：`difficulty`、表示レベル `level`、譜面定数 `internal_level`。
- `score.achievement`：達成率。
- `score.judgements`：`tap`、`hold`、`slide`、`touch`、`break`。各行は `critical_perfect`、`perfect`、`great`、`good`、`miss` を必ず含みます。
- `score.break_detail`：Flex で表示する現在最も可能性の高い BREAK 詳細判定です。`candidate_count` は選択した BREAK 行内の詳細候補数、Calc が行全体を推定した場合の任意フィールド `row_candidate_count` は行候補数です。離散的に一致する候補がない場合は `{}` です。
- `validation`：曲名一致方式、行列補正、MISS 補正、Calc 検証・補正、不確実な OCR セル。

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

### OCR 結果画像

`POST /api/v2/score-recognition/image` は JSON エンドポイントと同じ multipart の `image`、`ver`、アップロード制限、認証方式を使用します。成功時は生成済みの `image/png` を返します。

```bash
curl -X POST https://jietng-endpoint.matsuk1.com/api/v2/score-recognition/image \
  -H "Authorization: Bearer <developer_token>" \
  -F "ver=jp" \
  -F "image=@result.jpg" \
  --output ocr-result.png
```

Calc に複数の有効解がある場合、画像エンドポイントは順位が最も高い候補を描画します。レスポンスヘッダー `X-JiETNG-OCR-Candidate-Index` と `X-JiETNG-OCR-Candidate-Count` で候補番号と候補総数を確認できます。

アップロード上限は `SCORE_RECOGNITION_API_MAX_IMAGE_BYTES` で変更できます。開発者 Token ごとにレート制限されます。

`/songs/search` のバージョン選択は、明示された `ver`、`user_id` に保存されたサーバー、既定の `jp` の順です。

`command` はユーザーが入力できる B 系コマンドを受け付けます。

| command | 意味 |
|---------|------|
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
| `s50` / `sun50` / `寸50` / `寸止め` | SSS+ / SSS 寸止め 50 |
| `unknown` | バージョン不明楽曲 |

`b50 -lv 14.7` のようにフィルターも含められます。

## ブックマークレット画像

```http
POST /api/web/session-image
Content-Type: application/json
```

ブックマークレットの JSON を受け取り、`image/png` を返します。開発者 Token は不要ですが、CORS は公式 maimai モバイルページ向けです。

主な body：

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

このエンドポイントは画像生成のみです。保存には Import API を使います。

## 成績インポート

ユーザーは `settings` ページで Import Token を作成します。平文は一度だけ表示されます。

```http
POST /api/v2/import/records
Authorization: Bearer <import_token>
Content-Type: application/json
```

例：

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

`rating_block_path` はアップロード不要です。サーバーが `rating` から計算します。

置き換え規則：

- `"records": {"best": []}` は Best を空にします。
- `"records": {"recent": []}` は Recent を空にします。
- セクションを省略すると既存データを保持します。

成功レスポンス：

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

ブックマークレット用 API は次の公式サイトを想定しています。

- `https://maimaidx.jp`
- `https://maimaidx-eng.com`

## エラー

| 状態 | 主な理由 |
|------|----------|
| `400` | パラメータまたは payload 不正 |
| `401` | Token 無効、SEGA 認証失敗 |
| `403` | 権限なし |
| `404` | ユーザー、Token、リクエスト、タスクがない |
| `409` | 連携状態の衝突 |
| `413` | OCR 画像がアップロード上限を超えた |
| `415` | OCR 画像形式が未対応 |
| `422` | 完全な成績として認識・検証できない画像 |
| `429` | レート制限 |
| `503` | 公式メンテナンスまたは同期キュー満杯 |

## 安全上の注意

- 開発者 Token や Import Token を公開フロントエンドに埋め込まないでください。
- Import Token はユーザー自身のブラウザまたは信頼できるツール用です。
- 第三者アプリは開発者 Token とユーザー権限フローを使ってください。
- unlink 時は `DELETE /api/v2/users/<user_id>/permissions/self` を呼び出してください。
