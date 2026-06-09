"""最小用例：同步客户端 / Minimal sync usage."""
import os

from jietng import jietngClient, NotFoundError

TOKEN = os.environ["JIETNG_TOKEN"]
USER_ID = os.environ.get("JIETNG_USER_ID", "U0000000000000000000000000000000")


with jietngClient(token=TOKEN) as client:
    # 列出已注册用户
    print("Users:", client.users.list().get("count"))

    # 取自己（或被授权的用户）的 B50 成绩图
    try:
        png = client.images.records(USER_ID, command="b50")
        with open("b50.png", "wb") as f:
            f.write(png)
        print(f"saved b50.png ({len(png)} bytes)")
    except NotFoundError as e:
        print(f"no records: {e}")

    # 导出成绩 JSON
    path = client.exports.save(USER_ID, fmt="json")
    print(f"exported: {path}")
