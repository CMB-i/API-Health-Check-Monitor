import asyncio
import time
import httpx


def _get_json_value(data, path):
    """
    Resolve a dotted path (e.g., 'a.b.c') in a nested dict.
    Returns: (value, found_bool)
    """
    current = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None, False
        current = current[part]
    return current, True


def validate_response_content(response, rules):
    """
    Validate response JSON using optional rules:
      - json_path_exists: [path1, path2, ...]
      - json_path_equals: {path: expected_value, ...}
    """
    if not rules:
        return True, None

    try:
        payload = response.json()
    except Exception:
        return False, "Response is not valid JSON"

    # Existence checks
    for path in rules.get("json_path_exists", []):
        _, found = _get_json_value(payload, path)
        if not found:
            return False, f"Missing key path: {path}"

    # Equality checks
    for path, expected in rules.get("json_path_equals", {}).items():
        value, found = _get_json_value(payload, path)
        if not found:
            return False, f"Missing key path: {path}"
        if value != expected:
            return False, f"Value mismatch at {path}: expected={expected!r}, got={value!r}"

    return True, None


async def check_endpoint(client, endpoint):
    """
    Checks a single API endpoint and returns a structured health-check result.
    """
    name = endpoint.get("name", "Unnamed API")
    url = endpoint.get("url")
    validation_rules = endpoint.get("validation", {})

    start_time = time.perf_counter()

    try:
        response = await client.get(url)

        end_time = time.perf_counter()
        latency_ms = round((end_time - start_time) * 1000, 2)

        status_code = response.status_code
        content_valid, validation_error = validate_response_content(response, validation_rules)

        # Service is considered up only when status is 200 and content validates
        is_up = (status_code == 200) and content_valid

        return {
            "name": name,
            "url": url,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "is_up": is_up,
            "error": None,
            "content_valid": content_valid,
            "validation_error": validation_error,
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
            "error": "Request timed out",
            "content_valid": False,
            "validation_error": None,
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
            "error": str(e),
            "content_valid": False,
            "validation_error": None,
        }

    except Exception as e:
        end_time = time.perf_counter()
        latency_ms = round((end_time - start_time) * 1000, 2)

        return {
            "name": name,
            "url": url,
            "status_code": None,
            "latency_ms": latency_ms,
            "is_up": False,
            "error": f"Unexpected error: {str(e)}",
            "content_valid": False,
            "validation_error": None,
        }


async def check_all_endpoints(endpoints, timeout=5):
    """
    Checks all endpoints concurrently and returns a list of result dictionaries.
    """
    timeout_config = httpx.Timeout(timeout)

    async with httpx.AsyncClient(timeout=timeout_config) as client:
        tasks = []

        for endpoint in endpoints:
            task = check_endpoint(client, endpoint)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

    return results