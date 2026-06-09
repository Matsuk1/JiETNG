# jietng — Python SDK

[`pip install jietng`](https://pypi.org/project/jietng/) — Python 客户端，封装 [JiETNG](https://jietng.matsuk1.com) 舞萌DX 查分器的 HTTP API。

支持同步 / 异步两套客户端、覆盖全部 v2 端点（用户 / 权限 / 同步 / 搜歌 / 成绩图 / 导出 …）、类型注解齐全。

## 安装

```bash
pip install jietng
```

需要 Python ≥ 3.8、httpx ≥ 0.25。

## 获取 Token

JiETNG API 通过 Bearer Token 鉴权。申请方式见 <https://jietng.matsuk1.com/developer-api> —— 发邮件到 `matsuk1@proton.me` 索取。

## 快速开始

### 同步

```python
from jietng import JiETNGClient

with JiETNGClient(token="your_token") as client:
    users = client.users.list()
    print(users["count"], "registered users")

    # 取 B50 成绩图（返回 PNG bytes）
    png = client.images.records("U1234567890", command="b50")
    with open("b50.png", "wb") as f:
        f.write(png)

    # 触发后台同步
    task = client.users.trigger_sync("U1234567890")
    print("queued:", task["task_id"])

    # 导出成绩为 JSON / XML，文件名由服务端推荐（含玩家名 + 时间戳）
    path = client.exports.save("U1234567890", fmt="json")
    print("exported to", path)
```

### 异步

```python
import asyncio
from jietng import AsyncJiETNGClient

async def main():
    async with AsyncJiETNGClient(token="your_token") as client:
        print(await client.songs.search("PANDORA", ver="jp", max_results=3))
        png = await client.images.plate("U1234567890", title="真神")
        with open("plate.png", "wb") as f:
            f.write(png)

asyncio.run(main())
```

## 资源总览

| 命名空间 | 主要方法 |
|---|---|
| `client.users` | `list / get / create / delete / trigger_sync / bind / update_bind / get_rebind_url / get_settings_url` |
| `client.permissions` | `request / list_requests / accept / reject / revoke / revoke_self` |
| `client.songs` | `search / info` |
| `client.tasks` | `get` |
| `client.versions` | `list` |
| `client.dxdata` | `get` |
| `client.images` | `user_song / records / plate / achievement` |
| `client.exports` | `download / save` |

所有方法的形参 / 返回结构与 [JiETNG API 文档](https://jietng.matsuk1.com/developer-api) 一一对应。

## 错误处理

所有 HTTP 非 2xx 状态都会抛 `APIError` 子类。可以按需 catch 具体类型：

```python
from jietng import JiETNGClient, NotFoundError, PermissionDeniedError, RateLimitedError, QueueFullError

try:
    png = client.images.records("U_unknown", command="b50")
except NotFoundError:
    print("user has no records yet")
except PermissionDeniedError:
    print("your token doesn't have access to this user")
except RateLimitedError:
    print("slow down")
except QueueFullError:
    print("server task queue is full, retry later")
```

完整异常层级：

```
JiETNGError                  # 基类
└─ APIError                  # 任意 HTTP 非 2xx
   ├─ ValidationError        # 400
   ├─ AuthenticationError    # 401
   ├─ PermissionDeniedError  # 403
   ├─ NotFoundError          # 404
   ├─ RateLimitedError       # 429
   ├─ ServerError            # 500
   └─ QueueFullError         # 503
```

每个异常实例都带 `status_code` / `error` / `message` / `payload` 字段，方便排查。

## 自定义

```python
client = JiETNGClient(
    token="your_token",
    base_url="https://your-self-hosted.example.com/api/v2",   # 自托管时
    timeout=60.0,
    extra_headers={"X-App-Name": "MyBot"},
)
```

## 许可

MIT。代码：<https://github.com/Matsuk1/JiETNG/tree/main/client>
