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

### 成绩图 OCR

```http
POST /api/v2/score-recognition
Authorization: Bearer <developer_token>
Content-Type: multipart/form-data
```

请求字段：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `image` | 文件 | 是 | JPEG、PNG 或 WebP 成绩图。默认最大 20 MiB、4000 万像素 |
| `ver` | 文本 | 否 | `jp` 或 `intl`，默认 `jp`，用于匹配对应服务器的乐曲和谱面 |

该端点同步执行 OCR。只有图片中的曲名、达成率、完整判定表能够匹配并校验到一张谱面时才返回成功；只有主屏、缺少副屏或无法确认歌曲时返回 `422`。

```bash
curl -X POST https://jietng-endpoint.matsuk1.com/api/v2/score-recognition \
  -H "Authorization: Bearer <developer_token>" \
  -F "ver=jp" \
  -F "image=@result.jpg"
```

成功响应：

```json
{
  "success": true,
  "song": {
    "id": "50d3df",
    "title": "Little \"Sister\" Bitch",
    "type": "dx"
  },
  "chart": {
    "difficulty": "master",
    "level": "13+",
    "internal_level": 13.8
  },
  "score": {
    "achievement": 100.5658,
    "rank": "sss+",
    "combo": null,
    "status": {
      "rank": "sss+",
      "rank_icon_url": "https://maimaidx.jp/maimai-mobile/img/playlog/sssplus.png",
      "combo": null,
      "combo_icon_url": null
    },
    "judgements": {
      "tap": {"critical_perfect": 403, "perfect": 225, "great": 15, "good": 0, "miss": 1},
      "hold": {"critical_perfect": 18, "perfect": 7, "great": 0, "good": 0, "miss": 0},
      "slide": {"critical_perfect": 98, "perfect": 0, "great": 0, "good": 0, "miss": 0},
      "touch": {"critical_perfect": 66, "perfect": 0, "great": 0, "good": 0, "miss": 0},
      "break": {"critical_perfect": 20, "perfect": 13, "great": 0, "good": 0, "miss": 0}
    },
    "loss_detail": {
      "rows": {
        "tap": {
          "cells": {
            "great": {"count": 15, "loss_per_note": 0.0131, "total_loss": 0.1965},
            "good": {"count": 0, "loss_per_note": 0.0262, "total_loss": 0.0},
            "miss": {"count": 1, "loss_per_note": 0.0524, "total_loss": 0.0524}
          },
          "total_loss": 0.2489
        }
      },
      "total_loss": 0.2489
    },
    "break_detail": {
      "critical_perfect": 20,
      "perfect_high": 12,
      "perfect_low": 1,
      "great_high": 0,
      "great_middle": 0,
      "great_low": 0,
      "good": 0,
      "miss": 0,
      "candidate_count": 1,
      "loss_percentages": {
        "perfect_high": 0.0066,
        "perfect_low": 0.0131,
        "great_high": 0.1442,
        "great_middle": 0.2752,
        "great_low": 0.3408,
        "good": 0.4063,
        "miss": 0.4063
      },
      "total_loss": 0.0917
    }
  },
  "metadata": {
    "display_title": "Little \"Sister\" Bitch [DX]",
    "subtitle_template": "Judgement Details {difficulty} {type_icon}",
    "type_label": "DX",
    "type_icon_url": "https://maimaidx.jp/maimai-mobile/img/music_dx.png",
    "difficulty_label": "MASTER",
    "difficulty_style": {
      "background": "#9F51DC",
      "text": "#FFFFFF",
      "metric": "#8E44AD"
    }
  },
  "validation": {
    "title_match_type": "exact",
    "exact_title_match": true,
    "compared_rows": 5,
    "matching_rows": 5,
    "row_offset": 0,
    "column_offset": 0,
    "miss_corrections": {},
    "achievement_calc": {
      "observed": 100.5658,
      "minimum": 100.4749,
      "maximum": 100.5733,
      "consistent": true,
      "complete": true
    },
    "calc_corrections": [],
    "uncertain_cells": []
  }
}
```

字段说明：

- `song.id` 是 dxdata 乐曲 ID；`song.type` 为 `dx` 或 `std`。
- `chart.internal_level` 是谱面定数，未知时为 `null`。
- `judgements` 固定包含 `tap`、`hold`、`slide`、`touch`、`break`，每行固定包含五种判定。
- `score.status` 是 Flex 顶部状态栏使用的评级和 Combo 图标元数据；`combo` 可能为 `fc`、`fc+`、`ap`、`ap+` 或 `null`。
- `score.loss_detail` 是 Flex “详细判定”使用的普通 Note 失分数据，只列出 TAP、HOLD、SLIDE、TOUCH 中产生失分的行；百分比保留四位小数。
- `break_detail` 是 Flex “BREAK 详细判定”使用的当前最可能 BREAK 细分结果；`loss_percentages` 和 `total_loss` 是各细分格及整行损失的达成率百分比。`candidate_count` 是当前 BREAK 行内部的细分候选数，整行由 Calc 推定时可选字段 `row_candidate_count` 表示可行的整行候选数。无法得到离散匹配时为 `{}`。
- `metadata` 包含 Flex 标题、谱面类型图标、难度标签和难度配色，可直接用于客户端复刻当前 OCR FlexMsg。
- `row_offset`、`column_offset` 表示 OCR 表格经过的行列对齐修正，`0` 表示未移动。
- `miss_corrections` 记录根据谱面物量把 OCR MISS 从 `ocr` 修正为 `validated` 的行。
- `achievement_calc` 记录 Calc 可接受区间及 OCR 达成率是否一致。
- `calc_corrections` 记录 Calc 自动配平或推算的单元格；无修正时为空数组。
- `uncertain_cells` 记录无法唯一修正的疑似 OCR 单元格；完全确定时为空数组。

### OCR 结果图片

```http
POST /api/v2/score-recognition/image
Authorization: Bearer <developer_token>
Content-Type: multipart/form-data
```

请求字段、限制和错误响应与 JSON OCR 接口完全相同。成功时直接返回排版完成的 `image/png`：

```bash
curl -X POST https://jietng-endpoint.matsuk1.com/api/v2/score-recognition/image \
  -H "Authorization: Bearer <developer_token>" \
  -F "ver=jp" \
  -F "image=@result.jpg" \
  --output ocr-result.png
```

存在多个 Calc 有效解时，图片接口返回按 OCR 置信度排序后的第一项。响应头 `X-JiETNG-OCR-Candidate-Index` 和 `X-JiETNG-OCR-Candidate-Count` 分别表示当前候选序号和候选总数。

识别失败：

```json
{
  "error": "Recognition failed",
  "message": "The image could not be recognized as a complete score result."
}
```

服务端通过 `SCORE_RECOGNITION_API_MAX_IMAGE_BYTES` 调整上传上限，单位为字节。OCR 请求按开发者 Token 限流。

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
| `s50` / `sun50` / `寸50` / `寸止め` | 寸止め 50：100.4000%-100.4999%、99.9000%-99.9999% |
| `unknown` | 版本未知歌曲列表 |

可在 `command` 后组合筛选参数，语义与 LINE 命令一致，例如 `b50 -lv 14.7`。

### 网页书签图片端点

```http
POST /api/web/session-image
Content-Type: application/json
```

接收网页书签整理出的 JSON，返回 `image/png`。该端点不需要开发者 Token。

请求体核心字段：

```json
{
  "version": "jp",
  "cmd_type": "best50",
  "command": "-lv 14",
  "timezone": 9,
  "profile": {
    "name": "Player",
    "rating": "15000"
  },
  "records": {
    "best": [
      {
        "name": "Song Title",
        "difficulty": "master",
        "type": "dx",
        "score": "100.5000%",
        "dx_score": "1234",
        "score_icon": "sssp",
        "combo_icon": "ap",
        "sync_icon": "fdx"
      }
    ]
  }
}
```

`version` 只支持 `jp` 与 `intl`。`cmd_type` 支持 `best50`、`best40`、`best35`、`best15`、`allb35`、`allb50`、`apb50`、`fdxb50`、`idlb50`、`sun50`；`command` 用于传入 `-lv 14` 等筛选条件。`profile` 和至少一条有效的 `records.best` 记录为必需字段。

图片文字由服务器版本固定：`jp` 使用日文，`intl` 使用英文。用户语言设置或请求中的其他语言字段不会覆盖图片语言。

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

字段说明：

- `version`：`jp` 或 `intl`。
- `profile`：用户资料。缺失字段会尽量保留服务器已有值。
- `records.best`：Best 记录。
- `records.recent`：Recent 记录。
- `rating_block_path` 不需要上传，服务端会根据 `rating` 计算。

替换规则：

- 请求体包含 `"records": {"best": []}` 会清空 Best。
- 请求体包含 `"records": {"recent": []}` 会清空 Recent。
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

`/api/web/session-image` 与 `/api/v2/import/records` 的生产环境允许以下来源：

- `https://maimaidx.jp`
- `https://maimaidx-eng.com`
- `https://dxrating.net`

本地开发还允许 `http://localhost:5173` 与 `http://127.0.0.1:5173`。

## 错误码

| 状态码 | 常见原因 |
|--------|----------|
| `400` | 参数错误、payload 不合法、用户未绑定 |
| `401` | Token 无效、SEGA 凭据错误 |
| `403` | 没有访问该用户的权限 |
| `404` | 用户、Token、请求或任务不存在 |
| `409` | 用户已绑定或状态冲突 |
| `413` | OCR 图片超过上传上限 |
| `415` | OCR 图片格式不受支持 |
| `422` | 图片有效，但无法识别并校验为完整成绩 |
| `429` | 请求频率超过限制 |
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
