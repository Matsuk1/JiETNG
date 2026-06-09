"""最小用例：异步客户端 / Minimal async usage."""
import asyncio
import os

from jietng import AsyncjietngClient, NotFoundError


async def main() -> None:
    token = os.environ["JIETNG_TOKEN"]
    user_id = os.environ.get("JIETNG_USER_ID", "U0000000000000000000000000000000")

    async with AsyncjietngClient(token=token) as client:
        print("Users:", (await client.users.list()).get("count"))

        try:
            png = await client.images.records(user_id, command="b50")
            with open("b50.png", "wb") as f:
                f.write(png)
            print(f"saved b50.png ({len(png)} bytes)")
        except NotFoundError as e:
            print(f"no records: {e}")

        path = await client.exports.save(user_id, fmt="json")
        print(f"exported: {path}")


if __name__ == "__main__":
    asyncio.run(main())
