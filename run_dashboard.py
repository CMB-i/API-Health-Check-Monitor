import asyncio
from monitor import load_config, run_cycle
from ui.dashboard import dashboard_loop
from data.logger import init_db


async def main():
    config = load_config()
    init_db()

    settings = config.get("settings", {})
    endpoints = config["endpoints"]
    interval = max(10, settings.get("interval_seconds", 30))
    timeout = settings.get("timeout_seconds", 5)
    latency_threshold = settings.get("latency_threshold_ms", 500)

    async def get_results():
        return await run_cycle(endpoints, timeout, latency_threshold_ms=latency_threshold)

    await dashboard_loop(get_results, interval=interval)



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitor stopped.")