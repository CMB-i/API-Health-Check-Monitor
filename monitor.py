import asyncio
import sys
import yaml
from pathlib import Path
from rich.console import Console

from core.engine import check_all_endpoints
from data.logger import init_db, safe_log_results, get_recent_logs, get_avg_latency
from alerts.notifier import process_alerts
from ui.dashboard import dashboard_loop

console = Console()
CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def map_for_alerts(results):
    # Engine uses status_code/latency_ms; notifier supports both styles.
    return [
        {
            "name": r.get("name"),
            "status": r.get("status_code"),
            "latency": r.get("latency_ms"),
            "content_valid": r.get("content_valid", True),
            "validation_error": r.get("validation_error"),
            "error": r.get("error"),
        }
        for r in results
    ]


async def run_cycle(endpoints, timeout, latency_threshold_ms, email_config=None):
    results = list(await check_all_endpoints(endpoints, timeout=timeout))
    safe_log_results(results)
    process_alerts(
        map_for_alerts(results),
        latency_threshold_ms=latency_threshold_ms,
        email_config=email_config,
    )
    return results


def print_report():
    logs = get_recent_logs(limit=20)
    avg = get_avg_latency()

    console.rule("[bold cyan]Historical Report (last 20 checks)[/bold cyan]")
    for name, status_code, latency_ms, timestamp in logs:
        code_text = status_code if status_code is not None else "ERR"
        lat_text = f"{latency_ms:.0f}ms" if latency_ms is not None else "—"
        console.print(f"  {timestamp}  {name:<28}  HTTP {code_text}  {lat_text}")

    if avg is not None:
        console.print(f"\n[bold]Average latency:[/bold] [cyan]{avg:.1f}ms[/cyan]")
    else:
        console.print("\n[dim]No data yet — run the monitor first.[/dim]")


async def run_loop(config):
    settings = config.get("settings", {})
    alert_settings = config.get("alerts", {})
    email_config = alert_settings.get("email", {})

    endpoints = config["endpoints"]
    interval = max(10, settings.get("interval_seconds", 30))
    timeout = settings.get("timeout_seconds", 5)
    latency_threshold = settings.get("latency_threshold_ms", 500)

    async def results_provider():
        return await run_cycle(
            endpoints,
            timeout,
            latency_threshold_ms=latency_threshold,
            email_config=email_config,
        )

    await dashboard_loop(results_provider, interval=interval)


def main():
    config = load_config()
    init_db()

    if "--report" in sys.argv:
        print_report()
    else:
        try:
            asyncio.run(run_loop(config))
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Monitor stopped.[/bold yellow]")


if __name__ == "__main__":
    main()