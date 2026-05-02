import asyncio
import time
import httpx


async def check_endpoint(client, endpoint):
    """
    Checks a single API endpoint and returns a dictionary result
    that can be directly used by the alerts module.
    """

    name = endpoint.get("name", "Unnamed API")
    url = endpoint.get("url")

    start_time = time.perf_counter()

    try:
        response = await client.get(url)

        end_time = time.perf_counter()
        latency_ms = round((end_time - start_time) * 1000, 2)

        status_code = response.status_code

        # Matching alerts module assumption:
        # only status code 200 is considered healthy
        is_up = status_code == 200

        return {
            "name": name,
            "url": url,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "is_up": is_up,
            "error": None
        }

    except httpx.TimeoutException:
        end_time = time.perf_counter()
        latency_ms = round((end_time - start_time) * 1000, 2)

        return {
            "name": name,
            "url": url,
            "status_code": None,
            "latency_ms": latency_ms,
            "is_up": False,
            "error": "Request timed out"
        }

    except httpx.RequestError as e:
        end_time = time.perf_counter()
        latency_ms = round((end_time - start_time) * 1000, 2)

        return {
            "name": name,
            "url": url,
            "status_code": None,
            "latency_ms": latency_ms,
            "is_up": False,
            "error": str(e)
        }


async def check_all_endpoints(endpoints, timeout=5):
    """
    Checks all endpoints concurrently and returns a list called results.
    """

    timeout_config = httpx.Timeout(timeout)

    async with httpx.AsyncClient(timeout=timeout_config) as client:
        tasks = []

        for endpoint in endpoints:
            task = check_endpoint(client, endpoint)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

    return results