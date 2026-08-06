# API Quick Reference - RESTful Endpoints

## 权限管理 Permission Management

### 请求权限 Request Permission
```http
POST /api/v2/users/{user_id}/permissions
Authorization: Bearer {token}
Content-Type: application/json

{
  "requester_name": "My App"  // 可选
}

Response: 201 Created
{
  "success": true,
  "request_id": "req_abc123",
  "user_id": "U123",
  "message": "Permission request sent"
}
```

### 获取权限请求 Get Permission Requests
```http
GET /api/v2/users/{user_id}/permissions/requests
Authorization: Bearer {owner_token}

Response: 200 OK
{
  "success": true,
  "user_id": "U123",
  "count": 2,
  "requests": [
    {
      "request_id": "req_abc123",
      "token_id": "token_xyz",
      "requester_name": "My App",
      "timestamp": "2026-02-03T10:00:00"
    }
  ]
}
```

### 管理权限请求 Manage Permission Request
```http
PATCH /api/v2/users/{user_id}/permissions/requests/{request_id}
Authorization: Bearer {owner_token}
Content-Type: application/json

// 接受
{
  "action": "accept"
}

// 拒绝
{
  "action": "reject"
}

Response: 200 OK
{
  "success": true,
  "user_id": "U123",
  "token_id": "token_xyz",
  "token_note": "My App",
  "message": "Permission accepted"
}
```

### 撤销权限 Revoke Permission
```http
DELETE /api/v2/users/{user_id}/permissions/{token_id}
Authorization: Bearer {owner_token}

Response: 200 OK
{
  "success": true,
  "user_id": "U123",
  "token_id": "token_xyz",
  "message": "Permission revoked for token token_xyz"
}
```

## 数据同步 Data Sync

### 流式同步 Streaming Sync
```http
POST /api/v2/users/{user_id}/sync/stream
Authorization: Bearer {token}

Content-Type: application/x-ndjson

{"event":"accepted","success":true,"user_id":"U123","version":"jp","started_at":"2026-06-20 12:34:56","message":"Sync started."}
{"event":"completed","success":true,"user_id":"U123","version":"jp","username":"Player","rating":"15392","last_update":"2026-06-20 12:35:04","elapsed_time":8.42,"func_status":{"User Info":true,"Best Records":true,"Recent Records":true},"best_count":1200,"recent_count":50,"message":"Sync completed successfully."}
```

## 歌曲搜索 Song Search

### 搜索歌曲 Search Songs
```http
GET /api/v2/songs/search?q=残響&ver=jp&max_results=6
Authorization: Bearer {token}

Response: 200 OK
{
  "success": true,
  "count": 1,
  "query": "残響",
  "ver": "jp",
  "songs": [
    {
      "id": "12345",
      "title": "残響散歌",
      "artist": "Aimer",
      ...
    }
  ]
}
```

`max_results` must be between 1 and 50.
If `ver` is omitted and `user_id` is provided, the API uses that user's saved server version. If both are omitted, it defaults to `jp`.

## 成绩图识别 Score Recognition

```http
POST /api/v2/score-recognition
Authorization: Bearer {token}
Content-Type: multipart/form-data

image=@result.jpg
ver=jp
```

仅在识别到完整成绩并匹配到歌曲、谱面时返回 `200`。响应包含：

- `song.id/title/type`
- `chart.difficulty/level/internal_level`
- `score.achievement/judgements/break_detail`
- `validation` 中的标题匹配、行列修正、MISS 修正和 Calc 校验元数据

图片支持 JPEG、PNG、WebP；默认最大 20 MiB、4000 万像素。无法确认完整成绩返回 `422`。

## 错误响应 Error Responses

### 400 Bad Request
```json
{
  "error": "Missing parameter",
  "message": "Parameter 'request_id' is required"
}
```

### 404 Not Found
```json
{
  "error": "User not found",
  "message": "User U123 does not exist"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Error details..."
}
```

## 常用参数 Common Parameters

### 权限请求
- `requester_name`: 请求者名称（可选）
- `request_id`: 请求ID（必需，用于accept/reject）
- `action`: 操作类型（"accept" 或 "reject"）

### 图像生成
- `format`: 返回格式，`png`（默认）或 `base64`（返回 JSON 含 base64 编码图片）
- 图片文字由服务器版本决定：`jp` 固定使用日文，`intl` 固定使用英文，不接受其他图片语言覆盖

### 歌曲搜索
- `q`: 搜索关键词（支持 "__empty__" 表示空字符串）
- `ver`: 服务器版本（jp/intl，默认jp）
- `max_results`: 最大结果数（服务端默认10，允许1-50；SDK默认传6）
- `user_id`: 用户ID（可选，返回用户记录）

## HTTP 状态码速查

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | OK | GET 成功，PATCH 成功，DELETE 成功 |
| 201 | Created | POST 创建权限请求成功 |
| 202 | Accepted | POST 异步任务（数据同步）已接受 |
| 400 | Bad Request | 参数缺失或无效 |
| 404 | Not Found | 资源不存在（用户/任务/权限） |
| 413 | Payload Too Large | OCR 图片超过上传上限 |
| 415 | Unsupported Media Type | OCR 图片格式不受支持 |
| 422 | Unprocessable Content | 无法识别并校验完整成绩 |
| 429 | Too Many Requests | 请求频率超过限制 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | 队列已满 |

## 认证 Authentication

所有 API 端点都需要 Bearer Token 认证：

```http
Authorization: Bearer your_token_here
```

某些端点需要特定权限：
- **Owner Permission**: 用户的所有者 token（管理权限请求、撤销权限）
- **User Permission**: 对用户有访问权限的 token（查询记录、触发同步）
