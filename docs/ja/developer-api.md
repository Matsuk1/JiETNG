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
  "best": [
    {
      "song_id": "123456",
      "title": "Song Title",
      "type": "DX",
      "difficulty": "MASTER",
      "level": "14+",
      "level_index": 3,
      "achievement": 100.5,
      "dx_score": 1234,
      "dx_rating": 312,
      "fc": "AP+",
      "sync": "FDX+"
    }
  ],
  "recent": []
}
```

`rating_block_path` はアップロード不要です。サーバーが `rating` から計算します。

置き換え規則：

- `"best": []` は Best を空にします。
- `"recent": []` は Recent を空にします。
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
| `503` | 公式メンテナンスまたは同期キュー満杯 |

## 安全上の注意

- 開発者 Token や Import Token を公開フロントエンドに埋め込まないでください。
- Import Token はユーザー自身のブラウザまたは信頼できるツール用です。
- 第三者アプリは開発者 Token とユーザー権限フローを使ってください。
- unlink 時は `DELETE /api/v2/users/<user_id>/permissions/self` を呼び出してください。
