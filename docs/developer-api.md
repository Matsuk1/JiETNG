# 开发者 API

JiETNG 提供两套 API：

- **开发者 API**：由开发者 Token 调用，用于创建用户、生成绑定/设置链接、请求用户授权、生成图片等。
- **用户导入 API**：由用户 Import Token 调用，用于上传网页书签或第三方工具整理后的成绩 JSON。

默认服务域名：

```text
https://jietng-endpoint.matsuk1.com
```

## 认证

开发者 API 使用 Bearer Token：

```http
Authorization: Bearer <developer_token>
```

Import API 使用用户 Import Token：

```http
Authorization: Bearer <import_token>
```

开发者 Token 和 Import Token 不是同一种凭证。开发者 Token 用于应用集成；Import Token 属于单个用户，只能上传该用户自己的成绩。

## 开发者 Token

开发者 Token 通过 LINE Bot 管理：

```text
devtoken create <备注>
devtoken list
devtoken revoke <token_id>
devtoken info <token_id>
```

Token 明文只在创建时返回一次，请安全保存。

## 用户与权限模型

开发者 API 访问用户数据需要满足其一：

- 该用户由当前 Token 创建，Token 是 owner。
- 用户已接受当前 Token 的权限请求。

权限请求流程：

```http
POST /api/v2/users/<user_id>/permissions
PATCH /api/v2/users/<user_id>/permissions/requests/<request_id>
DELETE /api/v2/users/<user_id>/permissions/<token_id>
DELETE /api/v2/users/<user_id>/permissions/self
```

用户也可以在 LINE 中处理请求：

```text
accept-perm-request <request_id>
reject-perm-request <request_id>
```

## 用户相关端点

### 创建用户

```http
POST /api/v2/users
```

创建外部集成用户，并返回可用于绑定的用户 ID 或绑定链接。

### 绑定 SEGA 账号

```http
POST /api/v2/users/<user_id>/bind
PUT /api/v2/users/<user_id>/bind
```

`POST` 用于首次绑定完整 SEGA 账号，`PUT` 用于换绑/更新密码、版本、Aime。当前 LINE 侧 `rebind` 不允许更换 SEGA ID；API 集成也应避免把换绑设计成任意换号。

### 生成网页链接

```http
GET /api/v2/users/<user_id>/bind-url
GET /api/v2/users/<user_id>/rebind-url
GET /api/v2/users/<user_id>/settings-url
```

用于让用户在 JiETNG 网页中完成绑定、换绑或设置。`settings` 页面也包含 Import Token 管理。

### 触发同步

```http
POST /api/v2/users/<user_id>/sync/stream
```

`/sync/stream` 返回 `application/x-ndjson`，第一行是 `accepted`，结束时返回 `completed` 或 `failed`。仅适用于已绑定完整 SEGA 账号的用户。导入模式用户应调用导入 API 上传成绩。

## 图片与查询端点

### 生成成绩图

```http
GET /api/v2/users/<user_id>/image?command=b50
GET /api/v2/users/<user_id>/songs/<song_id>/image
GET /api/v2/users/<user_id>/plate?title=真神
GET /api/v2/users/<user_id>/achievement?level=14%2B&rank=sss
GET /api/v2/songs/<song_id>/image
GET /api/v2/users/<user_id>/export?fmt=json
GET /api/v2/dxdata?ver=jp
```

`/songs/search` 的版本选择优先级：显式 `ver` > `user_id` 对应用户的服务器版本 > 默认 `jp`。

`command` 可使用用户可输入的 B 系列命令：

| command | 说明 |
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
| `unknown` | 版本未知歌曲列表 |

可在 `command` 后组合筛选参数，语义与 LINE 命令一致，例如 `b50 -lv 14.7`。

### 网页书签图片端点

```http
POST /api/web/session-image
Content-Type: application/json
```

接收网页书签整理出的 JSON，返回 `image/png`。该端点不需要开发者 Token，但只允许官方 maimai 移动站相关来源跨域调用。

请求体核心字段：

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

该端点只生成图片，不保存成绩。保存成绩请使用 Import API。

## Import Token 与成绩导入

用户在 LINE 私聊发送 `settings` 后，可在设置页生成 Import Token。Token 明文只显示一次，服务器只保存哈希。

### 上传加工后成绩

```http
POST /api/v2/import/records
Authorization: Bearer <import_token>
Content-Type: application/json
```

请求体示例：

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

字段说明：

- `version`：`jp` 或 `intl`。
- `profile`：用户资料。缺失字段会尽量保留服务器已有值。
- `best`：Best 记录。
- `recent`：Recent 记录。
- `rating_block_path` 不需要上传，服务端会根据 `rating` 计算。

替换规则：

- 请求体包含 `"best": []` 会清空 Best。
- 请求体包含 `"recent": []` 会清空 Recent。
- 省略某个分区则保留服务器旧数据。

成功响应：

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

`/api/web/session-image` 与 `/api/v2/import/records` 为网页书签设计，允许官方 maimai 移动站来源：

- `https://maimaidx.jp`
- `https://maimaidx-eng.com`

## 错误码

| 状态码 | 常见原因 |
|--------|----------|
| `400` | 参数错误、payload 不合法、用户未绑定 |
| `401` | Token 无效、SEGA 凭据错误 |
| `403` | 没有访问该用户的权限 |
| `404` | 用户、Token、请求或任务不存在 |
| `409` | 用户已绑定或状态冲突 |
| `503` | 官方维护或同步队列满 |

## 与 LINE 命令的差异

- LINE 命令会按聊天上下文、@ 提及和 self-only 规则分发。
- API 需要显式提供 `user_id`，并通过 Token 权限控制访问。
- Import API 不会爬取 maimai NET，只接收加工后的成绩 JSON。
- 图片接口使用当前服务器保存的数据；如果数据过期，需要先同步或导入。

## 安全建议

- 不要把开发者 Token 或 Import Token 写进前端公开代码。
- Import Token 只适合用户自己的浏览器书签或可信工具。
- 第三方应用应走开发者 Token + 用户授权流程。
- 用户取消授权时，应用应调用 `DELETE /api/v2/users/<user_id>/permissions/self` 放弃权限。
