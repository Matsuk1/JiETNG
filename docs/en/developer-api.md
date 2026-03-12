# Developer API Documentation

## Overview

The Developer Token system allows administrators to create and manage API access tokens for third-party applications or scripts to access JiETNG's API endpoints.


## Quick Start

### Get API Token

If you want to use the JiETNG API, follow these steps to get an access token:

1. **Send Email**
   - To: `matsuk1@proton.me`
   - Subject: `JiETNG API Token Request`
   - Content:
     - Your name or organization
     - Purpose of use
     - Expected usage frequency

2. **Wait for Review**
   - The administrator will review your application and create a dedicated token

3. **Receive Token**
   - You will receive the Token ID and complete token string via email
   - **Keep your token secure!**

### API Base Information

- **Base URL (v1)**: `https://jietng-endpoint.matsuki.work/api/v1/`
- **Base URL (v2)**: `https://jietng-endpoint.matsuki.work/api/v2/`
- **Authentication**: Bearer Token
- **Response Format**: JSON (image generation endpoints return `image/png`)

### Usage Example

```bash
# Use your token to access the API
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     "https://jietng-endpoint.matsuki.work/api/v1/users"
```


## Command Usage

### Admin Commands

Only administrators can use the following commands in LINE Bot:

#### 1. Create Token

```
devtoken create <note>
```

**Example:**
```
devtoken create MyApp API Integration
```

**Returns:**
- Token ID (for management)
- Complete token string (keep it secure)
- Note

#### 2. List All Tokens

```
devtoken list
```

**Shows:**
- Token ID
- Note
- Status (Active/Revoked)
- Created at
- Last used

#### 3. Revoke Token

```
devtoken revoke <token_id>
```

**Example:**
```
devtoken revoke jt_abc123def456
```

#### 4. View Token Details

```
devtoken info <token_id>
```

**Shows:**
- Token ID
- Complete token string
- Note
- Status
- Creator
- Created at
- Last used


## API Usage

### Base URL

```
https://jietng-endpoint.matsuki.work/api/v1/
```

### Authentication

All API endpoints require Bearer Token authentication:

```bash
curl -H "Authorization: Bearer <your_token>" https://jietng-endpoint.matsuki.work/api/v1/...
```

### Available Endpoints

v1 endpoints should be prefixed with `https://jietng-endpoint.matsuki.work/api/v1/`.

v2 endpoints should be prefixed with `https://jietng-endpoint.matsuki.work/api/v2/`.

#### 1. Get User List

```http
GET /api/v1/users
```

**Example:**
```bash
curl -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuki.work/api/v1/users
```

**Response:**
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

#### 2. Register User

```http
POST /api/v1/users
```

**Request Body (JSON):**
- `user_id`: **Required**, user ID
- `nickname`: **Required**, user nickname (automatically fetched from LINE API for LINE users, otherwise use this parameter)
- `language`: Language setting (ja/en/zh, optional, defaults to en)

**Nickname Priority:**
1. Automatically fetch from LINE API (if LINE user)
2. Get from user data's nickname field
3. Use the provided nickname parameter

**Example:**
```bash
curl -X POST -H "Authorization: Bearer abc123..." -H "Content-Type: application/json" -d '{"user_id":"U123456","nickname":"TestUser","language":"en"}' https://jietng-endpoint.matsuki.work/api/v1/users
```

**Response:**
```json
{
  "success": true,
  "user_id": "U123456",
  "nickname": "TestUser",
  "bind_url": "https://jietng-endpoint.matsuki.work/linebot/sega_bind?token=xxx&nickname=TestUser&language=en",
  "token": "xxx",
  "expires_in": 120,
  "message": "Bind URL generated successfully. Token expires in 2 minutes."
}
```

**Registration Tracking:**

New users registered via API will automatically track:
- `registered_via_token`: The token ID used for registration
- `registered_at`: Registration timestamp (format: YYYY-MM-DD HH:MM:SS)

#### 3. Get User Info

```http
GET /api/v1/users/<user_id>
```

**Example:**
```bash
curl -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuki.work/api/v1/users/U123456
```

**Response:**
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

#### 4. Delete User

```http
DELETE /api/v1/users/<user_id>
```

**Example:**
```bash
curl -X DELETE -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuki.work/api/v1/users/U123456
```

**Response:**
```json
{
  "success": true,
  "user_id": "U123456",
  "message": "User U123456 has been deleted successfully"
}
```

#### 5. Get Rebind URL

```http
POST /api/v1/users/<user_id>/rebind-url
```

**Description:** Generates a rebind page URL for modifying SEGA ID password, version, and other account information.

**Permission Required:** Owner or granted Token

**Example:**
```bash
curl -X POST -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuki.work/api/v1/users/U123456/rebind-url
```

**Response (201 Created):**
```json
{
  "success": true,
  "user_id": "U123456",
  "rebind_url": "https://jietng-endpoint.matsuki.work/linebot/sega_bind?token=xxx&mode=rebind",
  "expires_in": 120,
  "message": "Rebind URL generated successfully."
}
```

#### 6. Get Settings URL

```http
POST /api/v1/users/<user_id>/settings-url
```

**Description:** Generates a settings page URL for modifying language, timezone, background images, and other personal preferences.

**Permission Required:** Owner or granted Token

**Example:**
```bash
curl -X POST -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuki.work/api/v1/users/U123456/settings-url
```

**Response (201 Created):**
```json
{
  "success": true,
  "user_id": "U123456",
  "settings_url": "https://jietng-endpoint.matsuki.work/linebot/settings?token=xxx",
  "expires_in": 1800,
  "message": "Settings URL generated successfully."
}
```

#### 7. Sync User Data

```http
POST /api/v1/users/<user_id>/sync
```

**Description:** Asynchronously sync user data, returns 202 Accepted status code.

**Example:**
```bash
curl -X POST -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuki.work/api/v1/users/U123456/sync
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "user_id": "U123456",
  "task_id": "task_xxx",
  "queue_size": 5,
  "message": "User update task queued successfully"
}
```

#### 8. Query Task Status

```http
GET /api/v1/tasks/<task_id>
```

**Description:**
Query the status of an update task created via `/users/<user_id>/sync`.

**Example:**
```bash
curl -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuki.work/api/v1/tasks/task_xxx
```

**Response:**

**Task in progress:**
```json
{
  "success": true,
  "task_id": "task_xxx",
  "status": "pending",
  "message": "Task is still in queue or processing"
}
```

**Task completed:**
```json
{
  "success": true,
  "task_id": "task_xxx",
  "status": "completed",
  "result": {
    // Result data from the update task
  }
}
```

**Task not found or expired:**
```json
{
  "success": false,
  "task_id": "task_xxx",
  "status": "not_found",
  "message": "Task not found or has expired"
}
```

#### 9. Get User Records

```http
GET /api/v1/users/<user_id>/records?type=<record_type>&level=<level>&rating=<rating>&version=<version>&difficulty=<difficulty>
```

**Parameters:**
- `type`: Record type (best50/best35/best15/allb50/allb35/apb50/fdxb50/rct50/idlb50, optional, defaults to best50)
- `level`: Filter by chart constant (single value or "min,max" range, optional)
- `rating`: Filter by single song rating (single value or "min,max" range, optional)
- `version`: Filter by game version (supports multiple versions, comma-separated, e.g., "buddies,prism", optional)
- `difficulty`: Filter by chart difficulty (bas/adv/exp/mas/rem, supports multiple difficulties, comma-separated, optional)
- `command`: **Deprecated, maintained for backward compatibility**, filter command (optional), supports the following parameters:
  - `-lv <constant>` or `-lv <min> <max>` - Filter by chart constant
  - `-ra <rating>` or `-ra <min> <max>` - Filter by single song rating
  - `-scr <achievement>` or `-scr <min> <max>` - Filter by achievement rate
  - `-dx <score>` or `-dx <min> <max>` - Filter by DX score
  - `-ver <version1> [version2] ...` - Filter by game version (supports multiple versions, space-separated)
  - `-diff <difficulty1> [difficulty2] ...` - Filter by chart difficulty (bas/adv/exp/mas/rem, supports multiple difficulties, space-separated)

**Example:**
```bash
# Get best50
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuki.work/api/v1/users/U123456/records?type=best50"

# Filter specific version (new parameter)
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuki.work/api/v1/users/U123456/records?type=best50&version=buddies"

# Filter MASTER difficulty (new parameter)
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuki.work/api/v1/users/U123456/records?type=best50&difficulty=mas"

# Filter constant 14.0 and above (new parameter)
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuki.work/api/v1/users/U123456/records?type=best50&level=14.0"

# Filter constant range 14.0-15.0 (new parameter)
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuki.work/api/v1/users/U123456/records?type=best50&level=14.0,15.0"

# Combined filter: MASTER difficulty and constant 14.0-15.0 (new parameter)
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuki.work/api/v1/users/U123456/records?type=best50&difficulty=mas&level=14.0,15.0"

# Using old command parameter (backward compatible)
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuki.work/api/v1/users/U123456/records?type=best50&command=-diff%20mas%20-lv%2014.0%2015.0"
```

**Response:**
```json
{
  "success": true,
  "old_songs": [...],
  "new_songs": [...]
}
```

#### 10. Search Songs

```http
GET /api/v1/songs/search?q=<query>&user_id=<user_id>&ver=<version>&max_results=<limit>
```

**Parameters:**
- `q`: Search query (optional, defaults to empty string; use `__empty__` for explicit empty string)
- `user_id`: Match songs in the specified user's score database (default is empty, no matching)
- `ver`: Version (jp/intl, optional, defaults to jp, after specifying the user_id, this field can be omitted.)
- `max_results`: Maximum number of results (optional, defaults to 6)

**Example:**
```bash
# Search Japanese songs
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuki.work/api/v1/songs/search?q=%E3%83%92%E3%83%90%E3%83%8A&ver=jp"

# Search empty string song names
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuki.work/api/v1/songs/search?q=__empty__&ver=jp"

# Match within the user's score database
curl -H "Authorization: Bearer abc123..." "https://jietng-endpoint.matsuki.work/api/v1/songs/search?q=%E3%83%92%E3%83%90%E3%83%8A&user_id=U123456"
```

**Response:**
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

#### 11. Get Version List

```http
GET /api/v1/versions
```

**Example:**
```bash
curl -H "Authorization: Bearer abc123..." https://jietng-endpoint.matsuki.work/api/v1/versions
```

**Response:**
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

## Permission Request API

The permission request system allows developer tokens to request access to user data not created by that token. Users can approve or reject these requests.

### Permission Model

JiETNG uses a two-tier permission model:

1. **Owner Permission**: The token that created the user (identified by `registered_via_token` field)
   - Can perform all operations: read, update, delete user
   - Can manage permission requests: view, approve, reject, revoke

2. **Granted Access Permission**: Tokens authorized by the user (in token's `allowed_users` list)
   - Can read user data
   - Can trigger user data updates
   - **Cannot** delete users or manage permissions

### Decorator Description

The API uses two decorators to control access permissions:

- **`@require_user_permission`**: Allows both owners and authorized tokens (for read operations)
- **`@require_owner_permission`**: Only allows owners (for sensitive operations)

#### 12. Request Access Permission

```http
POST /api/v1/users/<user_id>/permissions
```

**Description:** Send a permission request to access the specified user's data.

**Permission Required:** Any valid developer token

**Request Body (JSON):**
- `requester_name`: Optional, requester name (displayed in notifications, defaults to token note)

**Example:**
```bash
curl -X POST -H "Authorization: Bearer abc123..." \
     -H "Content-Type: application/json" \
     -d '{"requester_name":"MyApp"}' \
     https://jietng-endpoint.matsuki.work/api/v1/users/U123456/permissions
```

**Response:**
```json
{
  "success": true,
  "request_id": "20250203120000_jt_abc123",
  "user_id": "U123456",
  "message": "Permission request sent to user U123456"
}
```

**Error Responses:**
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

#### 13. View Permission Requests

```http
GET /api/v1/users/<user_id>/permissions/requests
```

**Description:** Get the list of pending permission requests for a user.

**Permission Required:** Owner token only (`@require_owner_permission`)

**Example:**
```bash
curl -H "Authorization: Bearer abc123..." \
     https://jietng-endpoint.matsuki.work/api/v1/users/U123456/permissions/requests
```

**Response:**
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
    }
  ]
}
```

#### 14. Approve or Reject Permission Request

```http
PATCH /api/v1/users/<user_id>/permissions
```

**Description:** Approve or reject the specified permission request.

**Permission Required:** Owner token only (`@require_owner_permission`)

**Request Body (JSON):**
- `request_id`: **Required**, the permission request ID to process
- `action`: **Required**, action type ("accept" or "reject")

**Approve request example:**
```bash
curl -X PATCH -H "Authorization: Bearer abc123..." \
     -H "Content-Type: application/json" \
     -d '{"request_id":"20250203120000_jt_abc123","action":"accept"}' \
     https://jietng-endpoint.matsuki.work/api/v1/users/U123456/permissions
```

**Approve response:**
```json
{
  "success": true,
  "user_id": "U123456",
  "token_id": "jt_abc123",
  "token_note": "MyApp",
  "message": "Permission granted to token jt_abc123"
}
```

**Reject request example:**
```bash
curl -X PATCH -H "Authorization: Bearer abc123..." \
     -H "Content-Type: application/json" \
     -d '{"request_id":"20250203120000_jt_abc123","action":"reject"}' \
     https://jietng-endpoint.matsuki.work/api/v1/users/U123456/permissions
```

**Reject response:**
```json
{
  "success": true,
  "user_id": "U123456",
  "token_id": "jt_abc123",
  "token_note": "MyApp",
  "message": "Permission request from token jt_abc123 rejected"
}
```

**Error Response:**
```json
{
  "error": "Request not found",
  "message": "Permission request not found or already processed"
}
```

#### 15. Revoke Granted Permission

```http
DELETE /api/v1/users/<user_id>/permissions/<token_id>
```

**Description:** Revoke access permission previously granted to a specific token.

**Permission Required:** Owner token only (`@require_owner_permission`)

**Example:**
```bash
curl -X DELETE -H "Authorization: Bearer abc123..." \
     https://jietng-endpoint.matsuki.work/api/v1/users/U123456/permissions/jt_abc123
```

**Response:**
```json
{
  "success": true,
  "user_id": "U123456",
  "token_id": "jt_abc123",
  "message": "Permission revoked for token jt_abc123"
}
```

#### 16. Self-Revoke Access Permission

```
DELETE /api/v1/users/<user_id>/permissions/self
```

**Description:** A token proactively surrenders its own granted access permission for a user. Cannot be used to revoke owner (creator) permission.

**Permission Required:** Any token holding a granted access permission (`@require_dev_token`, non-owner)

**Example:**
```bash
curl -X DELETE -H "Authorization: Bearer abc123..." \
     https://jietng-endpoint.matsuki.work/api/v1/users/U123456/permissions/self
```

**Response:**
```json
{
  "success": true,
  "user_id": "U123456",
  "message": "Permission revoked"
}
```

**Error Response:**
```json
{
  "error": "Forbidden",
  "message": "Owner permission cannot be self-revoked"
}
```

### API v2 Endpoints (Image Generation)

All endpoints below are under the `/api/v2/` path and return `image/png` data.

#### 17. Generate Song Info Image

```
GET /api/v2/songs/<song_id>/image?ver=<version>
```

**Description:** Generates a detailed song information image including cover, difficulty, and chart constants.

**Permission Required:** Any valid Token

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ver` | string | ❌ | Server version, `jp` or `intl`, default `jp` |

**Example:**
```bash
curl -H "Authorization: Bearer abc123..." \
     "https://jietng-endpoint.matsuki.work/api/v2/songs/834/image?ver=jp" \
     --output song_info.png
```

**Response:** `Content-Type: image/png`, returns PNG image binary data directly.

#### 18. Generate User Song Record Image

```
GET /api/v2/users/<user_id>/songs/<song_id>/image
```

**Description:** Generates an image of the user's play records for a specific song across all difficulties.

**Permission Required:** Owner or granted Token

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | User ID |
| `song_id` | string | Song ID |

**Example:**
```bash
curl -H "Authorization: Bearer abc123..." \
     "https://jietng-endpoint.matsuki.work/api/v2/users/U123456/songs/834/image" \
     --output song_record.png
```

**Response:** `Content-Type: image/png`, returns PNG image binary data directly.

#### 19. Generate Score Image

```
GET /api/v2/users/<user_id>/image?command=<command>
```

**Description:** Generates a score image for the user and returns PNG image data directly.

**Permission Required:** Owner or granted Token

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `command` | string | Score type (see table below), default `b50` |

**command options:**

| Value | Description |
|-------|-------------|
| `b50` / `best50` | Best 50 |
| `b40` / `best40` | Best 40 |
| `b35` / `best35` | Best 35 |
| `b15` / `best15` | Best 15 |
| `rct50` / `r50` | Recent 50 |
| `apb50` / `ap50` | AP Best 50 |
| `fdxb50` / `fdx50` | FDX Best 50 |
| `ab50` / `allb50` | All Best 50 |
| `idealb50` / `idlb50` | Ideal Best 50 |

**Example:**
```bash
curl -H "Authorization: Bearer abc123..." \
     "https://jietng-endpoint.matsuki.work/api/v2/users/U123456/image?command=b50" \
     --output b50.png
```

**Response:** `Content-Type: image/png`, returns PNG image binary data directly.

#### 20. Generate Plate Image

```
GET /api/v2/users/<user_id>/plate?title=<title>
```

**Description:** Generates a rating plate image for the user and returns PNG image data directly.

**Permission Required:** Owner or granted Token

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Rating title (e.g., `覇極`, `覇将`, `覇舞舞`) |

**Example:**
```bash
curl -H "Authorization: Bearer abc123..." \
     "https://jietng-endpoint.matsuki.work/api/v2/users/U123456/plate?title=覇極" \
     --output plate.png
```

**Response:** `Content-Type: image/png`, returns PNG image binary data directly.

#### 21. Generate Achievement Image

```
GET /api/v2/users/<user_id>/achievement?level=<level>&rank=<rank>
```

**Description:** Generates an achievement chart image for the specified difficulty level and returns PNG image data directly.

**Permission Required:** Owner or granted Token

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `level` | string | ✅ | Difficulty level (e.g., `15`, `14+`, `13`) |
| `rank` | string | ❌ | Achievement rank filter (e.g., `sss`, `ap+`, `fc`; omit to show all) |

**rank options:** `s`, `s+`, `ss`, `ss+`, `sss`, `sss+`, `fc`, `fc+`, `ap`, `ap+`, `fdx`, `fdx+`

**Example:**
```bash
curl -H "Authorization: Bearer abc123..." \
     "https://jietng-endpoint.matsuki.work/api/v2/users/U123456/achievement?level=15&rank=sss" \
     --output achievement.png
```

**Response:** `Content-Type: image/png`, returns PNG image binary data directly.

### Permission Request Workflow Example

```bash
# 1. Token B requests access to User1 created by Token A
curl -X POST -H "Authorization: Bearer TOKEN_B" \
     -H "Content-Type: application/json" \
     -d '{"requester_name":"MyApp"}' \
     https://jietng-endpoint.matsuki.work/api/v1/users/U123456/permissions

# 2. Token A (owner) views pending requests
curl -H "Authorization: Bearer TOKEN_A" \
     https://jietng-endpoint.matsuki.work/api/v1/users/U123456/permissions/requests

# 3. Token A approves the request
curl -X PATCH -H "Authorization: Bearer TOKEN_A" \
     -H "Content-Type: application/json" \
     -d '{"request_id":"20250203120000_jt_tokenb","action":"accept"}' \
     https://jietng-endpoint.matsuki.work/api/v1/users/U123456/permissions

# 4. Now Token B can access User1's data
curl -H "Authorization: Bearer TOKEN_B" \
     https://jietng-endpoint.matsuki.work/api/v1/users/U123456

# 5. (Optional) Token A revokes Token B's access
curl -X DELETE -H "Authorization: Bearer TOKEN_A" \
     https://jietng-endpoint.matsuki.work/api/v1/users/U123456/permissions/jt_tokenb
```

### LINE User Permission Management

LINE users receive FlexMessage notifications for permission requests and can approve or reject directly in LINE:

1. When a new permission request arrives, users receive a notification message
2. The message includes requester information and two buttons: "Accept" and "Reject"
3. Clicking a button automatically processes the request

## Error Handling

### 401 Unauthorized

**Cases:**
- Missing Authorization header
- Invalid token format
- Token is invalid or has been revoked

**Response Example:**
```json
{
  "error": "Invalid token",
  "message": "Token is invalid or has been revoked"
}
```

### 400 Bad Request

**Cases:**
- Missing required parameters (e.g., register endpoint missing nickname)
- Invalid parameter values (e.g., language not in allowed list)

**Response Example:**
```json
{
  "error": "Missing parameter",
  "message": "Parameter 'nickname' is required"
}
```

### 403 Forbidden

**Cases:**
- The current token cannot access this user_id
- Token is not the user's owner (for operations requiring owner permission)
- Token is neither the owner nor authorized

**Response Examples:**
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

**Cases:**
- Requested resource does not exist (e.g., user not found)

**Response Example:**
```json
{
  "error": "User not found",
  "message": "User U123456 does not exist"
}
```

### 500 Internal Server Error

**Cases:**
- Internal server error

**Response Example:**
```json
{
  "error": "Internal server error",
  "message": "Error description"
}
```


## API Endpoints Summary

### Basic Endpoints

| Endpoint | Method | Description | Permission Required |
|----------------|--------------|-------------------|----------|
| `/users` | GET | Get all users | Any Token |
| `/users` | POST | Register user and generate bind URL | Any Token |
| `/users/<user_id>` | GET | Get user info | Owner or Granted |
| `/users/<user_id>` | DELETE | Delete user | **Owner Only** |
| `/users/<user_id>/rebind-url` | POST | Get rebind URL | Owner or Granted |
| `/users/<user_id>/settings-url` | POST | Get settings URL | Owner or Granted |
| `/users/<user_id>/tasks` | POST | Create sync task (202 Accepted) | Owner or Granted |
| `/tasks/<task_id>` | GET | Query task status | Any Token |
| `/users/<user_id>/records` | GET | Get user records | Owner or Granted |
| `/songs` | GET | Search songs | Any Token |
| `/versions` | GET | Get version list | Any Token |

### Permission Management Endpoints

| Endpoint | Method | Description | Permission Required |
|----------------|--------------|-------------------|----------|
| `/users/<user_id>/permissions` | POST | Request access permission | Any Token |
| `/users/<user_id>/permissions/requests` | GET | View permission requests | **Owner Only** |
| `/users/<user_id>/permissions/requests/<request_id>` | PATCH | Approve or reject permission request | **Owner Only** |
| `/users/<user_id>/permissions/<token_id>` | DELETE | Revoke granted permission | **Owner Only** |
| `/users/<user_id>/permissions/self` | DELETE | Self-revoke access permission | Granted Token (non-owner) |

### Image Generation Endpoints (v2)

| Endpoint | Method | Description | Permission Required |
|----------------|--------------|-------------------|----------|
| `/api/v2/songs/<song_id>/image` | GET | Generate song info image | Any Token |
| `/api/v2/users/<user_id>/songs/<song_id>/image` | GET | Generate user song record image | Owner or Granted |
| `/api/v2/users/<user_id>/image` | GET | Generate score image | Owner or Granted |
| `/api/v2/users/<user_id>/plate` | GET | Generate plate image | Owner or Granted |
| `/api/v2/users/<user_id>/achievement` | GET | Generate achievement image | Owner or Granted |

## Security Recommendations

1. **Keep tokens secure**
   - Tokens are only shown once during creation
   - Store tokens in a secure location
   - Don't commit tokens to public repositories

2. **Rotate tokens regularly**
   - Periodically revoke old tokens and create new ones
   - Use different tokens for different applications

3. **Use HTTPS**
   - Always transmit tokens over HTTPS
   - Avoid using the API on unsecured networks

4. **Monitor usage**
   - Regularly check token last usage times
   - Revoke unused tokens

5. **Principle of least privilege**
   - Only create tokens for necessary applications
   - Revoke access permissions promptly when no longer needed


## Technical Implementation

### Data Storage

Token data storage location is configured by `file_path.dev_tokens` in `config.json` (default: `./data/dev_tokens.json`):

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

### Decorator Usage

Use the `@require_dev_token` decorator for new API endpoints:

```python
@app.route("/api/v1/my_endpoint", methods=["GET"])
@csrf.exempt
@require_dev_token
def my_api_endpoint():
    # Token info is automatically added to request.token_info
    token_info = request.token_info
    logger.info(f"API access via token {token_info['token_id']}")

    return jsonify({"success": True})
```

---

## Example Code

### Python

```python
import requests

TOKEN = "your_token_here"
BASE_URL = "https://jietng-endpoint.matsuki.work/api/v1"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# Get user list
response = requests.get(f"{BASE_URL}/users", headers=headers)
users = response.json()

print(f"Total users: {users['count']}")
for user in users['users']:
    print(f"  - {user['nickname']} ({user['user_id']})")
```

### JavaScript

```javascript
const TOKEN = 'your_token_here';
const BASE_URL = 'https://jietng-endpoint.matsuki.work/api/v1';

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
BASE_URL="https://jietng-endpoint.matsuki.work/api/v1"

# Get user list
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/users"

# Get specific user info
USER_ID="U123456"
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/users/$USER_ID"

# Search songs
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/songs/search?q=ヒバナ&ver=jp"
```


## FAQ

### Q: Can tokens expire?
**A:** Currently, tokens do not expire automatically, but can be manually revoked by administrators.

### Q: What if I lose my token?
**A:** Tokens are only shown once during creation. If lost, you need to revoke the old token and create a new one.

### Q: Can one application have multiple tokens?
**A:** Yes. It's recommended to create different tokens for different purposes for easier management and revocation.

### Q: What are the permission scopes of tokens?
**A:** JiETNG implements a two-tier permission model:
- **Owner permissions**: Tokens that created the user have full access (read, update, delete user, manage permission requests)
- **Granted permissions**: Tokens authorized by the user can only read and update user data, cannot delete users or manage permissions


## Version History

- **v2.0** (2026-03-12): Added API v2 image generation endpoints
  - Migrated image generation endpoints to `/api/v2/` path
  - Added song info image generation (`GET /api/v2/songs/<song_id>/image`)
  - Added user song record image generation (`GET /api/v2/users/<user_id>/songs/<song_id>/image`)
  - Score image, plate image, and achievement image migrated to v2
- **v1.3** (2026-02-27): Added self-revoke permission and image generation endpoints
  - Added `DELETE /permissions/self` allowing tokens to proactively surrender granted access
  - Added 3 image generation endpoints (score image, plate image, achievement image) (migrated to v2)
- **v1.2** (2026-02-03): Updated to comply with RESTful API standards
  - Revised all fields to better align with RESTful API conventions
- **v1.1** (2025-12-04): Added permission request system
  - Added 5 permission management API endpoints
  - Implemented two-tier permission model (owner vs granted)
  - Added `@require_owner_permission` decorator
  - LINE users receive FlexMessage notifications for permission requests
- **v1.0** (2025-01-24): Initial release with basic token management and API authentication


## Related Files

- `config.json` - Configuration file (contains token file path)
- `modules/config_loader.py` - Configuration loader
- `modules/devtoken_manager.py` - Token management core logic
- `modules/perm_request_handler.py` - Permission request handling logic
- `modules/perm_request_generator.py` - Permission request FlexMessage generator
- `modules/message_manager.py` - Trilingual message definitions
- `main.py` - API endpoints and command handling
- `data/dev_tokens.json` - Token data storage (default location)


## Support

For questions or suggestions, please contact the system administrator (email: matsuk1@proton.me).
