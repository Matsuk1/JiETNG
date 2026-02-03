# API Quick Reference - RESTful Endpoints

## 权限管理 Permission Management

### 请求权限 Request Permission
```http
POST /api/v1/users/{user_id}/permissions
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
GET /api/v1/users/{user_id}/permissions/requests
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
PATCH /api/v1/users/{user_id}/permissions
Authorization: Bearer {owner_token}
Content-Type: application/json

// 接受
{
  "request_id": "req_abc123",
  "action": "accept"
}

// 拒绝
{
  "request_id": "req_abc123",
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
DELETE /api/v1/users/{user_id}/permissions/{token_id}
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

### 触发同步 Trigger Sync
```http
POST /api/v1/users/{user_id}/sync
Authorization: Bearer {token}

Response: 202 Accepted
{
  "success": true,
  "message": "Sync task queued successfully",
  "user_id": "U123",
  "task_id": "api_sync_abc123",
  "queue_size": 3
}
```

## 成绩记录 Records

### 获取成绩 Get Records
```http
GET /api/v1/users/{user_id}/records?type=best50&level=14,15&rating=100-200
Authorization: Bearer {token}

Response: 200 OK
{
  "success": true,
  "user_id": "U123",
  "type": "best50",
  "count": 50,
  "old_songs": [...],
  "new_songs": [...]
}
```

## 歌曲搜索 Song Search

### 搜索歌曲 Search Songs
```http
GET /api/v1/songs/search?q=残響&ver=jp&max_results=6
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

// 带用户记录
GET /api/v1/songs/search?q=残響&user_id=U123
{
  "success": true,
  "count": 1,
  "query": "残響",
  "ver": "jp",
  "records": [
    [
      {
        "title": "残響散歌",
        "achievements": 100.5000,
        "fc": "ap",
        ...
      }
    ]
  ]
}
```

## 任务状态 Task Status

### 查询任务 Get Task
```http
GET /api/v1/tasks/{task_id}
Authorization: Bearer {token}

Response: 200 OK
{
  "success": true,
  "task_id": "api_sync_abc123",
  "status": "running",  // running, queued, completed, cancelled
  "start_time": "2026-02-03T10:00:00",
  "task_type": "maimai_update"
}
```

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

### 成绩查询
- `type`: best50, best40, best100, best35, best15, allb50, allb100, allb200, allb35, apb50, rct50, idlb50, UNKNOWN
- `level`: 定数范围，如 "14,15" 或 "14.0-15.0"
- `rating`: rating范围，如 "100-200"
- `version`: 版本过滤
- `difficulty`: 难度过滤

### 歌曲搜索
- `q`: 搜索关键词（支持 "__empty__" 表示空字符串）
- `ver`: 服务器版本（jp/intl，默认jp）
- `max_results`: 最大结果数（默认6）
- `user_id`: 用户ID（可选，返回用户记录）

## HTTP 状态码速查

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | OK | GET 成功，PATCH 成功，DELETE 成功 |
| 201 | Created | POST 创建权限请求成功 |
| 202 | Accepted | POST 异步任务（数据同步）已接受 |
| 400 | Bad Request | 参数缺失或无效 |
| 404 | Not Found | 资源不存在（用户/任务/权限） |
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
