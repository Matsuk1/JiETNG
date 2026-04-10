# 開発者 API ドキュメント

## 概要

開発者トークンシステムにより、管理者は第三者アプリケーションやスクリプトがJiETNGのAPIエンドポイントにアクセスするためのAPIアクセストークンを作成・管理できます。

## クイックスタート

### API トークンの取得

JiETNG APIを使用したい場合は、以下の手順でアクセストークンを取得してください:

1. **メールを送信**
   - 宛先: `matsuk1@proton.me`
   - 件名: `JiETNG API Token Request`
   - 内容:
     - お名前または組織名
     - 使用目的の説明
     - 予想される使用頻度

2. **審査を待つ**
   - 管理者があなたの申請を審査し、専用トークンを作成します

3. **トークンを受け取る**
   - メールでトークンIDと完全なトークン文字列を受け取ります
   - **トークンを安全に保管すること。**

### API 基本情報

- **Base URL (v1)**: `https://jietng-endpoint.matsuk1.com/api/v1/`
- **Base URL (v2)**: `https://jietng-endpoint.matsuk1.com/api/v2/`
- **認証方式**: Bearer Token
- **レスポンス形式**: JSON（画像生成エンドポイントは `image/png` を返します）

### 使用例

```bash
# トークンを使用してAPIにアクセス
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     "https://jietng-endpoint.matsuk1.com/api/v1/users"
```

## コマンド使用法

### 管理者コマンド

以下のコマンドはLINE Botで管理者のみが使用できます:

#### 1. トークン作成

```
devtoken create <メモ>
```

**例:**
```
devtoken create MyApp API Integration
```

**返り値:**
- トークンID（管理用）
- 完全なトークン文字列（安全に保管してください）
- メモ

#### 2. すべてのトークンを一覧表示

```
devtoken list
```

**表示内容:**
- トークンID
- メモ
- 状態（Active/Revoked）
- 作成日時
- 最終使用日時

#### 3. トークン無効化

```
devtoken revoke <token_id>
```

**例:**
```
devtoken revoke jt_abc123def456
```

#### 4. トークン詳細表示

```
devtoken info <token_id>
```

**表示内容:**
- トークンID
- 完全なトークン文字列
- メモ
- 状態
- 作成者
- 作成日時
- 最終使用日時

## API 使用法

### Base URL

```
https://jietng-endpoint.matsuk1.com/api/v1/
```

### 認証

すべてのAPIエンドポイントはBearer Token認証が必要です:

```bash
curl -H "Authorization: Bearer <your_token>" https://jietng-endpoint.matsuk1.com/api/v1/...
```

### 利用可能なエンドポイント

v1 エンドポイントは `https://jietng-endpoint.matsuk1.com/api/v1/` をプレフィックスとして使用します。

v2 エンドポイントは `https://jietng-endpoint.matsuk1.com/api/v2/` をプレフィックスとして使用します。

#### 1. ユーザー一覧取得

```http
GET /api/v1/users
```

**例:**
```bash
curl -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuk1.com/api/v1/users
```

**レスポンス:**
```json
{
  "success": true,
  "count": 100,
  "users": [
    {
      "user_id": "U123456",
      "nickname": "ユーザー名"
    },
    ...
  ]
}
```

#### 2. ユーザー登録

```http
POST /api/v1/users
```

**リクエストボディ (JSON):**
- `user_id`: **必須**、ユーザーID
- `nickname`: **必須**、ユーザーのニックネーム（LINEユーザーの場合はLINE APIから自動取得、それ以外の場合はこのパラメータを使用）
- `language`: 言語設定 (ja/en/zh、オプション、デフォルトはen)

**ニックネーム取得の優先順位:**
1. LINE APIから自動取得（LINEユーザーの場合）
2. ユーザーデータのnicknameフィールドから取得
3. 提供されたnicknameパラメータを使用

**例:**
```bash
curl -X POST -H "Authorization: Bearer abc123..." -H "Content-Type: application/json" -d '{"user_id":"U123456","nickname":"TestUser","language":"en"}' https://jietng-endpoint.matsuk1.com/api/v1/users
```

**レスポンス:**
```json
{
  "success": true,
  "user_id": "U123456",
  "nickname": "TestUser",
  "bind_url": "https://jietng-endpoint.matsuk1.com/linebot/sega_bind?token=xxx&nickname=TestUser&language=en",
  "token": "xxx",
  "expires_in": 120,
  "message": "Bind URL generated successfully. Token expires in 2 minutes."
}
```

**登録記録:**

API経由で登録された新規ユーザーは以下の情報を自動的に記録します:
- `registered_via_token`: 登録時に使用されたトークンID
- `registered_at`: 登録タイムスタンプ（形式: YYYY-MM-DD HH:MM:SS）

#### 3. ユーザー情報取得

```http
GET /api/v1/users/<user_id>
```

**例:**
```bash
curl -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuk1.com/api/v1/users/U123456
```

**レスポンス:**
```json
{
  "success": true,
  "user_id": "U123456",
  "nickname": "ユーザー名",
  "data": {
    "language": "ja",
    "sega_id": "...",
    ...
  }
}
```

#### 4. ユーザーを削除

```http
DELETE /api/v1/users/<user_id>
```

**例:**
```bash
curl -X DELETE -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuk1.com/api/v1/users/U123456
```

**レスポンス:**
```json
{
  "success": true,
  "user_id": "U123456",
  "message": "User U123456 has been deleted successfully"
}
```


#### 5. 再連携URLの取得

```http
POST /api/v1/users/<user_id>/rebind-url
```

**説明:** 再連携ページのURLを生成します。SEGA IDのパスワード、バージョンなどのアカウント情報の変更に使用します。

**必要な権限:** 所有者または承認済みトークン

**例:**
```bash
curl -X POST -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/rebind-url
```

**レスポンス (201 Created):**
```json
{
  "success": true,
  "user_id": "U123456",
  "rebind_url": "https://jietng-endpoint.matsuk1.com/linebot/sega_bind?token=xxx&mode=rebind",
  "expires_in": 120,
  "message": "Rebind URL generated successfully."
}
```

#### 6. 設定URLの取得

```http
POST /api/v1/users/<user_id>/settings-url
```

**説明:** 設定ページのURLを生成します。言語、タイムゾーン、背景画像などの個人設定の変更に使用します。

**必要な権限:** 所有者または承認済みトークン

**例:**
```bash
curl -X POST -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/settings-url
```

**レスポンス (201 Created):**
```json
{
  "success": true,
  "user_id": "U123456",
  "settings_url": "https://jietng-endpoint.matsuk1.com/linebot/settings?token=xxx",
  "expires_in": 1800,
  "message": "Settings URL generated successfully."
}
```

#### 7. ユーザーデータ同期

```http
POST /api/v1/users/<user_id>/sync
```

**説明:** 非同期でユーザーデータを同期し、202 Accepted ステータスコードを返します。

**例:**
```bash
curl -X POST -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/sync
```

**レスポンス (202 Accepted):**
```json
{
  "success": true,
  "user_id": "U123456",
  "task_id": "task_xxx",
  "queue_size": 5,
  "message": "User update task queued successfully"
}
```

#### 8. タスク状態確認

```http
GET /api/v1/tasks/<task_id>
```

**説明:**
`/users/<user_id>/sync` で作成された更新タスクの実行状態を確認します。

**例:**
```bash
curl -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuk1.com/api/v1/tasks/task_xxx
```

**レスポンス:**

**タスク処理中:**
```json
{
  "success": true,
  "task_id": "task_xxx",
  "status": "pending",
  "message": "Task is still in queue or processing"
}
```

**タスク完了:**
```json
{
  "success": true,
  "task_id": "task_xxx",
  "status": "completed",
  "result": {
    // 更新タスクの結果データ
  }
}
```

**タスクが見つからない、または期限切れ:**
```json
{
  "success": false,
  "task_id": "task_xxx",
  "status": "not_found",
  "message": "Task not found or has expired"
}
```

#### 9. ユーザーレコード取得

```http
GET /api/v1/users/<user_id>/records?type=<record_type>&level=<level>&rating=<rating>&version=<version>&difficulty=<difficulty>
```

**パラメータ:**
- `type`: レコードタイプ (best50/best35/best15/allb50/allb35/apb50/fdxb50/rct50/idlb50、オプション、デフォルトはbest50)
- `level`: 譜面定数でフィルター (単一値または "min,max" 範囲、オプション)
- `rating`: 単曲Ratingでフィルター (単一値または "min,max" 範囲、オプション)
- `version`: ゲームバージョンでフィルター (複数のバージョンをカンマ区切り、例: "buddies,prism"、オプション)
- `difficulty`: 譜面難易度でフィルター (bas/adv/exp/mas/rem、複数の難易度をカンマ区切り、オプション)
- `command`: **非推奨、後方互換性のために維持**、フィルターコマンド（オプション）、以下のパラメータをサポート：
  - `-lv <定数>` または `-lv <最小> <最大>` - 譜面定数でフィルター
  - `-ra <rating>` または `-ra <最小> <最大>` - 単曲Ratingでフィルター
  - `-scr <達成率>` または `-scr <最小> <最大>` - 達成率でフィルター
  - `-dx <スコア>` または `-dx <最小> <最大>` - でらっくすスコアでフィルター
  - `-ver <バージョン1> [バージョン2] ...` - ゲームバージョンでフィルター（複数のバージョンをスペース区切りでサポート）
  - `-diff <難易度1> [難易度2] ...` - 譜面難易度でフィルター（bas/adv/exp/mas/rem、複数の難易度をスペース区切りでサポート）
  - `-times <倍率>` - 表示件数を倍率でスケーリング（最大 2.5、5 の倍数に切り上げ。例：b50 で `-times 2` を使用すると 35+15 ではなく 70+30 を表示）

**例:**
```bash
# best50を取得
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/records?type=best50"

# 特定のバージョンでフィルター（新パラメータ）
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/records?type=best50&version=buddies"

# MASTER難易度でフィルター（新パラメータ）
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/records?type=best50&difficulty=mas"

# 定数14.0以上でフィルター（新パラメータ）
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/records?type=best50&level=14.0"

# 定数範囲14.0-15.0でフィルター（新パラメータ）
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/records?type=best50&level=14.0,15.0"

# 組み合わせフィルター：MASTER難易度かつ定数14.0-15.0（新パラメータ）
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/records?type=best50&difficulty=mas&level=14.0,15.0"

# 旧 command パラメータを使用（後方互換性）
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/records?type=best50&command=-diff%20mas%20-lv%2014.0%2015.0"
```

**レスポンス:**
```json
{
  "success": true,
  "old_songs": [...],
  "new_songs": [...]
}
```

#### 10. 楽曲検索

```http
GET /api/v1/songs/search?q=<query>&user_id=<user_id>&ver=<version>&max_results=<limit>
```

**パラメータ:**
- `q`: 検索キーワード（オプション、デフォルトは空文字列；明示的な空文字列には `__empty__` を使用）
- `user_id`: 指定ユーザーのスコアデータベース内で楽曲を照合します（デフォルトは空で、照合しません）
- `ver`: バージョン (jp/intl、オプション、デフォルトはjp、user_id を指定すると、この項目は省略できます)
- `max_results`: 最大結果数（オプション、デフォルトは6）

**例:**
```bash
# 日本語楽曲を検索
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuk1.com/api/v1/songs/search?q=%E3%83%92%E3%83%90%E3%83%8A&ver=jp"

# 空文字列の曲名を検索
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuk1.com/api/v1/songs/search?q=__empty__&ver=jp"

# ユーザーのスコアデータベース内で照合
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuk1.com/api/v1/songs/search?q=%E3%83%92%E3%83%90%E3%83%8A&user_id=U123456"
```

**レスポンス:**
```json
{
  "success": true,
  "count": 2,
  "songs": [
    {
      "title": "ヒバナ",
      "artist": "Artist Name",
      ...
    },
    ...
  ]
}
```

```json
{
  "success": true,
  "count": 2,
  "records": [
    [
      {
        "name": "ヒバナ",
        "score": "100.8828%",
        ...
      },
      ...
    ],
    ...
  ]
}
```

#### 11. バージョン一覧取得

```http
GET /api/v1/versions
```

**例:**
```bash
curl -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuk1.com/api/v1/versions
```

**レスポンス:**
```json
{
  "success": true,
  "versions": [
    {"id": 0, "name": "maimai"},
    {"id": 1, "name": "maimai PLUS"},
    ...
  ]
}
```

## 権限リクエスト API

権限リクエストシステムにより、開発者トークンは自分が作成していないユーザーデータへのアクセスをリクエストできます。ユーザーはこれらのリクエストを承認または拒否できます。

### 権限モデル

JiETNG は2層の権限モデルを使用しています：

1. **所有者権限（Owner）**: ユーザーを作成したトークン（`registered_via_token` フィールドで識別）
   - すべての操作を実行可能：読み取り、更新、ユーザー削除
   - 権限リクエストの管理：表示、承認、拒否、取り消し

2. **付与されたアクセス権限（Granted）**: ユーザーに承認されたトークン（トークンの `allowed_users` リストに含まれる）
   - ユーザーデータの読み取り
   - ユーザーデータ更新のトリガー
   - ユーザー削除や権限管理は**不可**

### デコレーターの説明

API は2種類のデコレーターを使用してアクセス権限を制御します：

- **`@require_user_permission`**: 所有者と承認された両方のトークンを許可（読み取り操作用）
- **`@require_owner_permission`**: 所有者のみを許可（機密操作用）

#### 12. アクセス権限のリクエスト

```http
POST /api/v1/users/<user_id>/permissions
```

**説明:** 指定されたユーザーのデータにアクセスするための権限リクエストを送信します。

**必要な権限:** 有効な開発者トークン

**リクエストボディ (JSON):**
- `requester_name`: オプション、リクエスト者名（通知に表示、デフォルトはトークンのノート）

**例:**
```bash
curl -X POST -H "Authorization: Bearer abc123..." \
     -H "Content-Type: application/json" \
     -d '{"requester_name":"MyApp"}' \
     https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/permissions
```

**レスポンス:**
```json
{
  "success": true,
  "request_id": "20250203120000_jt_abc123",
  "user_id": "U123456",
  "message": "Permission request sent to user U123456"
}
```

**エラーレスポンス:**
```json
{
  "error": "Permission already granted",
  "message": "Token already has access to user U123456"
}
```

```json
{
  "error": "Request already sent",
  "message": "Permission request already sent, waiting for approval"
}
```

#### 13. 権限リクエスト一覧の表示

```http
GET /api/v1/users/<user_id>/permissions/requests
```

**説明:** ユーザーの保留中の権限リクエスト一覧を取得します。

**必要な権限:** 所有者トークンのみ（`@require_owner_permission`）

**例:**
```bash
curl -H "Authorization: Bearer abc123..." \
     https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/permissions/requests
```

**レスポンス:**
```json
{
  "success": true,
  "user_id": "U123456",
  "count": 2,
  "requests": [
    {
      "request_id": "20250203120000_jt_abc123",
      "token_id": "jt_abc123",
      "token_note": "MyApp",
      "requester_name": "MyApp",
      "timestamp": "2025-02-03 12:00:00"
    },
    {
      "request_id": "20250203130000_jt_def456",
      "token_id": "jt_def456",
      "token_note": "AnotherApp",
      "requester_name": "AnotherApp",
      "timestamp": "2025-02-03 13:00:00"
    }
  ]
}
```

#### 14. 権限リクエストの承認または拒否

```http
PATCH /api/v1/users/<user_id>/permissions
```

**説明:** 指定された権限リクエストを承認または拒否します。

**必要な権限:** 所有者トークンのみ（`@require_owner_permission`）

**リクエストボディ (JSON):**
- `request_id`: **必須**、処理する権限リクエストID
- `action`: **必須**、アクション種別 ("accept" または "reject")

**承認リクエストの例:**
```bash
curl -X PATCH -H "Authorization: Bearer abc123..." \
     -H "Content-Type: application/json" \
     -d '{"request_id":"20250203120000_jt_abc123","action":"accept"}' \
     https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/permissions
```

**承認レスポンス:**
```json
{
  "success": true,
  "user_id": "U123456",
  "token_id": "jt_abc123",
  "token_note": "MyApp",
  "message": "Permission granted to token jt_abc123"
}
```

**拒否リクエストの例:**
```bash
curl -X PATCH -H "Authorization: Bearer abc123..." \
     -H "Content-Type: application/json" \
     -d '{"request_id":"20250203120000_jt_abc123","action":"reject"}' \
     https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/permissions
```

**拒否レスポンス:**
```json
{
  "success": true,
  "user_id": "U123456",
  "token_id": "jt_abc123",
  "token_note": "MyApp",
  "message": "Permission request from token jt_abc123 rejected"
}
```

**エラーレスポンス:**
```json
{
  "error": "Request not found",
  "message": "Permission request not found or already processed"
}
```

#### 15. 付与された権限の取り消し

```http
DELETE /api/v1/users/<user_id>/permissions/<token_id>
```

**説明:** 指定されたトークンに以前付与されたアクセス権限を取り消します。

**必要な権限:** 所有者トークンのみ（`@require_owner_permission`）

**例:**
```bash
curl -X DELETE -H "Authorization: Bearer abc123..." \
     https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/permissions/jt_abc123
```

**レスポンス:**
```json
{
  "success": true,
  "user_id": "U123456",
  "token_id": "jt_abc123",
  "message": "Permission revoked for token jt_abc123"
}
```

#### 16. アクセス権限の自己取り消し

```
DELETE /api/v1/users/<user_id>/permissions/self
```

**説明:** トークンが自分自身のアクセス権限を主体的に放棄します。所有者（作成者）権限の取り消しには使用できません。

**必要な権限:** 承認済みアクセス権限を持つ任意のトークン（`@require_dev_token`、非所有者）

**例:**
```bash
curl -X DELETE -H "Authorization: Bearer abc123..." \
     https://jietng-endpoint.matsuk1.com/api/v1/users/U123456/permissions/self
```

**レスポンス:**
```json
{
  "success": true,
  "user_id": "U123456",
  "message": "Permission revoked"
}
```

**エラーレスポンス:**
```json
{
  "error": "Forbidden",
  "message": "Owner permission cannot be self-revoked"
}
```

### API v2 エンドポイント（画像生成）

以下のエンドポイントはすべて `/api/v2/` パス配下にあり、`image/png` 形式の画像データを返します。

#### 17. 楽曲情報画像の生成

```
GET /api/v2/songs/<song_id>/image?ver=<version>
```

**説明:** 指定した楽曲の詳細情報画像を生成します。カバー、難易度、譜面定数などの情報を含みます。

**必要な権限:** 任意の有効なトークン

**クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|---------|------|------|------|
| `ver` | string | ❌ | サーバーバージョン、`jp` または `intl`、デフォルト `jp` |

**例:**
```bash
curl -H "Authorization: Bearer abc123..." \
     "https://jietng-endpoint.matsuk1.com/api/v2/songs/834/image?ver=jp" \
     --output song_info.png
```

**レスポンス:** `Content-Type: image/png`、PNG 画像バイナリデータを直接返します。

#### 18. ユーザー楽曲記録画像の生成

```
GET /api/v2/users/<user_id>/songs/<song_id>/image
```

**説明:** ユーザーの指定楽曲における各難易度のプレイ記録画像を生成します。

**必要な権限:** 所有者または承認済みトークン

**パスパラメータ:**

| パラメータ | 型 | 説明 |
|---------|------|------|
| `user_id` | string | ユーザー ID |
| `song_id` | string | 楽曲 ID |

**例:**
```bash
curl -H "Authorization: Bearer abc123..." \
     "https://jietng-endpoint.matsuk1.com/api/v2/users/U123456/songs/834/image" \
     --output song_record.png
```

**レスポンス:** `Content-Type: image/png`、PNG 画像バイナリデータを直接返します。

#### 19. 成績画像の生成

```
GET /api/v2/users/<user_id>/image?command=<command>
```

**説明:** ユーザーの成績画像を生成し、PNG 画像データを直接返します。

**必要な権限:** 所有者または承認済みトークン

**クエリパラメータ:**

| パラメータ | 型 | 説明 |
|---------|------|------|
| `command` | string | 成績タイプ（下表参照）、デフォルト `b50` |

**command の選択肢:**

| 値 | 説明 |
|----|------|
| `b50` / `best50` | Best 50 |
| `b40` / `best40` | Best 40 |
| `b35` / `best35` | Best 35 |
| `b15` / `best15` | Best 15 |
| `rct50` / `r50` | 最近 50 曲 |
| `apb50` / `ap50` | AP Best 50 |
| `fdxb50` / `fdx50` | FDX Best 50 |
| `ab50` / `allb50` | All Best 50 |
| `idealb50` / `idlb50` | Ideal Best 50 |

**例:**
```bash
curl -H "Authorization: Bearer abc123..." \
     "https://jietng-endpoint.matsuk1.com/api/v2/users/U123456/image?command=b50" \
     --output b50.png
```

**レスポンス:** `Content-Type: image/png`、PNG 画像バイナリデータを直接返します。

#### 20. 段位牌画像の生成

```
GET /api/v2/users/<user_id>/plate?title=<title>
```

**説明:** ユーザーの段位牌画像を生成し、PNG 画像データを直接返します。

**必要な権限:** 所有者または承認済みトークン

**クエリパラメータ:**

| パラメータ | 型 | 説明 |
|---------|------|------|
| `title` | string | 段位称号（例: `覇極`、`覇将`、`覇舞舞`） |

**例:**
```bash
curl -H "Authorization: Bearer abc123..." \
     "https://jietng-endpoint.matsuk1.com/api/v2/users/U123456/plate?title=覇極" \
     --output plate.png
```

**レスポンス:** `Content-Type: image/png`、PNG 画像バイナリデータを直接返します。

#### 21. 達成状況画像の生成

```
GET /api/v2/users/<user_id>/achievement?level=<level>&rank=<rank>
```

**説明:** 指定した難度レベルの達成状況画像を生成し、PNG 画像データを直接返します。

**必要な権限:** 所有者または承認済みトークン

**クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|---------|------|------|------|
| `level` | string | ✅ | 難度レベル（例: `15`、`14+`、`13`） |
| `rank` | string | ❌ | 達成ランクフィルター（例: `sss`、`ap+`、`fc`、未指定で全件表示） |

**rank の選択肢:** `s`、`s+`、`ss`、`ss+`、`sss`、`sss+`、`fc`、`fc+`、`ap`、`ap+`、`fdx`、`fdx+`

**例:**
```bash
curl -H "Authorization: Bearer abc123..." \
     "https://jietng-endpoint.matsuk1.com/api/v2/users/U123456/achievement?level=15&rank=sss" \
     --output achievement.png
```

**レスポンス:** `Content-Type: image/png`、PNG 画像バイナリデータを直接返します。

### LINE ユーザーの権限管理

LINE ユーザーは権限リクエストの FlexMessage 通知を受け取り、LINE 内で直接承認または拒否できます：

1. 新しい権限リクエストが到着すると、ユーザーは通知メッセージを受け取ります
2. メッセージにはリクエスト者情報と2つのボタンが含まれます：「承認」と「拒否」
3. ボタンをクリックすると、システムが自動的にリクエストを処理します

## エラー処理

### 401 Unauthorized

**ケース:**
- Authorization ヘッダーが提供されていない
- トークン形式が無効
- トークンが無効または無効化されている

**レスポンス例:**
```json
{
  "error": "Invalid token",
  "message": "Token is invalid or has been revoked"
}
```

### 400 Bad Request

**ケース:**
- 必須パラメータが不足（例: registerエンドポイントでnicknameが欠けている）
- パラメータ値が無効（例: languageが許可リストにない）

**レスポンス例:**
```json
{
  "error": "Missing parameter",
  "message": "Parameter 'nickname' is required"
}
```

### 403 Forbidden

**ケース:**
- 現在のトークンではこの user_id にアクセスできません
- トークンがユーザーの所有者ではありません（所有者権限が必要な操作の場合）
- トークンが所有者でも承認されてもいません

**レスポンス例:**
```json
{
  "error": "Forbidden",
  "message": "Only the owner token (creator) can perform this operation"
}
```

```json
{
  "error": "Permission denied",
  "message": "Token does not have permission to access user U123456"
}
```

### 404 Not Found

**ケース:**
- リクエストされたリソースが存在しない（例: ユーザーが見つからない）

**レスポンス例:**
```json
{
  "error": "User not found",
  "message": "User U123456 does not exist"
}
```

### 500 Internal Server Error

**ケース:**
- サーバー内部エラー

**レスポンス例:**
```json
{
  "error": "Internal server error",
  "message": "Error description"
}
```

## API エンドポイント一覧

### 基本エンドポイント

| エンドポイント | メソッド | 説明 | 必要な権限 |
|----------------|--------------|-------------------|----------|
| `/users` | GET | すべてのユーザーを取得 | 任意のトークン |
| `/users` | POST | ユーザーを登録し連携URLを生成 | 任意のトークン |
| `/users/<user_id>` | GET | ユーザー情報を取得 | 所有者または承認済み |
| `/users/<user_id>` | DELETE | ユーザーを削除 | **所有者のみ** |
| `/users/<user_id>/rebind-url` | POST | 再連携URLを生成 | 所有者または承認済み |
| `/users/<user_id>/settings-url` | POST | 設定URLを生成 | 所有者または承認済み |
| `/users/<user_id>/tasks` | POST | 同期タスクを作成 (202 Accepted) | 所有者または承認済み |
| `/tasks/<task_id>` | GET | タスク状態確認 | 任意のトークン |
| `/users/<user_id>/records` | GET | ユーザーレコードを取得 | 所有者または承認済み |
| `/songs` | GET | 楽曲を検索 | 任意のトークン |
| `/versions` | GET | バージョン一覧を取得 | 任意のトークン |

### 権限管理エンドポイント

| エンドポイント | メソッド | 説明 | 必要な権限 |
|----------------|--------------|-------------------|----------|
| `/users/<user_id>/permissions` | POST | アクセス権限をリクエスト | 任意のトークン |
| `/users/<user_id>/permissions/requests` | GET | 権限リクエスト一覧を表示 | **所有者のみ** |
| `/users/<user_id>/permissions/requests/<request_id>` | PATCH | 権限リクエストを承認または拒否 | **所有者のみ** |
| `/users/<user_id>/permissions/<token_id>` | DELETE | 付与された権限を取り消し | **所有者のみ** |
| `/users/<user_id>/permissions/self` | DELETE | アクセス権限の自己取り消し | 承認済みトークン（非所有者）|

### 画像生成エンドポイント（v2）

| エンドポイント | メソッド | 説明 | 必要な権限 |
|----------------|--------------|-------------------|----------|
| `/api/v2/songs/<song_id>/image` | GET | 楽曲情報画像を生成 | 任意のトークン |
| `/api/v2/users/<user_id>/songs/<song_id>/image` | GET | ユーザー楽曲記録画像を生成 | 所有者または承認済み |
| `/api/v2/users/<user_id>/image` | GET | 成績画像を生成 | 所有者または承認済み |
| `/api/v2/users/<user_id>/plate` | GET | 段位牌画像を生成 | 所有者または承認済み |
| `/api/v2/users/<user_id>/achievement` | GET | 達成状況画像を生成 | 所有者または承認済み |

## セキュリティ推奨事項

1. **トークンを安全に保管**
   - トークンは作成時に一度しか表示されません
   - トークンを安全な場所に保存してください
   - 公開リポジトリにトークンをコミットしないでください

2. **定期的にトークンをローテーション**
   - 定期的に古いトークンを無効化し、新しいトークンを作成してください
   - 異なるアプリケーションには異なるトークンを使用してください

3. **HTTPS を使用**
   - 常にHTTPS経由でトークンを送信してください
   - 安全でないネットワークでAPIを使用しないでください

4. **使用状況を監視**
   - 定期的にトークンの最終使用時刻を確認してください
   - 使用されていないトークンを無効化してください

5. **最小権限の原則**
   - 必要なアプリケーションにのみトークンを作成してください
   - 不要になったアクセス権限は速やかに無効化してください

## 技術実装

### データストレージ

トークンデータの保存場所は `config.json` の `file_path.dev_tokens` で設定されます（デフォルト: `./data/dev_tokens.json`）:

```json
{
  "jt_abc123def456": {
    "token": "actual_token_string",
    "note": "MyApp API Integration",
    "created_at": "2025-01-24 12:00:00",
    "created_by": "U123456",
    "last_used": "2025-01-24 15:30:00",
    "revoked": false
  }
}
```

### デコレーター使用法

新しいAPIエンドポイントには `@require_dev_token` デコレーターを使用します:

```python
@app.route("/api/v1/my_endpoint", methods=["GET"])
@csrf.exempt
@require_dev_token
def my_api_endpoint():
    # トークン情報は request.token_info に自動的に追加されます
    token_info = request.token_info
    logger.info(f"API access via token {token_info['token_id']}")

    return jsonify({"success": True})
```

## サンプルコード

### Python

```python
import requests

TOKEN = "your_token_here"
BASE_URL = "https://jietng-endpoint.matsuk1.com/api/v1"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# ユーザー一覧を取得
response = requests.get(f"{BASE_URL}/users", headers=headers)
users = response.json()

print(f"Total users: {users['count']}")
for user in users['users']:
    print(f"  - {user['nickname']} ({user['user_id']})")
```

### JavaScript

```javascript
const TOKEN = 'your_token_here';
const BASE_URL = 'https://jietng-endpoint.matsuk1.com/api/v1';

async function getUsers() {
  const response = await fetch(`${BASE_URL}/users`, {
    headers: {
      'Authorization': `Bearer ${TOKEN}`
    }
  });

  const data = await response.json();
  console.log(`Total users: ${data.count}`);

  data.users.forEach(user => {
    console.log(`  - ${user.nickname} (${user.user_id})`);
  });
}

getUsers();
```

### cURL

```bash
#!/bin/bash

TOKEN="your_token_here"
BASE_URL="https://jietng-endpoint.matsuk1.com/api/v1"

# ユーザー一覧を取得
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/users"

# 特定のユーザー情報を取得
USER_ID="U123456"
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/users/$USER_ID"

# 楽曲を検索
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/songs/search?q=ヒバナ&ver=jp"
```

## よくある質問

### Q: トークンは期限切れになりますか？
**A:** 現在、トークンは自動的に期限切れになりませんが、管理者が手動で無効化できます。

### Q: トークンを紛失した場合はどうすればよいですか？
**A:** トークンは作成時に一度しか表示されません。紛失した場合は、古いトークンを無効化し、新しいトークンを作成する必要があります。

### Q: 1つのアプリケーションで複数のトークンを持つことはできますか？
**A:** はい。管理と無効化を容易にするため、異なる目的には異なるトークンを作成することをお勧めします。

### Q: トークンの権限範囲はどうなっていますか？
**A:** JiETNG は2層権限モデルを実装しています：
- **所有者権限**：ユーザーを作成したトークンは完全なアクセス権限を持ちます（読み取り、更新、削除、権限リクエスト管理）
- **承認済みアクセス権限**：ユーザーに承認されたトークンはユーザーデータの読み取りと更新のみ可能で、削除や権限管理はできません

## バージョン履歴

- **v2.0**（2026-03-12）：API v2 画像生成エンドポイントを追加
  - 画像生成エンドポイントを `/api/v2/` パスに移行
  - 楽曲情報画像生成を追加（`GET /api/v2/songs/<song_id>/image`）
  - ユーザー楽曲記録画像生成を追加（`GET /api/v2/users/<user_id>/songs/<song_id>/image`）
  - 成績画像・段位牌画像・達成状況画像を v2 に移行
- **v1.3**（2026-02-27）：自己取り消し権限と画像生成エンドポイントを追加
  - `DELETE /permissions/self` でトークンが自主的に承認済みアクセスを放棄できる機能を追加
  - 3つの画像生成エンドポイントを追加（成績画像・段位牌画像・達成状況画像）（v2 に移行済み）
- **v1.2**（2026-02-03）：RESTful API 標準に準拠するように変更
  - すべてのフィールドを RESTful API の設計規約により適合するよう修正
- **v1.1** (2025-12-04): 権限リクエストシステムを追加
  - 5つの権限管理APIエンドポイントを追加
  - 2層権限モデル（所有者 vs 承認済み）を実装
  - `@require_owner_permission` デコレーターを追加
  - LINE ユーザーに FlexMessage 権限リクエスト通知機能を追加
- **v1.0** (2025-01-24): 基本的なトークン管理とAPI認証をサポートする初回リリース

## 関連ファイル

- `config.json` - 設定ファイル（トークンファイルパスを含む）
- `modules/config_loader.py` - 設定ローダー
- `modules/devtoken_manager.py` - トークン管理のコアロジック
- `modules/perm_request_handler.py` - 権限リクエスト処理ロジック
- `modules/perm_request_generator.py` - 権限リクエスト FlexMessage ジェネレーター
- `modules/message_manager.py` - 三ヶ国語メッセージ定義
- `main.py` - APIエンドポイントとコマンド処理
- `data/dev_tokens.json` - トークンデータストレージ（デフォルト位置）

## サポート

質問や提案がある場合は、システム管理者にお問い合わせください（メール: matsuk1@proton.me）。
