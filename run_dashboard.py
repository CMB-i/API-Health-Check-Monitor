import asyncio
from core.engine import check_all_endpoints
from ui.dashboard import dashboard_loop

endpoints = [
    {"name": "HTTPBin", "url": "https://httpbin.org/get"},
    {"name": "GitHub API", "url": "https://api.github.com"},
]

timeout = 5
interval = 5


async def get_results():
    return await check_all_endpoints(endpoints, timeout=timeout)


async def main():
    await dashboard_loop(get_results, interval=interval)


if __name__ == "__main__":
    asyncio.run(main())
